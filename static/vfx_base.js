/* =============================================================================
   VFX BUDGET SYSTEM — Shared JS Utilities  (UPDATE-SISTEM06)
   vfx_base.js  — included in every template via <script src="...">
   ============================================================================= */

'use strict';

// ---------------------------------------------------------------------------
// 1. MONEY & NUMBER FORMATTING
// ---------------------------------------------------------------------------
const fmt = {
  usd: (v, compact = false) => {
    const n = Number(v) || 0;
    if (compact && Math.abs(n) >= 1_000_000)
      return '$' + (n / 1_000_000).toFixed(1) + 'M';
    if (compact && Math.abs(n) >= 1_000)
      return '$' + (n / 1_000).toFixed(0) + 'K';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
  },
  num: (v) => new Intl.NumberFormat('en-US').format(Number(v) || 0),
  pct: (v) => ((Number(v) || 0) * 100).toFixed(1) + '%',
  variance: (v) => {
    const n = Number(v) || 0;
    const s = fmt.usd(Math.abs(n), true);
    if (n > 500)  return `<span class="var-over">+${s}</span>`;
    if (n < -500) return `<span class="var-under">−${s}</span>`;
    return `<span class="var-neutral">${fmt.usd(n, true)}</span>`;
  },
};

// ---------------------------------------------------------------------------
// 2. BADGE HELPERS
// ---------------------------------------------------------------------------
const badge = {
  risk: (cls, label) =>
    `<span class="risk-badge ${cls}">${label}</span>`,

  complexity: (cx) => {
    const c = (cx || '').toUpperCase();
    const map = { SIMPLE: 'simple', MEDIUM: 'medium', HEAVY: 'heavy', HERO: 'heavy', HIGH: 'heavy' };
    const k = map[c] || 'simple';
    return `<span class="cx-pill ${k}">${cx || '—'}</span>`;
  },

  shotType: (t) => {
    const label = t || '—';
    const known = ['CG','Comp','Roto','Paint','Grade','Crowd','Extension','Creature','FX','Title'];
    const match = known.find(k => k.toLowerCase() === label.toLowerCase()) || '';
    return `<span class="type-pill ${match}">${label}</span>`;
  },

  assetType: (t) => {
    const label = (t || '—').toUpperCase();
    return `<span class="asset-pill ${label}">${t || '—'}</span>`;
  },

  invoice: (status) => {
    const s = (status || '').toUpperCase();
    return `<span class="inv-badge ${s}">${status || '—'}</span>`;
  },

  flag: (label, active) =>
    `<span class="flag-icon ${active ? 'active' : ''}">${label}</span>`,
};

// ---------------------------------------------------------------------------
// 3. VARIANCE BAR
// ---------------------------------------------------------------------------
function varBar(est, efc) {
  const diff = (efc || 0) - (est || 0);
  const pct = est ? Math.min(Math.abs(diff) / est, 1) * 100 : 0;
  const cls = diff > 500 ? 'over' : diff < -500 ? 'under' : 'watch';
  return `
    <div class="var-bar-wrap">
      <div class="var-bar-track">
        <div class="var-bar-fill ${cls}" style="width:${pct.toFixed(1)}%"></div>
      </div>
      <span class="text-small text-muted">${pct.toFixed(0)}%</span>
    </div>`;
}

// ---------------------------------------------------------------------------
// 4. BUDGET PROGRESS BAR
// ---------------------------------------------------------------------------
function budgetBar(paid, pending, total) {
  const t = total || 1;
  const paidPct    = Math.min(paid    / t, 1) * 100;
  const pendingPct = Math.min(pending / t, 1) * 100;
  return `
    <div class="budget-bar-wrap">
      <div class="budget-bar-track">
        <div class="budget-bar-paid"    style="width:${paidPct.toFixed(1)}%"></div>
        <div class="budget-bar-pending" style="width:${pendingPct.toFixed(1)}%"></div>
      </div>
      <div class="budget-bar-labels">
        <span>Paid ${fmt.usd(paid, true)}</span>
        <span>${fmt.usd(total, true)} total</span>
      </div>
    </div>`;
}

// ---------------------------------------------------------------------------
// 5. TOAST NOTIFICATIONS
// ---------------------------------------------------------------------------
(function () {
  const container = document.createElement('div');
  container.id = 'toast-container';
  document.body.appendChild(container);

  window.toast = function (msg, type = 'info', duration = 3000) {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'toast-out 0.25s ease forwards';
      el.addEventListener('animationend', () => el.remove());
    }, duration);
  };
})();

