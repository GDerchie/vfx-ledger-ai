/**
 * VFX Budget System v04 — Shared Utilities
 * utils.js — loaded globally via base.html
 *
 * Provides: fmt, apiPut, apiDelete, showSaveStatus,
 *           initUnsavedGuard, initSaveIndicator, TABULATOR_PERF
 */

// ── Currency formatter ─────────────────────────────────────────────────────
window.fmt = function(v) {
  const n = parseFloat(v);
  if (isNaN(n) || n === 0) return '';
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
};

// ── API helpers ────────────────────────────────────────────────────────────
window.apiPut = function(url, data) {
  return fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
};

window.apiPost = function(url, data) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
};

window.apiDelete = function(url) {
  return fetch(url, { method: 'DELETE' });
};

// ── Auto-save status indicator ─────────────────────────────────────────────
/**
 * initSaveIndicator(containerId)
 * Injects a save-status badge into the element with the given ID.
 * Returns { saving(), saved(), error() } controller.
 *
 * Usage:
 *   const status = initSaveIndicator('my-table-panel');
 *   status.saving();
 *   await apiPut(...);
 *   status.saved();
 */
window.initSaveIndicator = function(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return { saving: () => {}, saved: () => {}, error: () => {} };

  const badge = document.createElement('span');
  badge.style.cssText = [
    'font-size:9px', 'font-weight:700', 'letter-spacing:.5px',
    'padding:2px 7px', 'border-radius:3px', 'transition:opacity .3s',
    'opacity:0', 'margin-left:8px', 'vertical-align:middle',
    'font-family:Helvetica,sans-serif',
  ].join(';');
  container.appendChild(badge);

  let _fadeTimer = null;

  function show(text, color, autofade) {
    clearTimeout(_fadeTimer);
    badge.textContent = text;
    badge.style.color = color;
    badge.style.background = color + '22';
    badge.style.border = '1px solid ' + color + '55';
    badge.style.opacity = '1';
    if (autofade) {
      _fadeTimer = setTimeout(() => { badge.style.opacity = '0'; }, 2000);
    }
  }

  return {
    saving: () => show('SAVING...', '#f0b429', false),
    saved:  () => show('SAVED',     '#52c46a', true),
    error:  () => show('ERROR',     '#e05252', false),
    clear:  () => { badge.style.opacity = '0'; },
  };
};

// ── Unsaved-changes guard ──────────────────────────────────────────────────
/**
 * initUnsavedGuard()
 * Returns { setPending(bool) }.
 * When pending=true and user tries to close/navigate, browser warns.
 *
 * Usage:
 *   const guard = initUnsavedGuard();
 *   // before save:
 *   guard.setPending(true);
 *   // after save response:
 *   guard.setPending(false);
 */
window.initUnsavedGuard = function() {
  let _pending = false;

  window.addEventListener('beforeunload', function(e) {
    if (_pending) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  return {
    setPending: function(v) { _pending = !!v; },
    isPending:  function()  { return _pending; },
  };
};

// ── Tabulator performance defaults ────────────────────────────────────────
/**
 * TABULATOR_PERF — spread into any Tabulator config to enable virtual DOM.
 *
 * Usage:
 *   new Tabulator('#my-table', {
 *     ...TABULATOR_PERF,
 *     data: rows,
 *     columns: cols,
 *     ...
 *   });
 */
window.TABULATOR_PERF = {
  renderVertical:       'virtual',
  renderVerticalBuffer: 600,
};

// ── Toast notification ────────────────────────────────────────────────────
/**
 * showToast(message, type)
 * type: 'success' | 'warning' | 'error' | 'info'
 */
window.showToast = function(message, type) {
  type = type || 'info';
  const colors = {
    success: { bg: '#1a3020', border: '#52c46a', text: '#52c46a' },
    warning: { bg: '#2a2010', border: '#f0b429', text: '#f0b429' },
    error:   { bg: '#2a1010', border: '#e05252', text: '#e05252' },
    info:    { bg: '#101828', border: '#4a9cf0', text: '#4a9cf0' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.style.cssText = [
    'position:fixed', 'bottom:24px', 'right:24px', 'z-index:9999',
    `background:${c.bg}`, `border:1px solid ${c.border}`,
    `color:${c.text}`, 'font-size:11px', 'font-family:Helvetica,sans-serif',
    'padding:8px 14px', 'border-radius:5px', 'max-width:280px',
    'box-shadow:0 4px 16px rgba(0,0,0,.5)',
    'transition:opacity .3s', 'opacity:0',
  ].join(';');
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => { toast.style.opacity = '1'; });
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 320);
  }, 3000);
};

// ── Badge + date helpers (Opt #6) ─────────────────────────────────────────
window.badge = function(text, cls) {
  return `<span class="status-badge status-${cls||'default'}">${text}</span>`;
};

window.dateStr = function(d) {
  if (!d) return '';
  try {
    return new Date(d).toLocaleDateString('en-US', {year:'numeric', month:'short', day:'2-digit'});
  } catch(e) { return String(d); }
};

// ── Duplicate value checker ────────────────────────────────────────────────
/**
 * checkDuplicate(table, field, value, currentRowId)
 * Returns true if another row in the table has the same value for field.
 */
window.checkDuplicate = function(table, field, value, currentRowId) {
  if (!value) return false;
  const rows = table.getData();
  return rows.some(r => r.id !== currentRowId &&
    String(r[field] || '').trim().toLowerCase() === String(value).trim().toLowerCase());
};
