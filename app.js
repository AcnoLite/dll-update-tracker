const VENDOR_META = {
  microsoft: { color: '#0078D4', label: 'Microsoft' },
  amd:       { color: '#ED1C24', label: 'AMD' },
  nvidia:    { color: '#76B900', label: 'NVIDIA' },
  intel:     { color: '#0071C5', label: 'Intel' },
  vulkan:    { color: '#AC4A2A', label: 'Vulkan' },
  audio:     { color: '#8B5CF6', label: 'Audio' },
  other:     { color: '#6B7280', label: 'Other' },
};

const VENDOR_ORDER = ['microsoft','amd','nvidia','intel','vulkan','audio','other'];

/* Age thresholds, in days, used to grade how current a version is. */
const FRESH_DAYS = 7;
const RECENT_DAYS = 90;
const OLD_DAYS = 365;

/* Recent releases feed: releases inside this window, capped, with a floor so it is never empty. */
const FEED_WINDOW_DAYS = 45;
const FEED_MAX = 10;
const FEED_MIN = 5;

/* DLL lists longer than this are folded behind a "N more DLLs" toggle. */
const DLL_PREVIEW = 5;

const DAY_MS = 86400000;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

/* ================= Theme ================= */

function currentTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
}

function syncThemeButton() {
  const btn = $('#theme-toggle');
  if (!btn) return;
  const dark = currentTheme() === 'dark';
  btn.setAttribute('aria-pressed', String(dark));
  btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
}

function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('theme', next); } catch { /* private mode */ }
  syncThemeButton();
}

function initTheme() {
  const btn = $('#theme-toggle');
  if (btn) btn.addEventListener('click', toggleTheme);
  syncThemeButton();
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    let stored = null;
    try { stored = localStorage.getItem('theme'); } catch { /* private mode */ }
    if (!stored) {
      document.documentElement.dataset.theme = e.matches ? 'dark' : 'light';
      syncThemeButton();
    }
  });
}

const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let allEntries = [];
let initialized = false;

/* ================= Dates ================= */

/* Parses "YYYY-MM-DD" as a local calendar date, so it never shifts by a day across time zones. */
function parseDate(dateStr) {
  if (typeof dateStr !== 'string') return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return isNaN(d.getTime()) ? null : d;
}

function startOfToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

function daysSince(date) {
  return Math.max(0, Math.round((startOfToday() - date) / DAY_MS));
}

function fmtDate(dateStr, opts = { month: 'short', day: 'numeric', year: 'numeric' }) {
  const d = parseDate(dateStr);
  return d ? d.toLocaleDateString('en-GB', opts) : '';
}

const relativeFormat = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

function fmtAge(days) {
  if (days < 14) return relativeFormat.format(-days, 'day');
  if (days < 60) return relativeFormat.format(-Math.round(days / 7), 'week');
  if (days < 730) return relativeFormat.format(-Math.round(days / 30.44), 'month');
  return relativeFormat.format(-Math.round(days / 365.25), 'year');
}

function ageClass(days) {
  if (days <= FRESH_DAYS) return 'age-fresh';
  if (days <= RECENT_DAYS) return 'age-recent';
  if (days <= OLD_DAYS) return 'age-old';
  return 'age-stale';
}

/* ================= Helpers ================= */

function isValidUrl(str) {
  try { return new URL(str).protocol.startsWith('http'); } catch { return false; }
}

/* Escapes quotes too, since values are also interpolated into attributes (href, id). */
const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, ch => HTML_ESCAPES[ch]);
}

function versionHtml(version, days) {
  const text = escapeHtml(version);
  return days !== null && days <= FRESH_DAYS
    ? `<mark class="fresh">${text}</mark>`
    : text;
}

/* ================= Status line ================= */

function renderStatus(meta) {
  const dlls = allEntries.flatMap(dllItems);
  const versioned = dlls.filter(d => d.record?.version).length;
  const checked = meta.last_updated
    || allEntries.map(e => e.last_checked).filter(Boolean).sort().pop();
  const when = fmtDate(checked, { day: 'numeric', month: 'long', year: 'numeric' });
  $('#status-line').textContent =
    `${allEntries.length} SDKs and ${dlls.length} DLLs, ${versioned} of them with a version read from the file.`
    + (when ? ` Last checked ${when}.` : '');
}

