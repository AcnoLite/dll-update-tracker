# Modern UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Moderniser le dashboard GitHub Pages (style « premium dark minimal ») avec aurora animé, effets sur les cartes, thème dark/light et améliorations UX — en HTML/CSS/JS vanilla uniquement.

**Architecture:** Refactor en place des 3 fichiers existants. `style.css` réécrit autour de variables CSS (`:root` dark / `[data-theme="light"]`), `index.html` restructuré légèrement (aurora, toggle thème, contrôles sticky, script anti-FOUC), `app.js` conserve sa logique data et gagne deux modules : thème et effets.

**Tech Stack:** HTML5, CSS3 (custom properties, color-mix, backdrop-filter, IntersectionObserver-friendly), JS ES2017+ vanilla. Aucune dépendance, aucun build.

## Global Constraints

- Zéro dépendance, zéro étape de build ; le site doit rester 100 % statique (GitHub Pages).
- Ne PAS modifier : `data/tracker.json`, `scripts/*.py`, `.github/workflows/*`.
- Logique métier JS inchangée : fetch, groupement par vendor, recherche, filtres.
- Animations uniquement sur `transform` et `opacity` (perf).
- `prefers-reduced-motion: reduce` désactive toutes les animations.
- Effets souris (tilt/glow) uniquement sur `pointer: fine`.
- Contrastes texte/fond ≥ 4.5:1 dans les deux thèmes.
- Pas de framework de test : vérification = `node --check app.js` + serveur local + checklist manuelle (spec section « Plan de test »).
- Spec de référence : `docs/superpowers/specs/2026-07-30-modern-ui-redesign-design.md`.

---

### Task 1: Restructuration de `index.html`

**Files:**
- Modify: `index.html` (réécriture complète)

**Interfaces:**
- Produces (ids/classes consommés par Task 2 CSS et Tasks 3-4 JS) :
  - `<html data-theme="dark|light">` (posé par le script anti-FOUC)
  - `.aurora > .aurora-blob.blob-1|blob-2|blob-3`
  - `#theme-toggle` (button, `aria-pressed`, `aria-label`, svg `.icon-sun` + `.icon-moon`)
  - `#controls-sticky > #controls`, `.search-row`, `.search-wrapper > svg.search-icon + #search-input + kbd.search-kbd`
  - `#reset-filters` (button, attribut `hidden`)
  - Inchangés : `#stats-bar`, `#vendor-filters`, `#dashboard`, `data/tracker.json` fetch path

- [ ] **Step 1: Réécrire `index.html`**

Contenu complet du fichier :

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DLL Update Tracker</title>
  <meta name="description" content="Automatic version tracking of graphics, audio and development SDKs">
  <script>
    (function () {
      var theme = null;
      try { theme = localStorage.getItem('theme'); } catch (e) { /* private mode */ }
      if (theme !== 'light' && theme !== 'dark') {
        theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
      }
      document.documentElement.dataset.theme = theme;
    })();
  </script>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="aurora" aria-hidden="true">
    <div class="aurora-blob blob-1"></div>
    <div class="aurora-blob blob-2"></div>
    <div class="aurora-blob blob-3"></div>
  </div>

  <header>
    <h1>DLL Update Tracker</h1>
    <p class="subtitle">Automatic version tracking of graphics, audio and development SDKs</p>
    <button id="theme-toggle" type="button" aria-label="Switch theme" aria-pressed="false">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4"></circle>
        <line x1="12" y1="1" x2="12" y2="4"></line>
        <line x1="12" y1="20" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="6.34" y2="6.34"></line>
        <line x1="17.66" y1="17.66" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="4" y2="12"></line>
        <line x1="20" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="6.34" y2="17.66"></line>
        <line x1="17.66" y1="6.34" x2="19.78" y2="4.22"></line>
      </svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    </button>
  </header>

  <section id="stats-bar" role="status" aria-live="polite"></section>

  <div id="controls-sticky">
    <section id="controls">
      <div class="search-row">
        <div class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="search-input" placeholder="Search SDK (name, role, DLL...)" autocomplete="off">
          <kbd class="search-kbd">/</kbd>
        </div>
        <button id="reset-filters" type="button" hidden>Reset</button>
      </div>
      <div id="vendor-filters"></div>
    </section>
  </div>

  <main id="dashboard" aria-label="SDK list"></main>

  <footer>
    <p>
      Automatically updated every week via
      <a href="https://github.com/AcnoLite/dll-update-tracker/actions">GitHub Actions</a>
      &middot;
      <a href="https://github.com/AcnoLite/dll-update-tracker">GitHub</a>
    </p>
  </footer>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Vérifier la structure servie**

