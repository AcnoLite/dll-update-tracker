# Contributing

## Project structure

```
data/tracker.json       # Data: list of tracked SDKs/technologies
scripts/
  fetch_versions.py     # Fetches SDK versions from GitHub/NuGet/web
  binaries.py           # Reads DLL file versions from the published binaries
  net.py                # Shared HTTP session (retries on 429/5xx)
  generate_readme.py    # Generates README.md from tracker.json
  requirements.txt      # Python dependencies (Python 3.15+, see .python-version)
tests/                  # Unit tests (python -m unittest discover -s tests)
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
- **`github-tags`** — GitHub tags (if the repo has no releases). The highest tag by version number wins. `"repo": "owner/repo"`
- **`github-commits`** — For repos that never tag. With `"regex"`, the first recent commit message that matches gives the version (group 1): `{"repo": "NVIDIA/nvapi", "regex": "^(R\\d+)"}`. Without it, the version is the latest commit's short sha, flagged `"rolling": true` (shown as "latest commit", kept out of the recent releases feed). Optional `"branch"`.
- **`nuget`** — NuGet package. `"package_id": "Package.Name"`
- **`pe-version`** — File version of a remote DLL or installer EXE behind a stable "latest" link, read over HTTP Range (date from `Last-Modified`). `"url": "https://aka.ms/vs/17/release/vc_redist.x64.exe"`
- **`scraping-json`** — JSON endpoint. `"url": "...", "json_path": "version"` (dot-delimited path)
- **`scraping-html`** — HTML page with CSS selector + optional regex. `"url": "...", "selector": "h1", "regex": "v(\\d+\\.\\d+)"`

If multiple sources are listed, they are tried in order. The first one to respond is used.

If every source of an entry fails, the entry keeps its previous versions and `last_checked`, and the weekly run shows a warning. The run fails only when every automatic entry fails.

A prerelease is only reported when it is newer than the latest stable: either published after it, or on a higher version line (a `1.10` preview next to a `1.9.x` stable patch). Tags without any digit are ignored.

### DLL file versions (`binaries`)

SDK versions do not say which version each DLL carries. List `binaries` locators and the fetcher reads `VS_FIXEDFILEINFO` from the DLLs themselves, into `dll_versions` (`{"name.dll": {"version", "date", "source", "key"}}`).

```json
"binaries": [
  { "type": "github-file", "repo": "NVIDIA/DLSS", "path_regex": "lib/Windows_x86_64/rel/nvngx_dlss[dg]?\\.dll" },
  { "type": "github-release-asset", "repo": "intel/xess", "asset_regex": "XeSS_SDK_[\\d.]+\\.zip", "path_regex": "bin/[^/]+\\.dll" },
  { "type": "nuget", "package_id": "Microsoft.Direct3D.D3D12", "path_regex": "build/native/bin/x64/[^/]+\\.dll" }
]
```

- **`github-file`** — DLLs committed to the repo (default branch). `path_regex` matches the path in the repo.
- **`github-release-asset`** — DLLs inside a `.zip` or `.nupkg` attached to the latest release. `asset_regex` picks the asset, `path_regex` the members.
- **`nuget`** — DLLs inside the latest stable NuGet package.

`path_regex` must match the whole path (case-insensitive, `/` separators even when the zip uses `\`). Pick one architecture (usually x64): when two paths give the same file name, the first one wins.

Only the PE headers and the resource section are downloaded (HTTP Range), and only the matching zip members. A `key` (blob sha, asset id, package version) is stored with each DLL: unchanged binaries are never downloaded again. A failing locator keeps the DLL versions from the previous run and shows a warning; it never fails the run. DLLs without a version resource are skipped.

To find the right paths, list an archive's members:

```bash
python -c "import sys; sys.path.insert(0, 'scripts'); import binaries, zipfile; _, f = binaries.open_remote('<asset or .nupkg URL>'); print(*zipfile.ZipFile(f).namelist(), sep='\n')"
```

### Entry keys

| Field | Description |
|---|---|
| `vendor` | Display group: `microsoft`, `amd`, `nvidia`, `intel`, `vulkan`, `audio`, `other` |
| `manual` | `true` = do not fetch automatically, manual update only |
| `dlls` | List of produced DLLs (shown even when no file version is known) |
| `binaries` | Optional locators of the DLL binaries, see above |
| `dll_versions` | Written by the fetcher: file version per DLL |
| `role` | Description of the technical role |

## Running locally

```bash
python3.15 -m venv .venv && source .venv/bin/activate   # Python 3.15+ required
pip install -r scripts/requirements.txt

python scripts/fetch_versions.py
python scripts/generate_readme.py
```

The CI runs automatically every Monday at 8 AM UTC. You can also manually trigger the workflow from the Actions tab on GitHub.

## Proposing a change

1. Create a branch, commit, push
2. Open a PR against `main`
