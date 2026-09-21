"""routes/settings_bp.py — Settings, Slack config, and LLM endpoints Blueprint."""
import json
from flask import Blueprint, render_template, request, jsonify

import core
import llm as llm_module
from services.llm_helpers import stream_llm, complete_llm, complete_json

bp = Blueprint('settings_bp', __name__)


# ── Settings page ─────────────────────────────────────────────────────────────

@bp.route('/settings')
def settings_page():
    return render_template('settings.html')


# ── Slack config ──────────────────────────────────────────────────────────────

@bp.route('/api/settings/slack', methods=['GET'])
def slack_config_get():
    cfg = core._load_slack_config()
    url = cfg.get('webhook_url', '')
    safe = url[:30] + '\u2026' if len(url) > 30 else url
    return jsonify({'webhook_url': safe, 'configured': bool(url)})


@bp.route('/api/settings/slack', methods=['PUT'])
def slack_config_put():
    from flask import current_app
    d = request.json or {}
    cfg = {'webhook_url': d.get('webhook_url', '').strip()}
    core._save_slack_config(cfg)
    current_app.config['SLACK_WEBHOOK'] = cfg['webhook_url']
    return jsonify({'status': 'ok'})


# ── LLM config ────────────────────────────────────────────────────────────────

@bp.route('/api/llm/config', methods=['GET'])
def llm_config_get():
    cfg = llm_module.load_config(core.BASE_DIR)
    safe = dict(cfg)
    for k in ('claude_api_key', 'openai_api_key'):
        v = safe.get(k, '')
        safe[k] = v[:8] + '\u2026' if len(v) > 8 else v
    return jsonify(safe)


@bp.route('/api/llm/config', methods=['PUT'])
def llm_config_put():
    d = request.json or {}
    cfg = llm_module.load_config(core.BASE_DIR)
    allowed = ['provider', 'ollama_url', 'ollama_model', 'claude_api_key', 'claude_model',
               'openai_api_key', 'openai_model', 'openai_base_url', 'max_tokens', 'temperature']
    for k in allowed:
        if k in d:
            cfg[k] = d[k]
    llm_module.save_config(core.BASE_DIR, cfg)
    core.reset_llm_client()
    return jsonify({'status': 'ok'})


@bp.route('/api/llm/status', methods=['GET', 'POST'])
def llm_status():
    if request.method == 'POST':
        cfg = request.json or {}
    else:
        cfg = llm_module.load_config(core.BASE_DIR)
    return jsonify(llm_module.test_connection(cfg))


# ── Context enrichment for LLM tasks ─────────────────────────────────────────

