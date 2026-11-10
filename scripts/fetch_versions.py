#!/usr/bin/env python3
"""Fetch versions from GitHub (releases, tags, commits), NuGet, JSON endpoints
and web pages, plus the file version of each DLL (see binaries.py)."""

import json
import os
import re
import sys
from datetime import datetime, timezone

import binaries
import net

TRACKER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracker.json")
NUGET_API = "https://api.nuget.org/v3-flatcontainer"

PRERELEASE_RE = re.compile(r"-(alpha|beta|preview|rc|dev|nightly|pre)", re.IGNORECASE)


def iso_day(timestamp):
    """"2026-10-16T12:00:00Z" -> "2026-10-16"; None stays None."""
    if not timestamp:
        return None
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d")


def parse_version(tag):
    return tag.lstrip("v")


def looks_like_version(version):
    """Reject tags that are not versions at all (e.g. a "utils" tooling release)."""
    return bool(version) and any(ch.isdigit() for ch in version)


def version_key(version):
    """Numeric parts of a version, for a rough ordering ("release-1.1.65" -> (1, 1, 65))."""
    return tuple(int(n) for n in re.findall(r"\d+", version))


def is_outdated_prerelease(stable, prerelease):
    """A prerelease is outdated when it was published before the latest stable
    and does not belong to a higher version line.

    Example: Steam Audio 2.0-beta.20 (2021) vs 4.8.1 (2026) is outdated, but
    DXC 1.10 preview (August) vs 1.9 stable patch (September) is not.
    """
    if not stable or not prerelease:
        return False
    if not stable.get("date") or not prerelease.get("date"):
        return False
    if prerelease["date"] > stable["date"]:
        return False
    return version_key(prerelease["version"]) <= version_key(stable["version"])


# ─── GitHub Releases ──────────────────────────────────────────────

def fetch_github_releases(repo):
    """Fetch releases from a GitHub repo. Returns (stable, prerelease)."""
    releases = net.github_json(f"/repos/{repo}/releases", params={"per_page": 50})

    stable = None
    prerelease = None

    for rel in releases:
        if rel.get("draft"):
            continue

        version = parse_version(rel["tag_name"])
        if not looks_like_version(version):
            continue
        entry = {"version": version, "date": iso_day(rel.get("published_at"))}

        if rel.get("prerelease"):
            if prerelease is None:
                prerelease = entry
        else:
            if stable is None:
                stable = entry

        if stable and prerelease:
            break

    if is_outdated_prerelease(stable, prerelease):
        prerelease = None

    return stable, prerelease


def fetch_github_tags(repo):
    """Fallback for repos without releases: the highest tag by version number.

    The refs API lists tags alphabetically ("3.4.2" after "3.10.0"), so tags
    are sorted by their numeric parts. The date is the tagged commit's date.
    """
    refs = net.github_json(f"/repos/{repo}/git/refs/tags")
    tags = [ref["ref"].removeprefix("refs/tags/") for ref in refs]
    tags = [t for t in tags if looks_like_version(parse_version(t))]
    tags.sort(key=lambda t: version_key(parse_version(t)), reverse=True)

    stable_tag = next((t for t in tags if not PRERELEASE_RE.search(t)), None)
    pre_tag = next((t for t in tags if PRERELEASE_RE.search(t)), None)
    if stable_tag and pre_tag and version_key(parse_version(pre_tag)) <= version_key(parse_version(stable_tag)):
        pre_tag = None

    def describe(tag):
        if not tag:
            return None
        commit = net.github_json(f"/repos/{repo}/commits/{tag}")
        return {"version": parse_version(tag), "date": iso_day(commit["commit"]["committer"]["date"])}

    return describe(stable_tag), describe(pre_tag)


# ─── GitHub commits ───────────────────────────────────────────────

def fetch_github_commits(source):
    """Version from the commit history, for repos that never tag a release.

    With ``regex``: the first recent commit whose message matches gives the
    version (NVAPI commits read "R620-Developer SDK"). Without it: a rolling
    version, the short sha of the latest commit, flagged ``rolling``.
    """
    repo = source["repo"]
    params = {"per_page": 50}
    if source.get("branch"):
        params["sha"] = source["branch"]
    commits = net.github_json(f"/repos/{repo}/commits", params=params)
    if not commits:
        return None

    pattern = source.get("regex")
    if not pattern:
        latest = commits[0]
        return {"version": latest["sha"][:7], "date": iso_day(latest["commit"]["committer"]["date"]),
                "rolling": True}

    regex = re.compile(pattern)
    for commit in commits:
        match = regex.search(commit["commit"]["message"])
        if match:
            version = match.group(1) if match.groups() else match.group(0)
            return {"version": version, "date": iso_day(commit["commit"]["committer"]["date"])}
    return None


# ─── NuGet ────────────────────────────────────────────────────────

def fetch_nuget_versions(package_id):
    """Fetch versions from NuGet. Returns (stable, prerelease)."""
    data = net.get_json(f"{NUGET_API}/{package_id.lower()}/index.json")
    versions = data.get("versions", [])

    stable = None
    prerelease = None

    # The index lists versions oldest first. Walking it newest first, a
    # prerelease met after the latest stable is older than it: stop there.
    for ver in reversed(versions):
        if not looks_like_version(ver):
            continue
        is_pre = bool(PRERELEASE_RE.search(ver))
        entry = {"version": ver, "date": None}

        if is_pre:
            if prerelease is None:
                prerelease = entry
        else:
            stable = entry
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
        data = net.get_json(url)
        for page in data.get("items", []):
            for item in page.get("items", []):
                entry = item.get("catalogEntry", {})
                if entry.get("version") == version:
                    return iso_day(entry.get("published"))
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

    data = net.get_json(url)

    # Navigate nested path like "windows" or "windows.x64"
    value = data
    for key in json_path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None

    if value and isinstance(value, str):
        return {"version": value, "date": None}

    return None


