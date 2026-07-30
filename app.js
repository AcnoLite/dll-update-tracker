const VENDOR_META = {
  microsoft: { color: '#0078D4', label: 'Microsoft' },
  amd:       { color: '#ED1C24', label: 'AMD' },
  nvidia:    { color: '#76B900', label: 'NVIDIA' },
  intel:     { color: '#0071C5', label: 'Intel' },
  vulkan:    { color: '#AC4A2A', label: 'Vulkan' },
  audio:     { color: '#8B5CF6', label: 'Audio' },
  other:     { color: '#6B7280',     label: 'Other' },
};

const VENDOR_ORDER = ['microsoft','amd','nvidia','intel','vulkan','audio','other'];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let allEntries = [];
let initialized = false;

function fmtDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function isValidUrl(str) {
  try { return new URL(str).protocol.startsWith('http'); } catch { return false; }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderStats(entries) {
  const total = entries.length;
  const stable = entries.filter(e => e.versions?.stable?.version).length;
  const pre = entries.filter(e => e.versions?.prerelease?.version).length;
  const auto = entries.filter(e => e.active_source).length;
  const manual = entries.filter(e => e.manual).length;

  $('#stats-bar').innerHTML = `
    <div class="stat-card"><div class="stat-value">${total}</div><div class="stat-label">SDKs tracked</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--green)">${stable}</div><div class="stat-label">Stable</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--orange)">${pre}</div><div class="stat-label">Pre-release</div></div>
    <div class="stat-card"><div class="stat-value">${auto}</div><div class="stat-label">Auto</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--text-dim)">${manual}</div><div class="stat-label">Manual</div></div>
  `;
}

function renderVendorFilters() {
  const container = $('#vendor-filters');
  container.innerHTML = VENDOR_ORDER.map(key => {
    const meta = VENDOR_META[key];
    const count = allEntries.filter(e => e.vendor === key).length;
    return `<button class="vendor-chip active" data-vendor="${key}" style="--chip-color:${meta.color}">${meta.label} (${count})</button>`;
  }).join('');
}

function getActiveVendors() {
  return [...$$('.vendor-chip.active')].map(c => c.dataset.vendor);
}

function renderDashboard() {
  const query = $('#search-input').value.toLowerCase().trim();
  const activeVendors = getActiveVendors();

  const filtered = allEntries.filter(e => {
    if (!activeVendors.includes(e.vendor)) return false;
    if (!query) return true;
    const haystack = [e.name, e.role, ...(e.dlls || [])].join(' ').toLowerCase();
    return haystack.includes(query);
  });

  const main = $('#dashboard');

  if (filtered.length === 0) {
    main.innerHTML = `<div id="empty-state"><p>No SDK found</p><p class="hint">Try changing your search or filters</p></div>`;
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
      const cards = entries.map(e => renderCard(e, meta.color)).join('');
      return `
        <section class="vendor-group">
          <div class="vendor-header" style="--vendor-color:${meta.color}">
            <span class="vendor-dot" style="background:${meta.color}"></span>
            <h2>${meta.label}</h2>
            <span class="vendor-count">${entries.length}</span>
          </div>
          <div class="card-grid">${cards}</div>
        </section>
      `;
    }).join('');
}

function renderCard(entry, vendorColor) {
  const versions = entry.versions || {};
  const stable = versions.stable;
  const pre = versions.prerelease;
  const dlls = entry.dlls || [];

  const dllHtml = dlls.length > 0
    ? dlls.map(d => `<span class="dll-badge">${escapeHtml(d)}</span>`).join('')
    : '<span class="dll-badge none">No DLL</span>';

  let stableHtml = '';
  if (stable && stable.version) {
    stableHtml = `<div class="version-row"><span class="version-badge stable">Stable</span><span class="version-number">${escapeHtml(stable.version)}</span>${stable.date ? `<span class="version-date">(${fmtDate(stable.date)})</span>` : ''}</div>`;
  } else if (!entry.manual) {
    stableHtml = `<div class="version-row"><span class="version-badge stable" style="opacity:0.4">—</span></div>`;
  }

  let preHtml = '';
  if (pre && pre.version) {
    preHtml = `<div class="version-row"><span class="version-badge prerelease">Pre</span><span class="version-number">${escapeHtml(pre.version)}</span>${pre.date ? `<span class="version-date">(${fmtDate(pre.date)})</span>` : ''}</div>`;
  }

  const sources = entry.sources || [];
  const sourceHtml = sources.length > 0
    ? sources.map(s => {
        if (s.type === 'github' || s.type === 'github-tags') {
          return `<a href="https://github.com/${escapeHtml(s.repo)}">GitHub</a>`;
        }
        if (s.type === 'nuget') {
          return `<a href="https://www.nuget.org/packages/${escapeHtml(s.package_id)}/">NuGet</a>`;
        }
        if (s.url && isValidUrl(s.url)) {
          const label = s.label || 'Source';
          return `<a href="${escapeHtml(s.url)}">${escapeHtml(label)}</a>`;
        }
        return '';
      }).filter(Boolean).join(' · ')
    : '—';

  const checked = entry.last_checked ? fmtDate(entry.last_checked) : '';
  const isManual = entry.manual;

  return `
    <article class="sdk-card" style="--vendor-color:${vendorColor}">
      <div class="sdk-card-header">
        <span class="sdk-name">${escapeHtml(entry.name)}</span>
        ${isManual ? `<span class="sdk-lock" title="Manual update">🔒</span>` : ''}
      </div>
      ${entry.role ? `<div class="sdk-role">${escapeHtml(entry.role)}</div>` : ''}
      <div class="sdk-dlls">${dllHtml}</div>
      <div class="sdk-versions">${stableHtml}${preHtml}</div>
      <div class="sdk-footer">
        <span class="sdk-sources">${sourceHtml}</span>
        ${checked ? `<span class="sdk-checked">📅 ${checked}</span>` : ''}
      </div>
    </article>
  `;
}

function showLoading() {
  $('#dashboard').innerHTML = `<div class="loading"><div class="spinner"></div><span>Loading data...</span></div>`;
  $('#stats-bar').innerHTML = '';
}

function showError(msg) {
  $('#dashboard').innerHTML = `
    <div id="error-state">
      <p>${escapeHtml(msg)}</p>
      <button class="retry-btn" onclick="init()">Retry</button>
    </div>`;
  $('#stats-bar').innerHTML = '';
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
        chip.classList.toggle('active');
        renderDashboard();
      });
      $('#search-input').addEventListener('input', renderDashboard);
    }

    renderStats(allEntries);
    renderVendorFilters();
    renderDashboard();
  } catch (err) {
    console.error('Failed to load tracker data:', err);
    showError('Unable to load data. Check that data/tracker.json exists.');
  }
}

document.addEventListener('DOMContentLoaded', init);