def _enrich_context(task: str, ctx: dict) -> dict:
    """
    Inject DB-sourced data into LLM context for tasks that benefit from actuals.

    cost_est      → project shot actuals (type/complexity/vendor averages)
    cost_est_v2   → actuals + invoice payment history + bid history
    vendor_suggest_v2 → vendor capacity, tax regions, payment performance
    """
    conn = core.get_db()
    if not conn:
        return ctx

    if task in ('cost_est', 'cost_est_v2'):
        actuals = core.get_cost_actuals(
            conn,
            shot_type=ctx.get('shot_type') or None,
            complexity=ctx.get('complexity') or None,
            award_vendor=ctx.get('award_vendor') or None,
        )
        enriched = {**ctx, 'actuals_context': actuals}

        if task == 'cost_est_v2':
            # Add invoice payment history for this vendor
            vendor = ctx.get('award_vendor') or ctx.get('vendor') or ''
            inv_history = ''
            if vendor:
                inv_rows = conn.execute(
                    """SELECT episode, amount, status
                       FROM invoice_log
                       WHERE UPPER(vendor)=UPPER(?)
                       ORDER BY created_at DESC LIMIT 10""",
                    (vendor,)
                ).fetchall()
                if inv_rows:
                    lines = [
                        f"  EP{r['episode']} ${r['amount']:,.0f} [{r['status']}]"
                        for r in inv_rows
                    ]
                    inv_history = 'Recent invoice history for ' + vendor + ':\n' + '\n'.join(lines)
            enriched['invoice_history'] = inv_history

            # Add bid range context
            stype = ctx.get('shot_type') or ''
            bid_context = ''
            if stype:
                bid_rows = conn.execute(
                    """SELECT vendor_bids FROM bid_compare
                       WHERE UPPER(shot_type)=UPPER(?) AND novfx=0 LIMIT 20""",
                    (stype,)
                ).fetchall()
                all_bids = []
                for r in bid_rows:
                    try:
                        bids = json.loads(r['vendor_bids'] or '{}')
                        all_bids.extend(float(v) for v in bids.values() if v)
                    except Exception:
                        pass
                if len(all_bids) >= 2:
                    bid_context = (
                        f"Market bid range for {stype}: "
                        f"min=${min(all_bids):,.0f}, avg=${sum(all_bids)/len(all_bids):,.0f}, "
                        f"max=${max(all_bids):,.0f} ({len(all_bids)} bids)"
                    )
            enriched['bid_context'] = bid_context

        return enriched

    if task == 'vendor_suggest_v2':
        # Vendor capacity + tax rate + payment performance
        from services.vendors_svc import get_vendor_loads, get_vendor_perf_scores
        loads   = get_vendor_loads(conn)
        perf    = get_vendor_perf_scores(conn)
        tax_rows = conn.execute(
            'SELECT region, rate FROM tax_regions ORDER BY region'
        ).fetchall() if _table_exists(conn, 'tax_regions') else []

        vendor_detail = []
        for name, load in loads.items():
            util  = load.get('utilization')
            cap_s = f"{util*100:.0f}% utilized" if util is not None else 'no cap data'
            score = perf.get(name.upper(), {})
            perf_s = f"score={score.get('score',0):.2f}" if score else 'no perf data'
            tax_r = _find_tax_rate(tax_rows, name)
            tax_s = f"tax={tax_r:.1f}%" if tax_r is not None else ''
            vendor_detail.append(f"  {name}: {cap_s}, {perf_s}{', '+tax_s if tax_s else ''}")

        return {**ctx, 'vendor_list': '\n'.join(vendor_detail) or '  No vendor data'}

    return ctx


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _find_tax_rate(tax_rows, vendor_name: str):
    """Try to match vendor name to a tax region (loose match on region string)."""
    vendor_upper = vendor_name.upper()
    for r in tax_rows:
        if r['region'].upper() in vendor_upper or vendor_upper in r['region'].upper():
            return float(r['rate']) * 100
    return None


# ── Generic stream + complete endpoints ──────────────────────────────────────

@bp.route('/api/llm/stream', methods=['POST'])
def llm_stream_route():
    """Stream LLM output for a given task + context."""
    d      = request.json or {}
    task   = d.get('task', '')
    ctx    = _enrich_context(task, d.get('context', {}))
    prompt = llm_module.build_prompt(task, ctx)
    if not prompt:
        return jsonify({'error': f'Unknown task: {task}'}), 400

    client = core.get_llm_client()
    return stream_llm(prompt, client, cache_task=task, cache_ctx=ctx)


@bp.route('/api/llm/complete', methods=['POST'])
def llm_complete_route():
    """Non-streaming LLM completion. Checks cache; stores result after fresh call."""
    d      = request.json or {}
    task   = d.get('task', '')
    ctx    = _enrich_context(task, d.get('context', {}))
    prompt = llm_module.build_prompt(task, ctx)
    if not prompt:
        return jsonify({'error': f'Unknown task: {task}'}), 400

    client   = core.get_llm_client()
    full_txt = complete_llm(prompt, client, cache_task=task, cache_ctx=ctx)
    return jsonify({'result': full_txt, 'task': task})


# ── Project settings ──────────────────────────────────────────────────────────

@bp.route('/api/project_settings', methods=['GET'])
def project_settings_get():
    conn = core.get_db()
    if not conn: return jsonify({})
    rows = conn.execute('SELECT key, value FROM project_settings').fetchall()
    conn.close()
    return jsonify({r['key']: r['value'] for r in rows})


@bp.route('/api/project_settings', methods=['PUT'])
def project_settings_put():
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    updates = request.json or {}
    for key, value in updates.items():
        conn.execute(
            'INSERT INTO project_settings (key, value) VALUES (?,?) '
            'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            (key, str(value))
        )
    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'status': 'ok', 'updated': list(updates.keys())})


# ── Cost actuals (used by AI panel UI) ───────────────────────────────────────