# ─── Scraping HTML ────────────────────────────────────────────────

def fetch_scraping_html(source):
    """Fetch version from an HTML page using CSS selector + regex."""
    # A missing scrapling raises ImportError, which fetch_entry records as a failure.
    from scrapling.fetchers import Fetcher

    url = source.get("url", "")
    selector = source.get("selector", "")
    regex = source.get("regex", "")

    if not url:
        return None

    page = Fetcher.get(url)
    if not page or page.status != 200:
        raise RuntimeError(f"HTTP {getattr(page, 'status', None)} from {url}")

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

    return None


# ─── Main fetcher ─────────────────────────────────────────────────

def fetch_entry(entry):
    """Fetch versions for an entry based on its sources.

    Returns (stable, prerelease, active_source, errors). Sources are tried in
    order; errors lists one message per source that raised, so the caller can
    tell "no version published" apart from "every source failed".
    """
    errors = []
    for source in entry.get("sources", []):
        src_type = source.get("type")

        try:
            if src_type == "github":
                stable, prerelease = fetch_github_releases(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github:{source['repo']}", errors
                # Fallback to tags
                stable, prerelease = fetch_github_tags(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github-tags:{source['repo']}", errors

            elif src_type == "github-tags":
                stable, prerelease = fetch_github_tags(source["repo"])
                if stable or prerelease:
                    return stable, prerelease, f"github-tags:{source['repo']}", errors

            elif src_type == "nuget":
                stable, prerelease = fetch_nuget_versions(source["package_id"])
                if stable or prerelease:
                    return stable, prerelease, f"nuget:{source['package_id']}", errors

            elif src_type == "github-commits":
                result = fetch_github_commits(source)
                if result:
                    return result, None, f"github-commits:{source['repo']}", errors

            elif src_type == "scraping-json":
                result = fetch_scraping_json(source)
                if result:
                    return result, None, f"scraping-json:{source.get('url', '')}", errors

            elif src_type == "scraping-html":
                result = fetch_scraping_html(source)
                if result:
                    return result, None, f"scraping-html:{source.get('url', '')}", errors

            elif src_type == "scraping":
                result = fetch_scraping_html(source)
                if result:
                    return result, None, f"scraping:{source.get('url', '')}", errors

        except Exception as e:
            print(f"    [!] {src_type} failed: {e}", file=sys.stderr)
            errors.append(f"{src_type}: {e}")
            continue

    return None, None, None, errors


def report_failure(entry_id, messages, title="Fetch failed"):
    """Print a failure, as a GitHub Actions annotation when running in CI."""
    detail = "; ".join(messages) if messages else "no source returned a version"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title={title}: {entry_id}::{detail}")
    return f"{entry_id}: {detail}"


def update_dll_versions(entry):
    """Refresh entry["dll_versions"] from its "binaries" locators. Returns the error messages."""
    locators = entry.get("binaries") or []
    if not locators:
        return []
    found, dll_errors = binaries.fetch_dll_versions(locators, entry.get("dll_versions"))
    if found:
        entry["dll_versions"] = found
        listed = ", ".join(f"{name}={rec['version']}" for name, rec in found.items())
        print(f"      dlls: {listed}")
    return dll_errors


def main():
    tracker_path = os.path.abspath(TRACKER_PATH)
    with open(tracker_path, "r", encoding="utf-8") as f:
        tracker = json.load(f)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0
    skipped = 0
    attempted = 0
    errors = []
    dll_warnings = []

    for entry in tracker["entries"]:
        sources = entry.get("sources", [])
        if entry.get("manual") or not (sources or entry.get("binaries")):
            skipped += 1
            if entry.get("manual"):
                print(f"  [{entry['id']}] (manual) ... skipped")
            continue

        if not sources:
            print(f"  [{entry['id']}] (binaries only)")
            for message in update_dll_versions(entry):
                dll_warnings.append(report_failure(entry["id"], [message], "DLL version failed"))
            continue

        attempted += 1
        source_desc = " / ".join(s.get("type") for s in sources)
        print(f"  [{entry['id']}] ({source_desc}) ... ", end="", flush=True)

        stable, prerelease, active, source_errors = fetch_entry(entry)

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
            # Keep the previous versions and last_checked: nothing was verified.
            print("FAILED")
            errors.append(report_failure(entry["id"], source_errors))

        # DLL versions are independent of the SDK version: a failure here is a
        # warning and keeps the previously known DLL versions.
        for message in update_dll_versions(entry):
            dll_warnings.append(report_failure(entry["id"], [message], "DLL version failed"))

    tracker["_meta"]["last_updated"] = today

    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {updated} updated, {skipped} skipped, {len(errors)} failed, "
          f"{len(dll_warnings)} DLL warnings.")
    for err in errors:
        print(f"  ERROR: {err}", file=sys.stderr)
    for warning in dll_warnings:
        print(f"  WARNING: {warning}", file=sys.stderr)

    # Partial failures still exit 0 so CI commits the entries that did update.
    # Exit 1 only when every automatic entry failed: that is an outage (rate
    # limit, network, token), and there is nothing worth committing.
    if attempted and len(errors) == attempted:
        print("Every automatic entry failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