/* ================= Recent releases ================= */

function collectReleases() {
  const releases = [];
  for (const e of allEntries) {
    for (const channel of ['stable', 'prerelease']) {
      const v = e.versions?.[channel];
      const date = parseDate(v?.date);
      // Rolling versions are commits, not releases: they would flood the feed.
      if (!v?.version || !date || v.rolling) continue;
      releases.push({ entry: e, channel, version: v.version, date, days: daysSince(date) });
    }
  }
  releases.sort((a, b) => b.date - a.date || a.entry.name.localeCompare(b.entry.name));
  return releases;
}

function renderRecent() {
  const releases = collectReleases();
  const inWindow = releases.filter(r => r.days <= FEED_WINDOW_DAYS);
  const feed = (inWindow.length >= FEED_MIN ? inWindow : releases.slice(0, FEED_MIN)).slice(0, FEED_MAX);
  const list = $('#recent-list');

  if (feed.length === 0) {
    list.innerHTML = `<li class="recent-empty">No dated releases yet. They appear after the next weekly check.</li>`;
    return;
  }

  list.innerHTML = feed.map(r => {
    const meta = VENDOR_META[r.entry.vendor] || VENDOR_META.other;
    const iso = `${r.date.getFullYear()}-${String(r.date.getMonth() + 1).padStart(2, '0')}-${String(r.date.getDate()).padStart(2, '0')}`;
    return `
      <li class="recent-item ${ageClass(r.days)}">
        <time datetime="${iso}">${fmtDate(iso, { day: 'numeric', month: 'short' })}</time>
        <a class="recent-name" href="#sdk-${encodeURIComponent(r.entry.id)}">
          <span class="swatch" style="--vendor-color:${meta.color}" aria-hidden="true"></span>${escapeHtml(r.entry.name)}
        </a>
        <span class="recent-version">${versionHtml(r.version, r.days)}${r.channel === 'prerelease' ? '<span class="channel">pre-release</span>' : ''}</span>
        <span class="recent-age">${fmtAge(r.days)}</span>
      </li>`;
  }).join('');
}

/* ================= Filters ================= */

function renderVendorFilters() {
  $('#vendor-filters').innerHTML = VENDOR_ORDER.map(key => {
    const meta = VENDOR_META[key];
    const count = allEntries.filter(e => e.vendor === key).length;
    return `<button type="button" class="vendor-chip active" aria-pressed="true" data-vendor="${key}" style="--vendor-color:${meta.color}"><span class="swatch" aria-hidden="true"></span>${meta.label}<span class="chip-count">${count}</span></button>`;
  }).join('');
}

function getActiveVendors() {
  return [...$$('.vendor-chip.active')].map(c => c.dataset.vendor);
}

function setChip(chip, active) {
  chip.classList.toggle('active', active);
  chip.setAttribute('aria-pressed', String(active));
}

function isDefaultFilters() {
  return $('#search-input').value.trim() === ''
    && $$('.vendor-chip.active').length === VENDOR_ORDER.length;
}

function updateResetButton(shown) {
  const filtered = !isDefaultFilters();
  $('#reset-filters').hidden = !filtered;
  $('#result-count').textContent = filtered ? `${shown} of ${allEntries.length} SDKs` : '';
}

function resetFilters() {
  $('#search-input').value = '';
  $$('.vendor-chip').forEach(c => setChip(c, true));
  renderDashboard();
}

/* ================= Register ================= */