@bp.route('/api/cost_actuals')
def cost_actuals():
    """Return historical cost stats for a shot_type/complexity/vendor combination."""
    conn = core.get_db()
    if not conn: return jsonify({'actuals': '', 'buckets': []})
    shot_type    = request.args.get('shot_type')    or None
    complexity   = request.args.get('complexity')   or None
    award_vendor = request.args.get('award_vendor') or None
    actuals_text = core.get_cost_actuals(conn, shot_type, complexity, award_vendor)

    buckets = []
    for where, params, label in [
        ('UPPER(shot_type)=UPPER(?)',
         (shot_type,), f'{shot_type}'),
        ('UPPER(shot_type)=UPPER(?) AND UPPER(complexity)=UPPER(?)',
         (shot_type, complexity), f'{shot_type}/{complexity}'),
        ('UPPER(shot_type)=UPPER(?) AND UPPER(award_vendor)=UPPER(?)',
         (shot_type, award_vendor), f'{shot_type} @ {award_vendor}'),
    ]:
        if not all(params):
            continue
        try:
            r = conn.execute(f'''
                SELECT COUNT(*) AS n,
                       AVG(CASE WHEN efc>0 THEN efc ELSE cost_est END) AS avg_cost,
                       MIN(CASE WHEN efc>0 THEN efc ELSE cost_est END) AS min_cost,
                       MAX(CASE WHEN efc>0 THEN efc ELSE cost_est END) AS max_cost
                FROM shots WHERE omit=0 AND (efc>0 OR cost_est>0) AND {where}
            ''', params).fetchone()
            if r and r['n'] and r['n'] >= 1:
                buckets.append({
                    'label':    label,
                    'n':        r['n'],
                    'avg_cost': round(r['avg_cost'] or 0),
                    'min_cost': round(r['min_cost'] or 0),
                    'max_cost': round(r['max_cost'] or 0),
                })
        except Exception:
            pass

    conn.close()
    return jsonify({'actuals': actuals_text, 'buckets': buckets})


# ── Batch: auto-tag complexity ────────────────────────────────────────────────

@bp.route('/api/llm/batch/complexity/<int:ep>', methods=['POST'])
def batch_complexity(ep):
    """Auto-tag complexity for all untagged shots in an episode."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    rows = conn.execute(
        "SELECT id, scene_code, vfx_desc, shot_type FROM shots "
        "WHERE ep=? AND omit=0 AND (complexity IS NULL OR complexity='')",
        (ep,)
    ).fetchall()

    if not rows:
        conn.close()
        return jsonify({'tagged': 0, 'message': 'No untagged shots found'})

    shots_list = '\n'.join(
        f"{r['id']} | SC{r['scene_code']} | {r['shot_type'] or ''} | {(r['vfx_desc'] or '')[:80]}"
        for r in rows
    )
    cache_ctx = {'ep': ep, 'shots_list': shots_list[:256]}  # abbreviated for cache key
    prompt    = llm_module.build_prompt('complexity_batch', {'shots_list': shots_list})
    client    = core.get_llm_client()
    full_txt  = complete_llm(prompt, client, cache_task='complexity_batch', cache_ctx=cache_ctx)

    from llm.parsers import parse_id_value_lines
    parsed = parse_id_value_lines(full_txt)
    valid  = {'SIMPLE', 'MEDIUM', 'HEAVY'}
    tagged = 0
    errors = []
    for shot_id_str, cmp in parsed.items():
        try:
            shot_id = int(shot_id_str)
            cmp_up  = cmp.upper()
            if cmp_up not in valid:
                continue
            conn.execute('UPDATE shots SET complexity=? WHERE id=?', (cmp_up.capitalize(), shot_id))
            tagged += 1
        except (ValueError, Exception) as e:
            errors.append(str(e))

    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'tagged': tagged, 'total': len(rows), 'errors': errors})


# ── Batch: fill missing VFX descriptions ─────────────────────────────────────

@bp.route('/api/llm/batch/vfx_desc/<int:ep>', methods=['POST'])
def batch_vfx_desc(ep):
    """Generate VFX descriptions for all shots missing them in an episode."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    rows = conn.execute(
        "SELECT id, scene_code, location, ext_int, asset, script_desc, shot_type "
        "FROM shots WHERE ep=? AND omit=0 AND (vfx_desc IS NULL OR vfx_desc='')",
        (ep,)
    ).fetchall()

    if not rows:
        conn.close()
        return jsonify({'filled': 0, 'message': 'No shots missing VFX descriptions'})

    shots_list = '\n'.join(
        f"{r['id']} | SC{r['scene_code']} | {r['ext_int'] or ''} {r['location'] or ''} | "
        f"{r['shot_type'] or ''} | {(r['script_desc'] or '')[:80]}"
        for r in rows
    )
    cache_ctx = {'ep': ep, 'shots_list': shots_list[:256]}
    prompt    = llm_module.build_prompt('batch_vfx_desc', {'shots_list': shots_list})
    client    = core.get_llm_client()
    full_txt  = complete_llm(prompt, client, cache_task='batch_vfx_desc', cache_ctx=cache_ctx)

    from llm.parsers import parse_id_value_lines
    parsed = parse_id_value_lines(full_txt)
    filled = 0
    for shot_id_str, desc in parsed.items():
        try:
            shot_id = int(shot_id_str)
            if desc:
                conn.execute('UPDATE shots SET vfx_desc=? WHERE id=?', (desc, shot_id))
                filled += 1
        except (ValueError, Exception):
            continue

    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'filled': filled, 'total': len(rows)})


