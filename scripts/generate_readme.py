#!/usr/bin/env python3
"""Generate README.md from tracker.json data."""

import json
import os
import sys
from datetime import datetime, timezone

TRACKER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracker.json")
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

VENDOR_ORDER = ["microsoft", "amd", "nvidia", "intel", "vulkan", "audio", "other"]
VENDOR_LABELS = {
    "microsoft": ("Microsoft", "\U0001f7e6"),
    "amd": ("AMD", "\U0001f7e5"),
    "nvidia": ("NVIDIA", "\U0001f7e2"),
    "intel": ("Intel", "\U0001f7ea"),
    "vulkan": ("Vulkan", "\U0001f7e8"),
    "audio": ("Audio", "\U0001f50a"),
    "other": ("Other", "\U0001f4e6"),
}


def fmt_version(v):
    """Format version entry to (display_string, date)."""
    if not v:
        return "-", "-"
    ver = v.get("version", "-")
    date = v.get("date") or "?"
    return ver, date


def source_links(entry):
    """Build source display string from sources array."""
    parts = []
    for src in entry.get("sources", []):
        t = src.get("type", "")
        if t in ("github", "github-tags"):
            repo = src.get("repo", "")
            parts.append(f"[{repo}](https://github.com/{repo})")
        elif t == "nuget":
            pkg = src.get("package_id", "")
            parts.append(f"[NuGet](https://www.nuget.org/packages/{pkg}/)")
        elif t == "vulkan-sdk":
            parts.append(f"[Lunarg](https://vulkan.lunarg.com/sdk/home)")
        elif t == "scraping":
            url = src.get("url", "#")
            label = src.get("label", "Website")
            parts.append(f"[{label}]({url})")
    return " / ".join(parts) if parts else "-"


def build_rows(entries):
    """Build table rows."""
    rows = []
    for e in entries:
        versions = e.get("versions", {})
        stable = versions.get("stable")
        pre = versions.get("prerelease")

        s_ver, s_date = fmt_version(stable)
        p_ver, p_date = fmt_version(pre)

        dlls = e.get("dlls", [])
        if dlls:
            dlls_str = ", ".join(f"`{d}`" for d in dlls)
        else:
            dlls_str = "\u26a0\ufe0f None"

        src = source_links(e)
        checked = e.get("last_checked") or "-"

        # Version display with dates
        if stable and s_date != "?":
            s_display = f"`{s_ver}` ({s_date})"
        elif stable:
            s_display = f"`{s_ver}`"
        else:
            s_display = "-"

        if pre and p_date != "?":
            p_display = f"`{p_ver}` ({p_date})"
        elif pre:
            p_display = f"`{p_ver}`"
        else:
            p_display = "-"

        rows.append({
            "name": e["name"],
            "dlls": dlls_str,
            "source": src,
            "stable": s_display,
            "prerelease": p_display,
            "checked": checked,
            "manual": e.get("manual", False),
        })
    return rows


def vendor_section(vendor_key, entries):
    label, emoji = VENDOR_LABELS.get(vendor_key, (vendor_key, ""))
    lines = []
    lines.append(f"## {emoji} {label}\n")
    lines.append("| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |")
    lines.append("|---|---|---|---|---|---|")

    for r in build_rows(entries):
        name = r['name']
        if r['manual']:
            name += ' \U0001f512'
        lines.append(f"| **{name}** | {r['dlls']} | {r['source']} | {r['stable']} | {r['prerelease']} | {r['checked']} |")

    lines.append("")
    return "\n".join(lines)


def main():
    tracker_path = os.path.abspath(TRACKER_PATH)
    with open(tracker_path, "r", encoding="utf-8") as f:
        tracker = json.load(f)

    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    entries = tracker.get("entries", [])

    # Group by vendor
    by_vendor = {}
    for e in entries:
        v = e.get("vendor", "other")
        by_vendor.setdefault(v, []).append(e)

    total = len(entries)
    with_stable = sum(1 for e in entries if e.get("versions", {}).get("stable"))
    with_pre = sum(1 for e in entries if e.get("versions", {}).get("prerelease"))
    auto = sum(1 for e in entries if e.get("active_source"))

    lines = []
    lines.append("# DLL Update Tracker\n")
    lines.append(f"> Last updated: **{today}**")
    lines.append(f"> **{total}** SDKs/technologies tracked | **{with_stable}** stable | **{with_pre}** pre-release | **{auto}** auto-tracked")
    lines.append(">")
    lines.append("> Automatic tracking of graphics, audio and tools DLLs (upscaling, frame gen, low latency, ray tracing, physics, debug, audio middleware).")
    lines.append("> Versions are fetched via GitHub APIs, NuGet and web scraping.")
    lines.append("")
    lines.append("---\n")

    for vk in VENDOR_ORDER:
        if vk in by_vendor:
            lines.append(vendor_section(vk, by_vendor[vk]))
            lines.append("---\n")

    lines.append("")
    lines.append("## Update\n")
    lines.append("```bash")
    lines.append("# All at once")
    lines.append("python scripts/fetch_versions.py && python scripts/generate_readme.py")
    lines.append("")
    lines.append("# Or separately")
    lines.append("python scripts/fetch_versions.py")
    lines.append("python scripts/generate_readme.py")
    lines.append("```")
    lines.append("")
    lines.append("GitHub Actions: cron every Monday 8am UTC + manual trigger.")
    lines.append("")

    readme_path = os.path.abspath(README_PATH)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"README.md generated ({len(lines)} lines)")


if __name__ == "__main__":
    main()
