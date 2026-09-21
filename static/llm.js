/**
 * llm.js — shared LLM helper for VFX Budget System
 * Included in base.html — available on every page.
 */

/**
 * Stream an LLM response.
 * @param {string}   task     - task key (vfx_desc | shot_type | cost_est | ...)
 * @param {object}   context  - context dict passed to the prompt builder
 * @param {function} onChunk  - called with accumulated text on each chunk
 * @param {function} onDone   - called with final full text when stream ends
 * @param {function} onError  - called with error message string on failure
 */
async function llmStream(task, context, onChunk, onDone, onError) {
  let fullText = '';
  try {
    const res = await fetch('/api/llm/stream', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({task, context}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      onError(err.error || `HTTP ${res.status}`);
      return;
    }
    const reader = res.body.getReader();
    const dec    = new TextDecoder();
    let   buf    = '';

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      const lines = buf.split('\n');
      buf = lines.pop();                        // keep incomplete line in buffer
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') { onDone(fullText); return; }
        try {
          const parsed = JSON.parse(payload);
          if (parsed.error) { onError(parsed.error); return; }
          if (parsed.t)     { fullText += parsed.t; onChunk(fullText); }
        } catch (_) { /* skip malformed lines */ }
      }
    }
    onDone(fullText);
  } catch (e) {
    onError(e.message);
  }
}

/**
 * Blocking completion — returns {result, task} or {error}.
 */
async function llmComplete(task, context) {
  try {
    const res = await fetch('/api/llm/complete', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({task, context}),
    });
    return await res.json();
  } catch (e) {
    return {error: e.message};
  }
}

/**
 * Safely parse a JSON block from a freeform LLM response.
 * Returns null if no valid JSON object is found.
 */
function llmParseJSON(text) {
  if (!text) return null;
  const m = text.match(/\{[\s\S]*\}/);
  if (!m) return null;
  try { return JSON.parse(m[0]); } catch (_) { return null; }
}

/**
 * Generic streaming UI helper.
 * Manages a [Generate] button, a streaming preview div, and [Accept]/[Discard] buttons.
 *
 * @param {object} opts
 *   task, context, genBtn, previewEl, actionsEl,
 *   onAccept(fullText),   // called when user clicks Accept
 *   postProcess(text)     // optional — transforms text before displaying
 */
function llmUI(opts) {
  const {task, context, genBtn, previewEl, actionsEl, onAccept, postProcess} = opts;

  genBtn.disabled    = true;
  genBtn.textContent = 'Generating…';
  previewEl.style.display  = 'block';
  previewEl.style.color    = '#d0d8f0';
  previewEl.textContent    = '';
  actionsEl.style.display  = 'none';

  let lastText = '';

  llmStream(
    task, context,
    // onChunk
    (text) => {
      lastText = postProcess ? postProcess(text) : text;
      previewEl.textContent = lastText;
    },
    // onDone
    (fullText) => {
      lastText = postProcess ? postProcess(fullText) : fullText;
      previewEl.textContent = lastText;
      actionsEl.style.display = 'flex';
      genBtn.disabled    = false;
      genBtn.innerHTML   = '<i class="bi bi-arrow-clockwise me-1"></i>Regenerate';
      // wire Accept button
      const acceptBtn = actionsEl.querySelector('.ai-accept');
      if (acceptBtn) acceptBtn.onclick = () => onAccept(lastText);
      // wire Discard button
      const discardBtn = actionsEl.querySelector('.ai-discard');
      if (discardBtn) discardBtn.onclick = () => {
        previewEl.style.display = 'none';
        actionsEl.style.display = 'none';
        genBtn.innerHTML = '✨ Generate';
      };
    },
    // onError
    (err) => {
      previewEl.style.color = '#e05252';
      previewEl.textContent = `Error: ${err}`;
      genBtn.disabled    = false;
      genBtn.innerHTML   = '✨ Retry';
    }
  );
}