function renderDashboard() {
  const query = $('#search-input').value.toLowerCase().trim();
  const activeVendors = getActiveVendors();

  const filtered = allEntries.filter(e => {
    if (!activeVendors.includes(e.vendor)) return false;
    if (!query) return true;
    const haystack = [e.name, e.role, ...dllItems(e).map(d => d.name)].join(' ').toLowerCase();
    return haystack.includes(query);
  });

  const main = $('#dashboard');

  if (filtered.length === 0) {
    main.innerHTML = `
      <div class="empty-state">
        <p>No SDK matches these filters.</p>
        <p class="hint">Check the spelling, or clear the filters to see all ${allEntries.length} SDKs.</p>
      </div>`;
    updateResetButton(0);
    return;
  }

  const grouped = {};
  for (const e of filtered) {
    (grouped[e.vendor] = grouped[e.vendor] || []).push(e);
  }

  main.innerHTML = VENDOR_ORDER
    .filter(v => grouped[v])
    .map(v => {
      const meta = VENDOR_META[v];
      const entries = grouped[v];
      return `
        <section class="vendor-group" style="--vendor-color:${meta.color}" aria-labelledby="vendor-${v}">
          <h2 id="vendor-${v}" class="vendor-title"><span class="swatch" aria-hidden="true"></span>${meta.label}<span class="vendor-count">${entries.length}</span></h2>
          <table class="register">
            <thead>
              <tr>
                <th scope="col">SDK</th>
                <th scope="col">Stable</th>
                <th scope="col">Pre-release</th>
                <th scope="col">DLLs</th>
                <th scope="col">Source</th>
              </tr>
            </thead>
            <tbody>${entries.map(e => renderRow(e, query)).join('')}</tbody>
          </table>
        </section>`;
    }).join('');

  updateResetButton(filtered.length);
}

function renderVersionCell(v, label, emptyText) {
  if (!v?.version) {
    return `<td class="version-cell is-empty" data-label="${label}">${emptyText}</td>`;
  }
  const date = parseDate(v.date);
  const days = date ? daysSince(date) : null;
  const when = date
    ? `<span class="version-when">${v.rolling ? 'Latest commit, ' : ''}<time datetime="${escapeHtml(v.date)}">${fmtDate(v.date)}</time>, ${fmtAge(days)}</span>`
    : `<span class="version-when">Release date unknown</span>`;
  return `
    <td class="version-cell ${days === null ? 'age-unknown' : ageClass(days)}" data-label="${label}">
      <span class="version">${versionHtml(v.version, days)}</span>
      ${when}
    </td>`;
}

function renderSources(entry) {
  const links = (entry.sources || []).map(s => {
    if (['github', 'github-tags', 'github-commits'].includes(s.type) && s.repo) {
      return `<a href="https://github.com/${escapeHtml(s.repo)}">GitHub</a>`;
    }
    if (s.type === 'nuget' && s.package_id) {
      return `<a href="https://www.nuget.org/packages/${escapeHtml(s.package_id)}/">NuGet</a>`;
    }
    if (s.url && isValidUrl(s.url)) {
      return `<a href="${escapeHtml(s.url)}">${escapeHtml(s.label || 'Website')}</a>`;
    }
    return '';
  }).filter(Boolean);
  return links.length ? links.join('<br>') : '<span class="muted">None</span>';
}

/* Declared DLLs first, then any extra DLL found in the binaries, each with its
   file version record when the fetcher could read it. */
function dllItems(entry) {
  const known = entry.dll_versions || {};
  const byLower = new Map(Object.entries(known).map(([name, rec]) => [name.toLowerCase(), rec]));
  const declared = entry.dlls || [];
  const declaredLower = new Set(declared.map(d => d.toLowerCase()));
  return [
    ...declared.map(name => ({ name, record: byLower.get(name.toLowerCase()) })),
    ...Object.entries(known)
      .filter(([name]) => !declaredLower.has(name.toLowerCase()))
      .map(([name, record]) => ({ name, record })),
  ];
}

function renderDll({ name, record }) {
  if (!record?.version) {
    return `<span class="dll"><span class="dll-name">${escapeHtml(name)}</span></span>`;
  }
  const date = parseDate(record.date);
  const days = date ? daysSince(date) : null;
  const origin = record.source ? ` title="File version read from ${escapeHtml(record.source)}"` : '';
  return `<span class="dll"><span class="dll-name">${escapeHtml(name)}</span><span class="dll-version"${origin}>${versionHtml(record.version, days)}</span></span>`;
}

/* Long lists show their first DLLs and fold the rest. The fold opens by itself
   when the search matches one of the folded names, so a hit is never hidden. */
