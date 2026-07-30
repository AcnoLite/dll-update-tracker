# Contributing

## Project structure

```
data/tracker.json       # Data: list of tracked SDKs/technologies
scripts/
  fetch_versions.py     # Fetches versions from GitHub/NuGet/web
  generate_readme.py    # Generates README.md from tracker.json
  requirements.txt      # Python dependencies
.github/workflows/
  update_tracker.yml    # CI: weekly cron + workflow_dispatch
```

## Adding a new SDK

Edit `data/tracker.json` and add an entry in `entries`:

```json
{
  "id": "mon-sdk",
  "vendor": "microsoft",
  "name": "Mon SDK",
  "role": "Short description of what it does",
  "dlls": ["ma-dll.dll"],
  "sources": [
    { "type": "github", "repo": "vendor/mon-repo" }
  ],
  "versions": {
    "stable": null,
    "prerelease": null
  },
  "manual": false,
  "last_checked": null
}
```

The CI will automatically update `versions` and `last_checked`.

### Source types

- **`github`** — GitHub releases (preferred). `"repo": "owner/repo"`
- **`github-tags`** — GitHub tags (if the repo has no releases). `"repo": "owner/repo"`
- **`nuget`** — NuGet package. `"package_id": "Package.Name"`
- **`scraping-json`** — JSON endpoint. `"url": "...", "json_path": "version"` (dot-delimited path)
- **`scraping-html`** — HTML page with CSS selector + optional regex. `"url": "...", "selector": "h1", "regex": "v(\\d+\\.\\d+)"`

If multiple sources are listed, they are tried in order. The first one to respond is used.

### Entry keys

| Field | Description |
|---|---|
| `vendor` | Display group: `microsoft`, `amd`, `nvidia`, `intel`, `vulkan`, `audio`, `other` |
| `manual` | `true` = do not fetch automatically, manual update only |
| `dlls` | List of produced DLLs |
| `role` | Description of the technical role |

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt

python scripts/fetch_versions.py
python scripts/generate_readme.py
```

The CI runs automatically every Monday at 8 AM UTC. You can also manually trigger the workflow from the Actions tab on GitHub.

## Proposing a change

1. Create a branch, commit, push
2. Open a PR against `main`
