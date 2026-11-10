# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A tracker of the latest versions of graphics/audio/tooling SDKs that ship DLLs (DLSS, FSR, XeSS, Agility SDK, PhysX, FMOD…). It has three parts that all revolve around one data file, `data/tracker.json`:

1. **`scripts/fetch_versions.py`** queries upstream sources and rewrites `versions`, `active_source` and `last_checked` in `tracker.json` in place.
2. **`scripts/generate_readme.py`** regenerates `README.md` from `tracker.json`.
3. **A static site** (`index.html` + `app.js` + `style.css`, vanilla JS, no build step) fetches `data/tracker.json` at runtime and renders the dashboard. It is served by GitHub Pages (`.nojekyll`).

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt   # requests, scrapling[all]

python scripts/fetch_versions.py && python scripts/generate_readme.py

# Preview the site locally (fetch() needs HTTP, not file://)
python -m http.server 8000
```

Unit tests for `fetch_versions.py` live in `tests/` (stdlib `unittest`, network mocked): `python -m unittest discover -s tests`. They are not run by CI. There is no linter or build. Set `GITHUB_TOKEN` when running `fetch_versions.py` locally to avoid GitHub API rate limits.

## Rules that matter

- **Never edit `README.md` by hand.** It is fully overwritten by `generate_readme.py`. To change its layout, edit that script. The header and the "Update" section are hardcoded there too.
- **CI commits directly to `main`.** `.github/workflows/update_tracker.yml` runs every Monday at 08:00 UTC (and on manual dispatch). It runs both scripts, then commits `data/tracker.json` and `README.md` as `github-actions[bot]` with the message `chore: update DLL tracker versions [skip ci]`. Most of the git history is these commits. Expect `main` to move under you, and expect conflicts on those two files.
- To add or modify a tracked SDK, edit `entries` in `data/tracker.json`. `CONTRIBUTING.md` documents the entry schema and the source types.

## Fetch logic (`fetch_versions.py`)

- Each entry's `sources` are tried in order, and the first one that returns any version wins. The winner is recorded as `active_source` (`"<type>:<repo|package|url>"`).
- Source types: `github` (releases, falling back to tags automatically), `github-tags`, `nuget`, `scraping-json` (dot-path `json_path`), `scraping-html` (CSS `selector` + optional `regex`, via `scrapling`), plus a legacy alias `scraping`. Scraping types only produce a stable version, never a prerelease.
- Prerelease detection: for GitHub releases it uses the `prerelease` flag. Elsewhere it uses `PRERELEASE_RE` (`-alpha|beta|preview|rc|dev|nightly|pre`).
- Tags with no digit (e.g. a `utils` tooling release) are never treated as versions (`looks_like_version`).
- An outdated prerelease is dropped: for GitHub releases, one published before the latest stable and not on a higher version line (`is_outdated_prerelease`); for NuGet, any prerelease below the latest stable. `github-tags` has no dates and no reliable order, so it is not filtered.
- Entries with `manual: true` or no `sources` are skipped and keep their versions as they are (shown with 🔒 in the README).
- A source that raises is logged to stderr and the next one is tried; `fetch_entry` returns those messages. An entry with no version from any source counts as failed: its versions and `last_checked` are left untouched, and in CI it is emitted as a `::warning::` annotation.
- Exit code: 0 when at least one automatic entry updated (CI still commits partial results), 1 when every automatic entry failed (outage: rate limit, network, token), which stops the CI before it commits.

## Front-end (`app.js`)

Vendor groups are defined in two places: `VENDOR_META` / `VENDOR_ORDER` in `app.js` and `VENDOR_ORDER` / `VENDOR_LABELS` in `generate_readme.py`. To add a vendor, update both. User strings from the JSON go through `escapeHtml` / `isValidUrl` before they are inserted into the DOM.

Design specs and plans from past UI work live in `docs/superpowers/`.