// ---------------------------------------------------------------------------
// 6. LLM STREAMING HELPER
// ---------------------------------------------------------------------------
window.llmStream = async function ({ task, context, targetEl, onDone }) {
  if (!targetEl) return;
  targetEl.innerHTML = '<span class="llm-spinner"><span class="llm-dot"></span><span class="llm-dot"></span><span class="llm-dot"></span> generating...</span>';

  const resp = await fetch('/api/llm/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, context }),
  });

  if (!resp.ok) {
    targetEl.textContent = '[LLM error]';
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let text = '';
  targetEl.innerHTML = '<span class="llm-stream-text"></span>';
  const span = targetEl.querySelector('.llm-stream-text');

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n');
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const body = line.slice(6).trim();
      if (body === '[DONE]') { span.classList.remove('llm-stream-text'); break; }
      try {
        const d = JSON.parse(body);
        if (d.t) { text += d.t; span.textContent = text; }
      } catch {}
    }
  }

  if (onDone) onDone(text);
};

// ---------------------------------------------------------------------------
// 7. TABLE SORT
// ---------------------------------------------------------------------------
window.makeTableSortable = function (tableEl) {
  const ths = tableEl.querySelectorAll('thead th:not(.no-sort)');
  ths.forEach((th, colIdx) => {
    th.addEventListener('click', () => {
      const asc = !th.classList.contains('sort-asc');
      ths.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(asc ? 'sort-asc' : 'sort-desc');

      const tbody = tableEl.querySelector('tbody');
      const rows  = Array.from(tbody.querySelectorAll('tr:not(.row-totals)'));
      rows.sort((a, b) => {
        const av = a.cells[colIdx]?.dataset.val ?? a.cells[colIdx]?.textContent ?? '';
        const bv = b.cells[colIdx]?.dataset.val ?? b.cells[colIdx]?.textContent ?? '';
        const an = parseFloat(av.replace(/[$,]/g, '')), bn = parseFloat(bv.replace(/[$,]/g, ''));
        if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
        return asc ? av.localeCompare(bv) : bv.localeCompare(av);
      });
      rows.forEach(r => tbody.appendChild(r));
      // Re-append totals row at bottom
      const totals = tbody.querySelector('.row-totals');
      if (totals) tbody.appendChild(totals);
    });
  });
};

// ---------------------------------------------------------------------------
// 8. GLOBAL SEARCH  (nav bar)
// ---------------------------------------------------------------------------
(function () {
  const input = document.querySelector('.nav-search');
  if (!input) return;

  const dropdown = document.createElement('div');
  dropdown.className = 'search-results';
  document.body.appendChild(dropdown);

  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { dropdown.classList.remove('open'); return; }
    timer = setTimeout(() => doSearch(q), 250);
  });

  input.addEventListener('blur', () => setTimeout(() => dropdown.classList.remove('open'), 180));

  async function doSearch(q) {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) return;
    const data = await res.json();
    renderResults(data);
  }

  function renderResults({ shots, assets, notes }) {
    let html = '';
    if (shots.length) {
      html += `<div class="sr-section"><div class="sr-label">Shots (${shots.length})</div>`;
      shots.slice(0, 6).forEach(s => {
        html += `<div class="sr-item" onclick="location.href='/ep/${s.ep}'" >
          <span class="sr-ep">EP${s.ep}</span>
          <span class="truncate">${s.location || ''} — ${s.vfx_desc || s.script_desc || ''}</span>
        </div>`;
      });
      html += '</div>';
    }
    if (assets.length) {
      html += `<div class="sr-section"><div class="sr-label">Assets (${assets.length})</div>`;
      assets.slice(0, 4).forEach(a => {
        html += `<div class="sr-item" onclick="location.href='/assets'">
          <span class="sr-ep">EP${a.ep}</span>
          <span class="truncate">${a.asset_name || ''} — ${a.asset_type || ''}</span>
        </div>`;
      });
      html += '</div>';
    }
    if (!shots.length && !assets.length && !notes.length) {
      html = '<div class="sr-section"><div class="sr-label">No results</div></div>';
    }
    dropdown.innerHTML = html;
    dropdown.classList.add('open');
  }
})();

// ---------------------------------------------------------------------------
// 9. SET ACTIVE NAV LINK
// ---------------------------------------------------------------------------
(function () {
  const path = location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === path || path.startsWith(a.getAttribute('href') + '/'))
      a.classList.add('active');
  });
})();

// ---------------------------------------------------------------------------
// 10. MODAL HELPERS
// ---------------------------------------------------------------------------
window.openModal = function (id) {
  document.getElementById(id)?.classList.add('open');
};
window.closeModal = function (id) {
  document.getElementById(id)?.classList.remove('open');
};
// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});
// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
});
