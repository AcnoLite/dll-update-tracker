# Spec — Modernisation UI/UX du dashboard GitHub Pages

Date : 2026-07-30
Branche : `feat/modern-ui-redesign`
Statut : approuvé par l'utilisateur (brainstorming validé)

## Objectif

Rendre le dashboard GitHub Pages moderne avec des effets stylés, en restant
strictement en HTML + CSS + JS vanilla (aucune dépendance, aucun build).

Direction retenue : **« Premium dark minimal »** (style Linear / Vercel / Raycast).

Périmètre validé (4 axes) :
1. Restyle visuel complet
2. Animations & effets
3. Toggle dark / light
4. Petites améliorations UX

## Hors périmètre (ne change PAS)

- `data/tracker.json` et son schéma
- `scripts/fetch_versions.py`, `scripts/generate_readme.py`
- GitHub Actions / CI
- Logique métier de `app.js` : fetch, groupement par vendor, recherche, filtres
- Compatibilité GitHub Pages (site 100 % statique)

## Architecture

Refactor en place, 3 fichiers uniquement :

| Fichier | Changement |
|---|---|
| `index.html` | Restructuration légère : conteneur aurora, bouton toggle thème dans le header, script anti-FOUC inline dans `<head>` |
| `style.css` | Réécriture complète autour de variables CSS. Thème dark dans `:root`, thème light dans `[data-theme="light"]` |
| `app.js` | Logique data inchangée + deux modules ajoutés : gestion du thème, effets visuels |

Alternatives écartées :
- Découper en `css/` + `js/` : sur-ingénierie pour une seule page.
- Empiler des overrides sur le CSS actuel : cascade fragile, dette.

## Direction visuelle

### Fond aurora animé

- 2-3 « blobs » en dégradé radial (teintes vendor assombries : bleu Microsoft,
  vert NVIDIA, violet), `filter: blur(120px)`, positionnés en `fixed` derrière le
  contenu (`z-index: -1`, `pointer-events: none`).
- Dérive lente via `@keyframes` sur `transform` uniquement (GPU-friendly).
- Opacité fortement réduite en light mode.
- Désactivé sous `prefers-reduced-motion` (blobs statiques ou cachés).

### Cartes SDK

- Surface translucide, bordure 1px affinée, radius conservé (12px).
- **Glow radial suivant le curseur** au hover : `background: radial-gradient(... at var(--mouse-x) var(--mouse-y), ...)` avec la couleur vendor, via listener `mousemove` (JS).
- Léger soulèvement (`translateY(-2px)`) + ombre portée teintée vendor au hover.
- Badge DLL / versions : meilleur contraste, versions en monospace.

### Header & stats

- Titre avec dégradé de texte subtil (`background-clip: text`).
- Stats en « pilules » avec **compteurs animés** (interpolation `requestAnimationFrame`).
- Bouton toggle thème aligné à droite du header.

### Typographie

- Police système conservée (performance) ; échelle affinée, `letter-spacing` négatif sur les titres.
- Numéros de version et DLL en monospace avec contraste renforcé.

## Animations & effets

| Effet | Technique | Déclencheur |
|---|---|---|
| Reveal staggeré | `IntersectionObserver` + transition opacity/translate (~30ms de décalage par carte) | apparition au scroll et après filtre/recherche |
| Tilt 3D léger (~4° max) | `transform: perspective(800px) rotateX/Y` sur `mousemove`, reset au `mouseleave` | hover carte (pointeur fin uniquement : `@media (pointer: fine)`) |
| Compteurs animés | `requestAnimationFrame`, easing ease-out, ~600ms | rendu des stats |
| Aurora drift | `@keyframes` sur `transform` | continu |
| Micro-transitions | `transition` 150-250ms `ease-out` | chips, recherche, hover, toggle thème |

Contrainte perf : aucune animation sur `width/height/top/left` ; uniquement
`transform` et `opacity`.

## Thème dark / light

- Thème dark par défaut (`:root`), light via `[data-theme="light"]` sur `<html>`.
- Toggle soleil/lune dans le header, icône SVG inline avec rotation animée.
- Persistance `localStorage` (clé `theme`) ; fallback `prefers-color-scheme` si
  aucune préférence stockée.
- **Anti-FOUC** : petit script inline dans `<head>` appliquant `data-theme` avant
  le premier paint.
- Toutes les couleurs passent par les variables CSS (y compris couleurs vendor,
  adaptées par thème si nécessaire pour le contraste).

## Améliorations UX

- Barre de contrôle (recherche + chips) **sticky** sous le header, avec fond
  flouté (`backdrop-filter: blur(...)`) et ombre discrète au scroll.
- Raccourci clavier `/` : focus sur la recherche ; `Échap` : vide la recherche
  et retire le focus.
- Bouton « Reset » affiché uniquement quand une recherche ou un filtre non
  par défaut est actif ; réactive tous les vendors et vide la recherche.

## Accessibilité

- `prefers-reduced-motion: reduce` : désactive aurora, tilt, reveal et compteurs
  (affichage final immédiat).
- `:focus-visible` visible sur tous les éléments interactifs.
- Contrastes texte/fond ≥ 4.5:1 dans les deux thèmes.
- Le toggle thème expose `aria-pressed` et un `aria-label` explicite.
- Le raccourci `/` est ignoré quand un champ a le focus.

## Responsive

- Breakpoint mobile conservé (700px) : grille 1 colonne, stats compactes.
- Tilt et glow-curseur désactivés sur pointeur tactile (`pointer: coarse`).

## Plan de test

1. Ouvrir `index.html` via un serveur local (`python -m http.server`) et vérifier :
   - rendu initial dark + aurora, chargement des données, stats animées ;
   - toggle light/dark sans flash, persistance au rechargement ;
   - recherche, filtres chips, bouton reset, raccourcis `/` et `Échap` ;
   - reveal au scroll, tilt et glow sur desktop, absence sur mobile ;
   - sticky controls au scroll.
2. `prefers-reduced-motion` (DevTools → Rendering) : toutes les animations off.
3. Vérifier console sans erreur, et état erreur/empty/loading toujours fonctionnels.

## Risques

| Risque | Mitigation |
|---|---|
| `backdrop-filter` non supporté | fallback : fond opaque via `@supports` |
| `color-mix` déjà utilisé (navigateurs modernes) | fallback couleur pleine fourni |
| Perf du glow/tilt (repaints fréquents) | handlers passifs, `requestAnimationFrame`, désactivé sur tactile |
| Régression de la logique data | logique fetch/filtres/recherche inchangée ; test manuel complet |
