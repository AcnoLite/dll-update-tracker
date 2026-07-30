# Contributing

## Project structure

```
data/tracker.json       # Données : liste des SDK/technos trackés
scripts/
  fetch_versions.py     # Récupère les versions depuis GitHub/NuGet/web
  generate_readme.py    # Génère README.md depuis tracker.json
  requirements.txt      # Dépendances Python
.github/workflows/
  update_tracker.yml    # CI : cron hebdo + workflow_dispatch
```

## Ajouter un nouveau SDK

Éditer `data/tracker.json` et ajouter une entrée dans `entries` :

```json
{
  "id": "mon-sdk",
  "vendor": "microsoft",
  "name": "Mon SDK",
  "role": "Description courte de ce que ça fait",
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

Le CI mettra automatiquement à jour `versions` et `last_checked`.

### Types de sources

- **`github`** — releases GitHub (priorité). `"repo": "owner/repo"`
- **`github-tags`** — tags GitHub (si le repo n'a pas de releases). `"repo": "owner/repo"`
- **`nuget`** — package NuGet. `"package_id": "Package.Name"`
- **`scraping-json`** — endpoint JSON. `"url": "...", "json_path": "version"` (chemin délimité par `.`)
- **`scraping-html`** — page HTML avec CSS selector + regex optionnel. `"url": "...", "selector": "h1", "regex": "v(\\d+\\.\\d+)"`

Si plusieurs sources sont listées, elles sont essayées dans l'ordre. La première qui répond est utilisée.

### Clés d'entrée

| Champ | Description |
|---|---|
| `vendor` | Groupe d'affichage : `microsoft`, `amd`, `nvidia`, `intel`, `vulkan`, `audio`, `other` |
| `manual` | `true` = ne pas fetch automatiquement, mise à jour manuelle |
| `dlls` | Liste des DLL produites |
| `role` | Description du rôle technique |

## En local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt

python scripts/fetch_versions.py
python scripts/generate_readme.py
```

Le CI tourne automatiquement chaque lundi à 8h UTC. Tu peux aussi déclencher manuellement le workflow depuis l'onglet Actions de GitHub.

## Proposer un changement

1. Créer une branche, commiter, pousser
2. Ouvrir une PR sur `main`