# ── Vendor suggestion ─────────────────────────────────────────────────────────

@bp.route('/api/llm/vendor_suggest', methods=['POST'])
def vendor_suggest():
    """
    Recommend a vendor for a given shot.
    Uses vendor_suggest_v2 (capacity-aware) when capacity data exists,
    falls back to vendor_suggest otherwise.
    """
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json or {}

    # Determine which prompt to use: v2 if capacity data available
    from services.vendors_svc import get_vendor_loads
    loads = get_vendor_loads(conn)
    task  = 'vendor_suggest_v2' if loads else 'vendor_suggest'

    ctx   = _enrich_context(task, d)
    # Ensure vendor_list is populated for base vendor_suggest fallback
    if 'vendor_list' not in ctx:
        vrows = conn.execute('''
            SELECT award_vendor, COUNT(*) as shots,
                   SUM(COALESCE(cost_est,0)) as total_est,
                   SUM(COALESCE(efc,0)) as total_efc
            FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor != ''
            GROUP BY award_vendor ORDER BY total_efc DESC LIMIT 10
        ''').fetchall()
        ctx['vendor_list'] = '\n'.join(
            f"  {r['award_vendor']}: {r['shots']} shots, EST ${r['total_est']:,.0f}, EFC ${r['total_efc']:,.0f}"
            for r in vrows
        ) or '  No vendor history available'
    conn.close()

    prompt = llm_module.build_prompt(task, ctx)
    if not prompt:
        prompt = llm_module.build_prompt('vendor_suggest', ctx)

    client = core.get_llm_client()
    result = complete_json(prompt, client, cache_task=task, cache_ctx={
        'shot_type': d.get('shot_type', ''),
        'complexity': d.get('complexity', ''),
        'cost_est': str(d.get('cost_est', '')),
    })
    if result is None:
        result = {'vendor': '', 'reason': 'Could not parse LLM response'}
    return jsonify(result)


# ── Budget gap analysis (streaming) ──────────────────────────────────────────