function renderDllList(dlls, query) {
  if (dlls.length === 0) return '<span class="muted">No DLL</span>';
  if (dlls.length <= DLL_PREVIEW + 1) return dlls.map(renderDll).join('');
  const shown = dlls.slice(0, DLL_PREVIEW);
  const folded = dlls.slice(DLL_PREVIEW);
  const open = query && folded.some(d => d.name.toLowerCase().includes(query)) ? ' open' : '';
  return shown.map(renderDll).join('')
    + `<details class="dll-more"${open}><summary><span class="when-closed">${folded.length} more DLLs</span><span class="when-open">Show fewer</span></summary>${folded.map(renderDll).join('')}</details>`;
}

function renderRow(entry, query = '') {
  const versions = entry.versions || {};
  const dlls = dllItems(entry);
  const stableEmpty = entry.manual ? 'Updated by hand' : 'Not found';

  return `
    <tr id="sdk-${escapeHtml(entry.id)}">
      <th scope="row" class="sdk-cell">
        <span class="sdk-name">${escapeHtml(entry.name)}</span>
        ${entry.manual ? '<span class="manual-mark">manual</span>' : ''}
        ${entry.role ? `<span class="sdk-role">${escapeHtml(entry.role)}</span>` : ''}
      </th>
      ${renderVersionCell(versions.stable, 'Stable', stableEmpty)}
      ${renderVersionCell(versions.prerelease, 'Pre-release', '<span class="muted">None</span>')}
      <td class="dll-cell" data-label="DLLs">${renderDllList(dlls, query)}</td>
      <td class="source-cell" data-label="Source">${renderSources(entry)}</td>
    </tr>`;
}

/* ================= Behaviour ================= */

/* Jump to an SDK row. If the filters hide it, clear them first: a link from the
   recent releases feed must always land somewhere. */
function goToSdk(hash) {
  if (!hash.startsWith('#sdk-')) return false;
  let row = document.getElementById(decodeURIComponent(hash.slice(1)));
  if (!row) {
    resetFilters();
    row = document.getElementById(decodeURIComponent(hash.slice(1)));
  }
  if (!row) return false;
  if (location.hash !== hash) {
    history.pushState(null, '', hash);
  }
  $$('.register tr.is-target').forEach(r => r.classList.remove('is-target'));
  row.classList.add('is-target');
  row.scrollIntoView({ block: 'start', behavior: REDUCED_MOTION ? 'auto' : 'smooth' });
  return true;
}

function initSdkLinks() {
  $('#recent-list').addEventListener('click', (e) => {
    const link = e.target.closest('a.recent-name');
    if (link && goToSdk(link.getAttribute('href'))) e.preventDefault();
  });
  window.addEventListener('popstate', () => goToSdk(location.hash));
}

function initStickyControls() {
  const bar = $('#controls-sticky');
  if (!bar) return;
  const onScroll = () => bar.classList.toggle('scrolled', bar.getBoundingClientRect().top <= 0);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement && document.activeElement.tagName;
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

function showLoading() {
  $('#dashboard').innerHTML = `<p class="loading">Loading the register…</p>`;
}

function showError(msg) {
  $('#status-line').textContent = 'The register could not be loaded.';
  $('#recent-list').innerHTML = '';
  $('#dashboard').innerHTML = `
    <div class="error-state">
      <p>${escapeHtml(msg)}</p>
      <button class="retry-btn" type="button">Try again</button>
    </div>`;
  $('#dashboard .retry-btn').addEventListener('click', init);
}

async function init() {
  showLoading();

  try {
    const res = await fetch('data/tracker.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();
    allEntries = data.entries || [];

    if (!initialized) {
      initialized = true;
      $('#vendor-filters').addEventListener('click', (e) => {
        const chip = e.target.closest('.vendor-chip');
        if (!chip) return;
        setChip(chip, !chip.classList.contains('active'));
        renderDashboard();
      });
      $('#search-input').addEventListener('input', renderDashboard);
      $('#reset-filters').addEventListener('click', resetFilters);
      initSdkLinks();
    }

    renderStatus(data._meta || {});
    renderRecent();
    renderVendorFilters();
    renderDashboard();
    // The rows exist only now: honour a #sdk-… link opened directly.
    if (location.hash) goToSdk(location.hash);
  } catch (err) {
    console.error('Failed to load tracker data:', err);
    showError('Could not read data/tracker.json. Check that the file exists and is valid JSON, then try again.');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initStickyControls();
  initKeyboardShortcuts();
  init();
});