```bash
python3 -m http.server 8123 &>/tmp/http.log & sleep 1
curl -s http://localhost:8123/ | grep -c 'id="theme-toggle"\|id="controls-sticky"\|id="reset-filters"\|aurora-blob'
curl -s -o /dev/null -w '%{http_code}' http://localhost:8123/data/tracker.json
kill %1
```

Expected: `4` (au moins 4 occurrences) puis `200`. La page reste fonctionnelle avec l'ancien CSS (bouton non stylé, aurora invisible — normal à ce stade).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: restructure HTML for theme toggle, aurora and sticky controls"
```

---

### Task 2: Réécriture complète de `style.css`

**Files:**
- Modify: `style.css` (réécriture complète)

**Interfaces:**
- Consumes: ids/classes de Task 1 + classes générées par `app.js` (`.stat-card`, `.stat-value`, `.stat-label`, `.vendor-chip(.active)`, `.vendor-group`, `.vendor-header`, `.vendor-dot`, `.vendor-count`, `.card-grid`, `.sdk-card`, `.sdk-card-header`, `.sdk-name`, `.sdk-lock`, `.sdk-role`, `.sdk-dlls`, `.dll-badge(.none)`, `.sdk-versions`, `.version-row`, `.version-badge(.stable/.prerelease)`, `.version-number`, `.version-date`, `.sdk-footer`, `.sdk-sources`, `.sdk-checked`, `#empty-state`, `#error-state`, `.retry-btn`, `.loading`, `.spinner`)
- Produces: variables `--mouse-x`/`--mouse-y` (consommées par le glow JS de Task 4), classes `.reveal`/`.revealed` et `--reveal-delay` (consommées par l'observer de Task 4), classe `.scrolled` sur `#controls-sticky`.

- [ ] **Step 1: Réécrire `style.css`**

Contenu complet du fichier :

```css
/* ============ Reset ============ */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* ============ Design tokens ============ */
:root {
  /* Vendor brand colors */
  --microsoft: #0078D4;
  --amd: #ED1C24;
  --nvidia: #76B900;
  --intel: #0071C5;
  --vulkan: #AC4A2A;
  --audio: #8B5CF6;
  --other: #6B7280;

  color-scheme: dark;
  --bg: #0a0c11;
  --surface: rgba(255, 255, 255, 0.04);
  --surface-hover: rgba(255, 255, 255, 0.07);
  --border: rgba(255, 255, 255, 0.09);
  --border-strong: rgba(255, 255, 255, 0.16);
  --text: #e8eaf2;
  --text-muted: #9a9fb5;
  --text-dim: #666b80;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --accent: #58a6ff;
  --shadow: rgba(0, 0, 0, 0.5);
  --controls-bg: rgba(10, 12, 17, 0.72);
  --aurora-opacity: 0.55;
  --title-gradient: linear-gradient(120deg, #ffffff 25%, #9a9fb5 90%);

  --radius: 14px;
  --radius-sm: 9px;
  --font-mono: ui-monospace, 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
}

[data-theme="light"] {
  color-scheme: light;
  --bg: #f4f5f8;
  --surface: #ffffff;
  --surface-hover: #eceef4;
  --border: #e2e5ee;
  --border-strong: #c9cedd;
  --text: #171a24;
  --text-muted: #565c72;
  --text-dim: #878da3;
  --green: #16a34a;
  --orange: #d97706;
  --red: #dc2626;
  --accent: #0969da;
  --shadow: rgba(23, 26, 36, 0.14);
  --controls-bg: rgba(244, 245, 248, 0.78);
  --aurora-opacity: 0.28;
  --title-gradient: linear-gradient(120deg, #171a24 25%, #565c72 90%);
}

/* ============ Base ============ */
html {
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
  transition: background 0.3s ease, color 0.3s ease;
}

::selection {
  background: var(--accent);
  color: #fff;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ============ Aurora background ============ */
.aurora {
  position: fixed;
  inset: 0;
  overflow: hidden;
  z-index: -1;
  pointer-events: none;
}

.aurora-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: var(--aurora-opacity);
  will-change: transform;
}

.blob-1 {
  width: 55vw; height: 55vw;
  background: radial-gradient(circle, rgba(0, 120, 212, 0.5), transparent 65%);
  top: -18vw; left: -12vw;
  animation: drift-1 38s ease-in-out infinite alternate;
}

.blob-2 {
  width: 45vw; height: 45vw;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.45), transparent 65%);
  top: 15vh; right: -15vw;
  animation: drift-2 46s ease-in-out infinite alternate;
}

.blob-3 {
  width: 40vw; height: 40vw;
  background: radial-gradient(circle, rgba(118, 185, 0, 0.35), transparent 65%);
  bottom: -18vw; left: 25vw;
  animation: drift-3 52s ease-in-out infinite alternate;
}

@keyframes drift-1 { to { transform: translate(9vw, 7vh) scale(1.15); } }
@keyframes drift-2 { to { transform: translate(-8vw, 10vh) scale(1.1); } }
@keyframes drift-3 { to { transform: translate(10vw, -8vh) scale(1.2); } }

/* ============ Header ============ */
header {
  position: relative;
  text-align: center;
  padding: 3.5rem 1rem 1.25rem;
}

header h1 {
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  background: var(--title-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.92rem;
  margin-top: 0.35rem;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}

/* ============ Theme toggle ============ */
#theme-toggle {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: color 0.2s, border-color 0.2s, background 0.2s, transform 0.2s;
}

#theme-toggle:hover {
  color: var(--text);
  border-color: var(--border-strong);
  background: var(--surface-hover);
  transform: translateY(-1px);
}

#theme-toggle svg {
  position: absolute;
  width: 18px;
  height: 18px;
  transition: opacity 0.3s, transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

[data-theme="dark"] #theme-toggle .icon-moon,
[data-theme="light"] #theme-toggle .icon-sun {
  opacity: 0;
  transform: rotate(-90deg) scale(0.4);
}

[data-theme="dark"] #theme-toggle .icon-sun,
[data-theme="light"] #theme-toggle .icon-moon {
  opacity: 1;
  transform: rotate(0deg) scale(1);
}

/* ============ Stats bar ============ */
#stats-bar {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  flex-wrap: wrap;
  max-width: 820px;
  margin: 0 auto;
}

.stat-card {
  display: flex;
  align-items: baseline;
  gap: 0.55rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.5rem 1.15rem;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.stat-card .stat-value {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-card .stat-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ============ Sticky controls ============ */
#controls-sticky {
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 0.75rem 0;
  margin-bottom: 1.5rem;
  background: var(--controls-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid transparent;
  transition: border-color 0.25s, box-shadow 0.25s;
}

#controls-sticky.scrolled {
  border-bottom-color: var(--border);
  box-shadow: 0 10px 32px -14px var(--shadow);
}

@supports not (backdrop-filter: blur(1px)) {
  #controls-sticky { background: var(--bg); }
}

#controls {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1rem;
}

.search-row {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.7rem;
}

.search-wrapper {
  position: relative;
  flex: 1;
}

.search-icon {
  position: absolute;
  left: 0.9rem;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-dim);
  pointer-events: none;
}

#search-input {
  width: 100%;
  padding: 0.72rem 3rem 0.72rem 2.6rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}

#search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25);
}

#search-input::placeholder {
  color: var(--text-dim);
}

.search-kbd {
  position: absolute;
  right: 0.8rem;
  top: 50%;
  transform: translateY(-50%);
  font-family: inherit;
  font-size: 0.7rem;
  line-height: 1;
  color: var(--text-dim);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 0.22rem 0.42rem;
  background: var(--surface);
  pointer-events: none;
}

#reset-filters {
  padding: 0 1.05rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.18s, background 0.18s, border-color 0.18s;
}

#reset-filters:hover {
  color: var(--text);
  background: var(--surface-hover);
  border-color: var(--border-strong);
}

#reset-filters[hidden] {
  display: none;
}

@media (pointer: coarse) {
  .search-kbd { display: none; }
}

/* ============ Vendor filter chips ============ */
#vendor-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.vendor-chip {
  padding: 0.32rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  transition: color 0.18s, background 0.18s, border-color 0.18s, transform 0.18s, box-shadow 0.18s;
  user-select: none;
}

.vendor-chip:hover {
  background: var(--surface-hover);
  color: var(--text);
  transform: translateY(-1px);
}

.vendor-chip.active {
  background: var(--surface-hover);
  border-color: var(--chip-color);
  color: var(--text);
}

@supports (background: color-mix(in srgb, red 10%, blue)) {
  .vendor-chip.active {
    background: color-mix(in srgb, var(--chip-color) 22%, var(--surface));
    box-shadow: 0 2px 14px -4px color-mix(in srgb, var(--chip-color) 45%, transparent);
  }
}

/* ============ Vendor groups ============ */
.vendor-group {
  max-width: 1100px;
  margin: 0 auto 2.25rem;
  padding: 0 1rem;
}

.vendor-header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
  padding-bottom: 0.55rem;
}

.vendor-header::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--vendor-color), transparent 78%);
  opacity: 0.85;
}

.vendor-header h2 {
  font-size: 1.12rem;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.vendor-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 10px 1px var(--vendor-color);
}

.vendor-count {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

/* ============ SDK cards ============ */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 0.85rem;
}

.sdk-card {
  position: relative;
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.15rem;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.25s;
}

.sdk-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(320px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255, 255, 255, 0.06), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

@supports (background: color-mix(in srgb, red 10%, blue)) {
  .sdk-card::before {
    background: radial-gradient(320px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), color-mix(in srgb, var(--vendor-color) 13%, transparent), transparent 70%);
  }
}

.sdk-card > * {
  position: relative;
}

.sdk-card:hover {
  border-color: var(--vendor-color);
  box-shadow: 0 12px 34px -14px var(--shadow);
}

@supports (border-color: color-mix(in srgb, red 10%, blue)) {
  .sdk-card:hover {
    border-color: color-mix(in srgb, var(--vendor-color) 55%, var(--border));
    box-shadow: 0 12px 34px -14px color-mix(in srgb, var(--vendor-color) 40%, transparent);
  }
}

/* Reveal on scroll (JS adds .reveal then .revealed, removes both after transition) */
.reveal {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.5s ease-out var(--reveal-delay, 0ms),
              transform 0.5s ease-out var(--reveal-delay, 0ms);
  will-change: opacity, transform;
}

.reveal.revealed {
  opacity: 1;
  transform: none;
}

.sdk-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.sdk-name {
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}

.sdk-lock {
  font-size: 0.75rem;
  color: var(--text-dim);
  flex-shrink: 0;
}

.sdk-role {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.6rem;
  line-height: 1.45;
}

.sdk-dlls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-bottom: 0.6rem;
}

.dll-badge {
  font-size: 0.7rem;
  font-family: var(--font-mono);
  background: rgba(127, 127, 160, 0.14);
  padding: 0.15rem 0.45rem;
  border-radius: 5px;
  color: var(--text-muted);
}

.dll-badge.none {
  color: var(--text-dim);
  font-style: italic;
  font-family: inherit;
  background: none;
  padding-left: 0;
}

.sdk-versions {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.6rem;
}

.version-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
}

.version-badge {
  display: inline-block;
  padding: 0.1rem 0.42rem;
  border-radius: 5px;
  font-weight: 600;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.version-badge.stable {
  background: rgba(34, 197, 94, 0.15);
  color: var(--green);
}

.version-badge.prerelease {
  background: rgba(245, 158, 11, 0.15);
  color: var(--orange);
}

@supports (background: color-mix(in srgb, red 10%, blue)) {
  .version-badge.stable { background: color-mix(in srgb, var(--green) 16%, transparent); }
  .version-badge.prerelease { background: color-mix(in srgb, var(--orange) 16%, transparent); }
}

.version-number {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text);
}

.version-date {
  color: var(--text-dim);
  font-size: 0.73rem;
}

.sdk-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-dim);
  padding-top: 0.55rem;
  border-top: 1px solid var(--border);
}

.sdk-sources a {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.sdk-sources a:hover {
  color: var(--accent);
}

/* ============ States (empty / error / loading) ============ */
#empty-state,
#error-state,
.loading {
  animation: fade-in 0.3s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(6px); }
}

#empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
}

#empty-state p {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

#empty-state .hint {
  font-size: 0.85rem;
  color: var(--text-dim);
}

#error-state {
  text-align: center;
  padding: 3rem 1rem;
}

#error-state p {
  color: var(--red);
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.5rem 1.25rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.15s, border-color 0.15s;
}

.retry-btn:hover {
  background: var(--surface-hover);
  border-color: var(--border-strong);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin: 0 auto 0.75rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ============ Footer ============ */
footer {
  text-align: center;
  padding: 2rem 1rem 3rem;
  font-size: 0.8rem;
  color: var(--text-dim);
}

footer a {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

footer a:hover {
  color: var(--accent);
}

/* ============ Reduced motion ============ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .aurora-blob { animation: none; }
  .reveal { opacity: 1; transform: none; }
}

/* ============ Responsive ============ */
@media (max-width: 700px) {
  header { padding: 2.4rem 1rem 1rem; }
  header h1 { font-size: 1.45rem; }
  #theme-toggle { top: 0.9rem; right: 0.9rem; width: 36px; height: 36px; }
  .card-grid { grid-template-columns: 1fr; }
  #stats-bar { gap: 0.5rem; padding: 0.75rem; }
  .stat-card { padding: 0.35rem 0.8rem; gap: 0.4rem; }
  .stat-card .stat-value { font-size: 1rem; }
  #controls-sticky { padding: 0.6rem 0; }
}
```

- [ ] **Step 2: Vérifier que la page se sert sans erreur**

```bash
python3 -m http.server 8123 &>/tmp/http.log & sleep 1
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8123/style.css
kill %1
```

Expected: `200`. Revue visuelle manuelle : thème dark avec aurora, bouton toggle stylé (icône soleil), cartes modernisées. Le toggle ne fonctionne pas encore (Task 3) — normal.

- [ ] **Step 3: Commit**

```bash
git add style.css
git commit -m "feat: rewrite CSS with design tokens, light theme and effect styles"
```

---

### Task 3: `app.js` — module thème

**Files:**
- Modify: `app.js`

**Interfaces:**
- Consumes: `#theme-toggle` et `document.documentElement.dataset.theme` (Task 1).
- Produces: `initTheme()` appelée au `DOMContentLoaded` ; aucune interface consommée par Task 4.

- [ ] **Step 1: Ajouter le module thème dans `app.js`**

Insérer après le bloc `const $$ = ...` (ligne 14) :

```js
/* ================= Theme ================= */

function currentTheme() {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
}

function syncThemeButton() {
  const btn = $('#theme-toggle');
  if (!btn) return;
  const light = currentTheme() === 'light';
  btn.setAttribute('aria-pressed', String(light));
  btn.setAttribute('aria-label', light ? 'Switch to dark theme' : 'Switch to light theme');
}

function toggleTheme() {
  const next = currentTheme() === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('theme', next); } catch { /* private mode */ }
  syncThemeButton();
}

function initTheme() {
  const btn = $('#theme-toggle');
  if (btn) btn.addEventListener('click', toggleTheme);
  syncThemeButton();
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    let stored = null;
    try { stored = localStorage.getItem('theme'); } catch { /* private mode */ }
    if (!stored) {
      document.documentElement.dataset.theme = e.matches ? 'light' : 'dark';
      syncThemeButton();
    }
  });
}
```

Remplacer la dernière ligne `document.addEventListener('DOMContentLoaded', init);` par :

```js
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  init();
});
```

- [ ] **Step 2: Vérifier la syntaxe**

```bash
node --check app.js && echo OK
```

Expected: `OK`

- [ ] **Step 3: Test manuel rapide**

Servir (`python3 -m http.server 8123`), cliquer le toggle : le thème bascule, l'icône tourne, la préférence survit au rechargement, aucune erreur console.

- [ ] **Step 4: Commit**

```bash
git add app.js
git commit -m "feat: add dark/light theme toggle with persistence"
```

---

### Task 4: `app.js` — effets & UX (compteurs, reveal, tilt/glow, sticky, raccourcis, reset)

**Files:**
- Modify: `app.js`

**Interfaces:**
- Consumes: `.reveal`/`.revealed`/`--reveal-delay`, `--mouse-x`/`--mouse-y`, `#controls-sticky` + `.scrolled`, `#reset-filters`, `.search-kbd` (Tasks 1-2) ; `initTheme()` (Task 3).
- Produces: aucune nouvelle interface externe.

- [ ] **Step 1: Ajouter les constantes et le module effets**

Insérer après `let initialized = false;` (ligne 17 d'origine) :

```js
const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const FINE_POINTER = window.matchMedia('(pointer: fine)').matches;

let revealObserver = null;
```

Insérer après la fonction `initTheme()` (fin du module thème, Task 3) :

```js
/* ================= Effects & UX ================= */

function animateValue(el, target) {
  if (REDUCED_MOTION || target === 0) {
    el.textContent = String(target);
    return;
  }
  const duration = 600;
  const start = performance.now();
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = String(Math.round(target * eased));
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function attachCardEffects(card) {
  if (!FINE_POINTER || REDUCED_MOTION) return;
  let rafId = null;
  let lastEvent = null;

  card.addEventListener('mousemove', (e) => {
    lastEvent = e;
    if (rafId !== null) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      if (!lastEvent) return;
      const rect = card.getBoundingClientRect();
      const x = lastEvent.clientX - rect.left;
      const y = lastEvent.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
      const rx = ((y / rect.height) - 0.5) * -4;
      const ry = ((x / rect.width) - 0.5) * 4;
      card.style.transform = `perspective(800px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg)`;
    });
  });

  card.addEventListener('mouseleave', () => {
    if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
    lastEvent = null;
    card.style.transition = 'transform 0.35s ease-out';
    card.style.transform = '';
    setTimeout(() => { card.style.transition = ''; }, 350);
  });
}

function getRevealObserver() {
  if (revealObserver) return revealObserver;
  revealObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('revealed');
      revealObserver.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
  return revealObserver;
}

function prepareReveals(container) {
  const cards = [...container.querySelectorAll('.sdk-card')];
  if (REDUCED_MOTION) {
    cards.forEach(attachCardEffects);
    return;
  }
  const observer = getRevealObserver();
  cards.forEach((card, i) => {
    card.style.setProperty('--reveal-delay', `${Math.min(i, 14) * 30}ms`);
    card.classList.add('reveal');
    // N'agit qu'à la fin du reveal (opacity/transform), pas sur les transitions
    // de hover (border-color etc.) : évite un retrait prématuré des classes.
    const onRevealEnd = (e) => {
      if (e.propertyName !== 'opacity' && e.propertyName !== 'transform') return;
      card.classList.remove('reveal', 'revealed');
      card.style.removeProperty('--reveal-delay');
      attachCardEffects(card);
      card.removeEventListener('transitionend', onRevealEnd);
    };
    card.addEventListener('transitionend', onRevealEnd);
    observer.observe(card);
  });
}

function isDefaultFilters() {
  return $('#search-input').value.trim() === ''
    && $$('.vendor-chip.active').length === VENDOR_ORDER.length;
}

function updateResetButton() {
  $('#reset-filters').hidden = isDefaultFilters();
}

function resetFilters() {
  $('#search-input').value = '';
  $$('.vendor-chip').forEach(c => c.classList.add('active'));
  renderDashboard();
}

function initStickyControls() {
  const bar = $('#controls-sticky');
  if (!bar) return;
  const onScroll = () => bar.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    const typing = tag === 'INPUT' || tag === 'TEXTAREA';
    if (e.key === '/' && !typing) {
      e.preventDefault();
      $('#search-input').focus();
    } else if (e.key === 'Escape' && document.activeElement === $('#search-input')) {
      $('#search-input').value = '';
      $('#search-input').blur();
      renderDashboard();
    }
  });
}
```

- [ ] **Step 2: Brancher les effets dans le rendu existant**

Dans `renderStats`, remplacer le `$('#stats-bar').innerHTML = ...` (valeurs en dur) par des valeurs animées — nouveau contenu de la fonction :

```js
function renderStats(entries) {
  const total = entries.length;
  const stable = entries.filter(e => e.versions?.stable?.version).length;
  const pre = entries.filter(e => e.versions?.prerelease?.version).length;
  const auto = entries.filter(e => e.active_source).length;
  const manual = entries.filter(e => e.manual).length;

  $('#stats-bar').innerHTML = `
    <div class="stat-card"><div class="stat-value" data-target="${total}">0</div><div class="stat-label">SDKs tracked</div></div>
    <div class="stat-card"><div class="stat-value" data-target="${stable}" style="color:var(--green)">0</div><div class="stat-label">Stable</div></div>
    <div class="stat-card"><div class="stat-value" data-target="${pre}" style="color:var(--orange)">0</div><div class="stat-label">Pre-release</div></div>
    <div class="stat-card"><div class="stat-value" data-target="${auto}">0</div><div class="stat-label">Auto</div></div>
    <div class="stat-card"><div class="stat-value" data-target="${manual}" style="color:var(--text-dim)">0</div><div class="stat-label">Manual</div></div>
  `;

  $$('#stats-bar .stat-value').forEach(el => animateValue(el, Number(el.dataset.target) || 0));
}
```

Dans `renderDashboard`, cas vide — remplacer :

```js
  if (filtered.length === 0) {
    main.innerHTML = `<div id="empty-state"><p>No SDK found</p><p class="hint">Try changing your search or filters</p></div>`;
    return;
  }
```

par :

```js
  if (filtered.length === 0) {
    main.innerHTML = `<div id="empty-state"><p>No SDK found</p><p class="hint">Try changing your search or filters</p></div>`;
    updateResetButton();
    return;
  }
```

Et à la fin de `renderDashboard` (après `main.innerHTML = ...`), ajouter :

```js
  prepareReveals(main);
  updateResetButton();
```

- [ ] **Step 3: Brancher l'init**

Dans `init()`, bloc `if (!initialized)`, ajouter après le listener `#search-input` :

```js
      $('#reset-filters').addEventListener('click', resetFilters);
```

Remplacer le `DOMContentLoaded` final par :

```js
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initStickyControls();
  initKeyboardShortcuts();
  init();
});
```

- [ ] **Step 4: Vérifier la syntaxe**

```bash
node --check app.js && echo OK
```

Expected: `OK`

- [ ] **Step 5: Test manuel complet**

Servir (`python3 -m http.server 8123`) et vérifier :
1. Compteurs des stats animés de 0 → valeur au chargement.
2. Cartes révélées en cascade au chargement et au scroll.
3. Hover carte : glow radial suit le curseur + tilt léger ; sortie : retour fluide.
4. Recherche/filtres : nouvelles cartes révélées, bouton Reset apparaît ; Reset restaure l'état par défaut.
5. `/` focus la recherche, `Échap` vide et blur.
6. Scroll : barre de contrôle sticky avec bordure/ombre (classe `.scrolled`).
7. DevTools → Rendering → `prefers-reduced-motion: reduce` : aucune animation, contenu affiché immédiatement.
8. Console sans erreur.

- [ ] **Step 6: Commit**

```bash
git add app.js
git commit -m "feat: add counters, scroll reveal, card tilt/glow and UX shortcuts"
```

---

### Task 5: QA finale & PR

**Files:**
- Aucun (vérification uniquement)

- [ ] **Step 1: Relecture du diff complet**

```bash
git diff main...feat/modern-ui-redesign --stat
git diff main...feat/modern-ui-redesign
```

Expected: seuls `index.html`, `style.css`, `app.js`, `docs/superpowers/**` modifiés. Aucune régression de la logique data (fetch, filtres, recherche, groupement vendor).

- [ ] **Step 2: Checklist manuelle de la spec**

Reprendre le « Plan de test » de la spec (7 points : rendu dark+aurora, toggle sans flash + persistance, recherche/filtres/reset/raccourcis, reveal/tilt/glow desktop vs mobile, sticky, reduced-motion, états erreur/empty/loading + console propre).

- [ ] **Step 3: Push & PR**

```bash
git push
gh pr create --title "feat: modern UI/UX redesign" --body "Spec: docs/superpowers/specs/2026-07-30-modern-ui-redesign-design.md"
```

La CI ne contient pas de checks sur les PR (workflow `update_tracker.yml` = schedule uniquement) : merge direct après validation visuelle par l'utilisateur.
