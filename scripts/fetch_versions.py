#!/usr/bin/env python3
"""Fetch versions from GitHub releases and tags, NuGet, Vulkan SDK, and web scraping."""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

TRACKER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracker.json")
GITHUB_API = "https://api.github.com"
NUGET_API = "https://api.nuget.org/v3-flatcontainer"

PRERELEASE_RE = re.compile(r"-(alpha|beta|preview|rc|dev|nightly|pre)", re.IGNORECASE)


def get_github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_version(tag):
    return tag.lstrip("v")


# ─── GitHub Releases ──────────────────────────────────────────────

def fetch_github_releases(repo):
    """Fetch releases from a GitHub repo. Returns (stable, prerelease)."""
    url = f"{GITHUB_API}/repos/{repo}/releases"
    params = {"per_page": 50}
    headers = get_github_headers()

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    releases = resp.json()

    stable = None
    prerelease = None

    for rel in releases:
        if rel.get("draft"):
            continue

        version = parse_version(rel["tag_name"])
        date_str = rel.get("published_at", "")
        date = None
        if date_str:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")

        entry = {"version": version, "date": date}

        if rel.get("prerelease"):
            if prerelease is None:
                prerelease = entry
        else:
            if stable is None:
                stable = entry

        if stable and prerelease:
            break

    return stable, prerelease


def fetch_github_tags(repo):
    """Fallback: fetch tags from a GitHub repo (for repos without releases).
    Uses tag name as version, no date available."""
    url = f"{GITHUB_API}/repos/{repo}/git/refs/tags"
    params = {"per_page": 50}
    headers = get_github_headers()

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    refs = resp.json()

    stable = None
    prerelease = None

    for ref in refs:
        tag = ref["ref"].replace("refs/tags/", "")
        version = parse_version(tag)
        is_pre = bool(PRERELEASE_RE.search(version))

        entry = {"version": version, "date": None}

        if is_pre:
            if prerelease is None:
                prerelease = entry
        else:
            if stable is None:
                stable = entry

        if stable and prerelease:
            break

    return stable, prerelease


# ─── NuGet ────────────────────────────────────────────────────────

def fetch_nuget_versions(package_id):
    """Fetch versions from NuGet. Returns (stable, prerelease)."""
    url = f"{NUGET_API}/{package_id.lower()}/index.json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    versions = data.get("versions", [])

    stable = None
    prerelease = None

    for ver in reversed(versions):
        is_pre = bool(PRERELEASE_RE.search(ver))
        entry = {"version": ver, "date": None}

        if is_pre:
            if prerelease is None:
                prerelease = entry
        else:
            if stable is None:
                stable = entry

        if stable and prerelease:
            break

    # Fetch dates
    if stable and stable["version"]:
        stable["date"] = _get_nuget_date(package_id, stable["version"])
    if prerelease and prerelease["version"]:
        prerelease["date"] = _get_nuget_date(package_id, prerelease["version"])

    return stable, prerelease


def _get_nuget_date(package_id, version):
    """Try to get the publish date from the NuGet registration API."""
    url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_id.lower()}/index.json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("items", []):
            for item in page.get("items", []):
                entry = item.get("catalogEntry", {})
                if entry.get("version") == version:
                    published = entry.get("published", "")
                    if published:
                        return datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


# ─── Scraping JSON ────────────────────────────────────────────────

def fetch_scraping_json(source):
    """Fetch version from a JSON endpoint (e.g. Vulkan SDK latest.json)."""
    url = source.get("url", "")
    json_path = source.get("json_path", "")

    if not url:
        return None

    try:
        resp = requests.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

        # Navigate nested path like "windows" or "windows.x64"
        value = data
        for key in json_path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        if value and isinstance(value, str):
            return {"version": value, "date": None}

    except Exception as e:
        print(f"    [!] scraping-json failed: {e}", file=sys.stderr)

    return None


# ─── Scraping HTML ────────────────────────────────────────────────

def fetch_scraping_html(source):
    """Fetch version from an HTML page using CSS selector + regex."""
    try:
        from scrapling.fetchers import Fetcher
    except ImportError:
        print("    [!] scrapling not installed, skipping", file=sys.stderr)
        return None

    url = source.get("url", "")
    selector = source.get("selector", "")
    regex = source.get("regex", "")

    if not url:
        return None

    try:
        page = Fetcher.get(url)
        if not page or not page.status or page.status != 200:
            return None

        version = None

        # Try CSS selector first
        if selector:
            elements = page.css(selector)
            if elements:
                text = elements[0].text.strip()
                if regex:
                    match = re.search(regex, text)
                    if match:
                        version = match.group(1)
                else:
                    version = text

        # Fallback: regex on full page text
        if not version and regex:
            all_text = page.get_all_text()
            match = re.search(regex, all_text)
            if match:
                version = match.group(1)

        if version:
            return {"version": version, "date": None}

    except Exception as e:
        print(f"    [!] scraping-html failed: {e}", file=sys.stderr)

    return None


# ─── Main fetcher ─────────────────────────────────────────────────

def fetch_entry(entry):
    """Fetch versions for an entry based on its sources. Returns (stable, prerelease, active_source_type)."""
    for source in entry.get("sources", []):
        src_type = source.get("type")

        try:
            if src_type == "github":
                stable, prerelease = fetch_github_releases(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github:{source['repo']}"
                # Fallback to tags
                stable, prerelease = fetch_github_tags(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github-tags:{source['repo']}"

            elif src_type == "github-tags":
                stable, prerelease = fetch_github_tags(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github-tags:{source['repo']}"

            elif src_type == "nuget":
                stable, prerelease = fetch_nuget_versions(source["package_id"])
                if stable or prerelease:
                    return stable, prerelease, f"nuget:{source['package_id']}"

            elif src_type == "scraping-json":
                result = fetch_scraping_json(source)
                if result:
                    return result, None, f"scraping-json:{source.get('url', '')}"

            elif src_type == "scraping-html":
                result = fetch_scraping_html(source)
                if result:
                    return result, None, f"scraping-html:{source.get('url', '')}"

            elif src_type == "scraping":
                result = fetch_scraping_html(source)
                if result:
                    return result, None, f"scraping:{source.get('url', '')}"

        except Exception as e:
            print(f"    [!] {src_type} failed: {e}", file=sys.stderr)
            continue

    return None, None, None


def main():
    tracker_path = os.path.abspath(TRACKER_PATH)
    with open(tracker_path, "r", encoding="utf-8") as f:
        tracker = json.load(f)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0
    skipped = 0
    errors = []

    for entry in tracker["entries"]:
        sources = entry.get("sources", [])
        if not sources or entry.get("manual"):
            skipped += 1
            if entry.get("manual"):
                print(f"  [{entry['id']}] (manual) ... skipped")
            continue

        source_desc = " / ".join(s.get("type") for s in sources)
        print(f"  [{entry['id']}] ({source_desc}) ... ", end="", flush=True)

        stable, prerelease, active = fetch_entry(entry)

        if stable or prerelease:
            entry["versions"]["stable"] = stable
            entry["versions"]["prerelease"] = prerelease
            entry["active_source"] = active
            entry["last_checked"] = today
            updated += 1

            s_ver = stable["version"] if stable else "-"
            p_ver = prerelease["version"] if prerelease else "-"
            print(f"stable={s_ver}  pre={p_ver}  via={active}")
        else:
            entry["last_checked"] = today
            skipped += 1
            print("no versions found (skipped)")

    tracker["_meta"]["last_updated"] = today

    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {updated} updated, {skipped} skipped/unchanged, {len(errors)} errors.")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