@bp.route('/api/llm/budget_gap/<int:ep>', methods=['POST'])
def budget_gap_analysis(ep):
    """Identify cost-reduction opportunities for an episode — streamed."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    agg = conn.execute('''
        SELECT COUNT(CASE WHEN omit=0 THEN 1 END) AS total_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS total_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS total_efc
        FROM shots WHERE ep=?''', (ep,)).fetchone()

    top_shots = conn.execute('''
        SELECT scene_code, shot_type, complexity, award_vendor, cost_est, efc,
               (efc - cost_est) AS overrun
        FROM shots WHERE ep=? AND omit=0 AND efc > cost_est
        ORDER BY overrun DESC LIMIT 6''', (ep,)).fetchall()

    type_rows = conn.execute('''
        SELECT shot_type, COUNT(*) AS cnt,
               SUM(COALESCE(cost_est,0)) AS total_est
        FROM shots WHERE ep=? AND omit=0 AND shot_type IS NOT NULL AND shot_type != ''
        GROUP BY shot_type ORDER BY total_est DESC''', (ep,)).fetchall()
    conn.close()

    total_est = agg['total_est'] or 0
    total_efc = agg['total_efc'] or 0
    ctx = {
        'ep':           ep,
        'total_shots':  agg['total_shots'] or 0,
        'total_est':    f'{total_est:,.0f}',
        'total_efc':    f'{total_efc:,.0f}',
        'variance':     f'{total_efc - total_est:,.0f}',
        'top_shots':    '\n'.join(
            f"  SC{r['scene_code']} {r['shot_type']} {r['complexity']} "
            f"vendor={r['award_vendor'] or '—'} EST=${r['cost_est']:,.0f} EFC=${r['efc']:,.0f} +${r['overrun']:,.0f}"
            for r in top_shots
        ) or '  No over-budget shots',
        'type_breakdown': '\n'.join(
            f"  {r['shot_type']}: {r['cnt']} shots, ${r['total_est']:,.0f}"
            for r in type_rows
        ) or '  No type data',
    }
    prompt = llm_module.build_prompt('budget_gap_analysis', ctx)
    if not prompt:
        return jsonify({'error': 'prompt build failed'}), 400

    client = core.get_llm_client()
    return stream_llm(prompt, client, cache_task='budget_gap_analysis',
                      cache_ctx={'ep': ep, 'variance': ctx['variance']})


# ── Season risk memo (streaming) ──────────────────────────────────────────────

@bp.route('/api/llm/season_risk', methods=['POST'])
def season_risk():
    """Executive season-level risk memo — streamed."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    agg = conn.execute('''
        SELECT COUNT(CASE WHEN omit=0 THEN 1 END) AS total_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS total_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS total_efc
        FROM shots''').fetchone()

    ep_rows = []
    for ep in core.get_episodes():
        r    = conn.execute('''
            SELECT SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS est,
                   SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS efc
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        meta = conn.execute('SELECT status FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        ep_rows.append(
            f"  EP{ep} [{meta['status'] if meta else ''}]: "
            f"EST ${r['est'] or 0:,.0f} / EFC ${r['efc'] or 0:,.0f} "
            f"var ${(r['efc'] or 0)-(r['est'] or 0):+,.0f}"
        )

    vrows = conn.execute('''
        SELECT award_vendor, COUNT(*) as shots,
               SUM(COALESCE(efc,0)) as total_efc
        FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor != ''
        GROUP BY award_vendor ORDER BY total_efc DESC LIMIT 6''').fetchall()
    conn.close()

    total_est = agg['total_est'] or 0
    total_efc = agg['total_efc'] or 0
    ctx = {
        'total_shots':      agg['total_shots'] or 0,
        'total_est':        f'{total_est:,.0f}',
        'total_efc':        f'{total_efc:,.0f}',
        'variance':         f'{total_efc - total_est:+,.0f}',
        'ep_breakdown':     '\n'.join(ep_rows) or '  No episode data',
        'vendor_breakdown': '\n'.join(
            f"  {r['award_vendor']}: {r['shots']} shots, EFC ${r['total_efc']:,.0f}"
            for r in vrows
        ) or '  No vendor data',
    }
    prompt = llm_module.build_prompt('season_risk', ctx)
    client = core.get_llm_client()
    return stream_llm(prompt, client, cache_task='season_risk',
                      cache_ctx={'total_efc': ctx['total_efc'], 'variance': ctx['variance']})


# ── Invoice anomaly check ─────────────────────────────────────────────────────

@bp.route('/api/llm/invoice_check', methods=['POST'])
def invoice_check():
    """Check an invoice for anomalies vs vendor award — returns JSON with parse_with_retry."""
    d    = request.json or {}
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    vendor  = d.get('vendor', '')
    ep      = d.get('ep')
    tracker = conn.execute(
        'SELECT tot_award, paid, remaining FROM vendor_tracker '
        'WHERE UPPER(vendor)=UPPER(?) AND ep=?', (vendor, ep)
    ).fetchone() if vendor and ep else None
    conn.close()

    ctx = {
        'vendor':    vendor,
        'ep':        ep or '',
        'tot_award': f"{tracker['tot_award'] or 0:,.0f}" if tracker else '0',
        'paid':      f"{tracker['paid'] or 0:,.0f}"      if tracker else '0',
        'remaining': f"{tracker['remaining'] or 0:,.0f}" if tracker else '0',
        'amount':    f"{d.get('amount', 0):,.0f}",
        'inv_num':   d.get('inv_num', ''),
        'inv_date':  d.get('inv_date', ''),
    }
    cache_ctx = {'vendor': vendor, 'ep': str(ep), 'amount': str(d.get('amount', 0))}
    prompt    = llm_module.build_prompt('invoice_check', ctx)
    client    = core.get_llm_client()
    result    = complete_json(prompt, client, cache_task='invoice_check', cache_ctx=cache_ctx)

    if result is None:
        result = {'status': 'warning', 'message': 'Could not parse LLM response'}
    return jsonify(result)


# ── LLM usage stats ───────────────────────────────────────────────────────────

@bp.route('/api/llm_usage', methods=['GET'])
def llm_usage():
    """Return LLM call statistics for the settings page."""
    from llm.cache import get_usage_stats
    import services.db as sdb
    stats = get_usage_stats(sdb.PROJECTS_DB)
    return jsonify(stats)
