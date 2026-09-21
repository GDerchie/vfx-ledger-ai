"""routes/dashboard.py — Season Dashboard Blueprint."""
from flask import Blueprint, render_template, jsonify, session
import core

bp = Blueprint('dashboard', __name__)


@bp.route('/dashboard')
def dashboard_page():
    r = core.require_project()
    if r: return r
    return render_template('dashboard.html')


@bp.route('/api/dashboard/summary')
def dashboard_summary():
    conn = core.get_db()
    if not conn: return jsonify({})

    eps = core.get_episodes()
    proj_name   = session.get('project_name', '')
    proj_season = session.get('project_season', '')

    # Season-level aggregates
    agg = conn.execute('''
        SELECT
            COUNT(CASE WHEN omit=0 THEN 1 END)                              AS total_shots,
            COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END)              AS est_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END)   AS edit_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END)     AS shot_est,
            SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END)          AS shot_efc,
            COUNT(DISTINCT CASE WHEN omit=0 AND award_vendor IS NOT NULL
                  AND award_vendor != '' THEN award_vendor END)             AS vendor_count
        FROM shots
    ''').fetchone()

    asset_agg = conn.execute('''
        SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS asset_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS asset_efc,
               COUNT(CASE WHEN omit=0 THEN 1 END) AS asset_count
        FROM assets
    ''').fetchone()

    shot_est  = agg['shot_est']  or 0
    shot_efc  = agg['shot_efc']  or 0
    asset_est = (asset_agg['asset_est'] or 0) if asset_agg else 0
    asset_efc = (asset_agg['asset_efc'] or 0) if asset_agg else 0
    total_est = shot_est + asset_est
    total_efc = shot_efc + asset_efc

    # Per-episode breakdown
    ep_rows = []
    for ep in eps:
        e_agg = conn.execute('''
            SELECT COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
                   SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS edit_shots,
                   SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS shot_est,
                   SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS shot_efc
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        e_meta = conn.execute('SELECT status, script_v, edit_v FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        e_aa = conn.execute('''
            SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS ae,
                   SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS af
            FROM assets WHERE ep=?''', (ep,)).fetchone()
        se = e_agg['shot_est'] or 0; sf = e_agg['shot_efc'] or 0
        ae = (e_aa['ae'] or 0) if e_aa else 0; af = (e_aa['af'] or 0) if e_aa else 0
        ep_rows.append({
            'ep': ep,
            'status':     e_meta['status']   if e_meta else '',
            'script_v':   e_meta['script_v'] if e_meta else '',
            'est_shots':  e_agg['est_shots'] or 0,
            'edit_shots': e_agg['edit_shots'] or 0,
            'est_budget': se + ae,
            'efc_budget': sf + af,
            'variance':   (sf + af) - (se + ae),
        })

    # Top vendors by EFC
    top_vendors = conn.execute('''
        SELECT award_vendor AS vendor,
               COUNT(*) AS shots,
               SUM(COALESCE(efc,0)) AS total_efc,
               SUM(COALESCE(cost_est,0)) AS total_est
        FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor != ''
        GROUP BY award_vendor ORDER BY total_efc DESC LIMIT 8
    ''').fetchall()

    # Shot type breakdown
    type_breakdown = conn.execute('''
        SELECT shot_type, COUNT(*) AS cnt,
               SUM(COALESCE(cost_est,0)) AS est
        FROM shots WHERE omit=0 AND shot_type IS NOT NULL AND shot_type != ''
        GROUP BY shot_type ORDER BY cnt DESC
    ''').fetchall()

    # Complexity breakdown
    complexity_breakdown = conn.execute('''
        SELECT complexity, COUNT(*) AS cnt
        FROM shots WHERE omit=0 AND complexity IS NOT NULL AND complexity != ''
        GROUP BY complexity ORDER BY cnt DESC
    ''').fetchall()

    # Recent audit entries
    recent_changes = conn.execute('''
        SELECT table_name, field, old_value, new_value, timestamp
        FROM change_log ORDER BY id DESC LIMIT 10
    ''').fetchall()

    conn.close()

    return jsonify({
        'project': {'name': proj_name, 'season': proj_season},
        'season': {
            'total_shots':   agg['total_shots']  or 0,
            'est_shots':     agg['est_shots']    or 0,
            'edit_shots':    agg['edit_shots']   or 0,
            'vendor_count':  agg['vendor_count'] or 0,
            'asset_count':   (asset_agg['asset_count'] or 0) if asset_agg else 0,
            'shot_est':      shot_est,
            'shot_efc':      shot_efc,
            'asset_est':     asset_est,
            'asset_efc':     asset_efc,
            'total_est':     total_est,
            'total_efc':     total_efc,
            'variance':      total_efc - total_est,
        },
        'episodes':     ep_rows,
        'top_vendors':  [dict(r) for r in top_vendors],
        'type_breakdown':       [dict(r) for r in type_breakdown],
        'complexity_breakdown': [dict(r) for r in complexity_breakdown],
        'recent_changes':       [dict(r) for r in recent_changes],
    })


@bp.route('/api/risk_forecast')
def risk_forecast():
    """Per-episode risk scores using the VFX Ledger formula:
    risk = capacity_risk*0.45 + complexity_risk*0.30 + confidence_risk*0.25
    """
    conn = core.get_db()
    if not conn: return jsonify([])
    eps = core.get_episodes()
    results = [core.compute_ep_risk(conn, ep) for ep in eps]
    conn.close()
    return jsonify(results)


@bp.route('/api/dashboard/burn')
def dashboard_burn():
    """EFC vs EST per EP — data for burn chart."""
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = []
    for ep in core.get_episodes():
        r = conn.execute('''
            SELECT SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS est,
                   SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS efc
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        aa = conn.execute('''
            SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS ae,
                   SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS af
            FROM assets WHERE ep=?''', (ep,)).fetchone()
        se = r['est'] or 0; sf = r['efc'] or 0
        ae = (aa['ae'] or 0) if aa else 0; af = (aa['af'] or 0) if aa else 0
        rows.append({'ep': ep, 'est': se + ae, 'efc': sf + af})
    conn.close()
    return jsonify(rows)


@bp.route('/api/dashboard/action_items')
def dashboard_action_items():
    """
    Return a list of items requiring producer attention.
    Each item: { type, severity, ep, message, link }
    severity: 'critical' | 'warning' | 'info'
    """
    conn = core.get_db()
    if not conn: return jsonify([])

    items = []

    # 1. Missing VFX descriptions
    missing_desc = conn.execute(
        "SELECT ep, COUNT(*) as n FROM shots "
        "WHERE omit=0 AND (vfx_desc IS NULL OR vfx_desc='') "
        "GROUP BY ep ORDER BY n DESC"
    ).fetchall()
    for r in missing_desc:
        items.append({
            'type': 'missing_vfx_desc', 'severity': 'warning',
            'ep': r['ep'],
            'message': f"EP{r['ep']}: {r['n']} shots missing VFX descriptions",
            'link': f'/ep/{r["ep"]}',
        })

    # 2. Missing cost estimates
    missing_cost = conn.execute(
        "SELECT ep, COUNT(*) as n FROM shots "
        "WHERE omit=0 AND (cost_est IS NULL OR cost_est=0) "
        "GROUP BY ep ORDER BY n DESC"
    ).fetchall()
    for r in missing_cost:
        items.append({
            'type': 'missing_cost', 'severity': 'warning',
            'ep': r['ep'],
            'message': f"EP{r['ep']}: {r['n']} shots without cost estimates",
            'link': f'/ep/{r["ep"]}',
        })

    # 3. High-variance EPs (EFC > EST by > 20%)
    eps = core.get_episodes()
    for ep in eps:
        r = conn.execute(
            "SELECT SUM(COALESCE(cost_est,0)) as est, SUM(COALESCE(efc,0)) as efc "
            "FROM shots WHERE ep=? AND omit=0", (ep,)
        ).fetchone()
        est = r['est'] or 0
        efc = r['efc'] or 0
        if est > 0 and efc > est * 1.20:
            pct = int((efc / est - 1) * 100)
            items.append({
                'type': 'high_variance', 'severity': 'critical',
                'ep': ep,
                'message': f"EP{ep}: EFC is {pct}% over estimate (${efc-est:,.0f} overrun)",
                'link': f'/ep/{ep}',
            })

    # 4. Vendors over capacity
    try:
        from services.vendors_svc import get_vendor_loads
        loads = get_vendor_loads(conn)
        for vendor, load in loads.items():
            if load.get('utilization') and load['utilization'] > 1.0:
                pct = int(load['utilization'] * 100)
                items.append({
                    'type': 'vendor_overload', 'severity': 'critical',
                    'ep': None,
                    'message': f"{vendor}: {pct}% capacity — risk of delivery delay",
                    'link': '/vendortracker',
                })
    except Exception:
        pass

    # 5. Invoices exceeding award
    try:
        over_invoiced = conn.execute(
            """SELECT vt.vendor, vt.ep, vt.tot_award,
                      COALESCE(SUM(il.amount),0) as total_invoiced
               FROM vendor_tracker vt
               LEFT JOIN invoice_log il
                 ON UPPER(il.vendor)=UPPER(vt.vendor) AND il.episode=vt.ep
               WHERE vt.tot_award > 0
               GROUP BY vt.vendor, vt.ep
               HAVING total_invoiced > vt.tot_award * 1.05"""
        ).fetchall()
        for r in over_invoiced:
            items.append({
                'type': 'over_invoiced', 'severity': 'critical',
                'ep': r['ep'],
                'message': (
                    f"{r['vendor']} EP{r['ep']}: invoiced ${r['total_invoiced']:,.0f} "
                    f"vs award ${r['tot_award']:,.0f} (+{int((r['total_invoiced']/r['tot_award']-1)*100)}%)"
                ),
                'link': '/invoicelog',
            })
    except Exception:
        pass

    conn.close()

    # Sort: critical first
    order = {'critical': 0, 'warning': 1, 'info': 2}
    items.sort(key=lambda x: order.get(x['severity'], 3))
    return jsonify(items)


@bp.route('/api/dashboard/predictive')
def dashboard_predictive():
    """
    Return season-level predictive EFC from delivery ratio model.
    Used to display predicted vs current EFC comparison on dashboard.
    """
    conn = core.get_db()
    if not conn: return jsonify({})
    try:
        from services.distribution import compute_predictive_efc
        _, summary = compute_predictive_efc(conn, ep=None)

        # Per-episode predicted totals
        all_shots, _ = compute_predictive_efc(conn, ep=None)
        from collections import defaultdict
        by_ep = defaultdict(lambda: {'total_predicted': 0, 'total_est': 0})
        for s in all_shots:
            by_ep[s['ep']]['total_predicted'] += s['predicted_efc']
            by_ep[s['ep']]['total_est']       += s['cost_est']
        for ep_data in by_ep.values():
            ep_data['total_predicted'] = round(ep_data['total_predicted'], 2)
            ep_data['total_est']       = round(ep_data['total_est'],       2)

        conn.close()
        return jsonify({'summary': summary, 'by_ep': dict(by_ep)})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/dashboard/vendor_health')
def dashboard_vendor_health():
    """
    Return vendor health metrics: capacity, payment status, performance score.
    Used for vendor health cards on dashboard.
    """
    conn = core.get_db()
    if not conn: return jsonify([])
    try:
        from services.vendors_svc import get_vendor_loads, get_vendor_perf_scores

        loads       = get_vendor_loads(conn)
        scores_list = get_vendor_perf_scores(conn)
        scores      = {r['vendor']: r for r in scores_list}

        # Invoice payment rates
        payment_rows = conn.execute(
            """SELECT UPPER(vendor) as v,
                      COUNT(*) as total_invoices,
                      SUM(CASE WHEN UPPER(status)='PAID' THEN 1 ELSE 0 END) as paid_invoices,
                      COALESCE(SUM(CASE WHEN UPPER(status)='PAID' THEN amount ELSE 0 END),0) as paid_amount,
                      COALESCE(SUM(CASE WHEN UPPER(status) IN ('PENDING','APPROVED')
                                        THEN amount ELSE 0 END),0) as pending_amount
               FROM invoice_log
               GROUP BY UPPER(vendor)"""
        ).fetchall()
        payment_map = {r['v']: dict(r) for r in payment_rows}

        result = []
        all_vendors = set(list(loads.keys()) + list(scores.keys()))
        for vendor in sorted(all_vendors):
            load  = loads.get(vendor, {})
            score = scores.get(vendor.upper(), {})
            pay   = payment_map.get(vendor.upper(), {})

            util  = load.get('utilization')
            if util is not None:
                cap_status = 'over'   if util > 1.0  else \
                             'high'   if util > 0.85 else \
                             'medium' if util > 0.5  else 'low'
            else:
                cap_status = 'unknown'

            result.append({
                'vendor':          vendor,
                'utilization':     round(util, 3)  if util is not None else None,
                'capacity_status': cap_status,
                'perf_score':      score.get('composite_score'),
                'invoice_accuracy': score.get('invoice_accuracy'),
                'total_invoices':  pay.get('total_invoices', 0),
                'paid_amount':     pay.get('paid_amount',    0),
                'pending_amount':  pay.get('pending_amount', 0),
            })

        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
