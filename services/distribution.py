"""
services/distribution.py — Episode risk forecast and predictive EFC engine.
"""
import json
from collections import defaultdict
from services.vendors_svc import get_vendor_loads


def compute_ep_risk(conn, ep):
    """Compute delivery risk score for one episode.

    Formula (from VFX Ledger delivery_risk_engine.py):
      risk = capacity_risk * 0.45 + complexity_risk * 0.30 + confidence_risk * 0.25
      predicted_delay_days = int(risk * 30)
      status: SAFE (<0.25) | WATCH (<0.50) | AT RISK (<0.70) | HIGH RISK

    Inputs pulled directly from the project DB:
      - shots.complexity + shots.award_vendor
      - vendor_capacity (via get_vendor_loads)
      - bid_compare.vendor_bids (for confidence scoring)
    """
    shots = conn.execute(
        'SELECT complexity, award_vendor, shot_est FROM shots WHERE ep=? AND omit=0',
        (ep,)
    ).fetchall()

    empty = {
        'ep': ep, 'risk_score': 0.0, 'predicted_delay_days': 0,
        'capacity_risk': 0.0, 'complexity_risk': 0.0, 'confidence_risk': 0.0,
        'status': 'SAFE', 'shot_count': 0,
    }
    if not shots:
        return empty

    vendor_loads = get_vendor_loads(conn)

    # Build per-vendor confidence from bid_compare (same CV formula as /api/vendor_confidence)
    bid_rows = conn.execute('SELECT vendor_bids FROM bid_compare WHERE novfx=0').fetchall()
    buckets = {}
    for r in bid_rows:
        try:
            bids = json.loads(r['vendor_bids'] or '{}')
            for v, amt in bids.items():
                try:
                    buckets.setdefault(v.strip().upper(), []).append(float(amt))
                except Exception:
                    pass
        except Exception:
            pass

    vendor_conf = {}
    for v_key, amounts in buckets.items():
        n = len(amounts)
        if n < 2:
            cv = 1.0
        else:
            m = sum(amounts) / n
            sd = (sum((x - m) ** 2 for x in amounts) / (n - 1)) ** 0.5
            cv = (sd / m) if m else 1.0
        sample_factor = min(n / 30.0, 1.0)
        vendor_conf[v_key] = round(sample_factor * max(0.0, 1.0 - cv), 3)

    total = len(shots)
    cap_risk = 0.0
    cmp_risk = 0.0
    conf_risk = 0.0

    for shot in shots:
        vendor = (shot['award_vendor'] or '').strip()
        vendor_key = vendor.upper()

        # Capacity risk contribution
        load = vendor_loads.get(vendor)
        if load and load['has_capacity'] and load['utilization'] is not None:
            util = load['utilization']
            if util > 1.0:
                cap_risk += 1.0
            elif util > 0.85:
                cap_risk += 0.5

        # Complexity risk contribution
        cx = (shot['complexity'] or '').strip().upper()
        if cx == 'HERO':
            cmp_risk += 1.0
        elif cx in ('HIGH', 'HEAVY'):
            cmp_risk += 0.6

        # Confidence risk contribution
        conf = vendor_conf.get(vendor_key)
        if conf is not None:
            conf_risk += (1.0 - conf)
        else:
            conf_risk += 0.5  # unscored vendor = moderate uncertainty

    cap_risk  /= total
    cmp_risk  /= total
    conf_risk /= total

    score = round(cap_risk * 0.45 + cmp_risk * 0.30 + conf_risk * 0.25, 3)

    if score < 0.25:
        status = 'SAFE'
    elif score < 0.50:
        status = 'WATCH'
    elif score < 0.70:
        status = 'AT RISK'
    else:
        status = 'HIGH RISK'

    return {
        'ep':               ep,
        'risk_score':       score,
        'predicted_delay_days': int(score * 30),
        'capacity_risk':    round(cap_risk, 3),
        'complexity_risk':  round(cmp_risk, 3),
        'confidence_risk':  round(conf_risk, 3),
        'status':           status,
        'shot_count':       total,
    }


# ---------------------------------------------------------------------------
# Predictive EFC — actuals-anchored delivery ratio model
# ---------------------------------------------------------------------------

def compute_predictive_efc(conn, ep=None):
    """
    Predict final cost per shot using vendor × type delivery ratios.

    delivery_ratio = mean(actual_invoice / cost_est) per (vendor, shot_type)
    predicted_efc  = cost_est × delivery_ratio[vendor][type]

    Falls back to:
      - vendor-only ratio   if type combo has < 2 data points
      - type-only ratio     if vendor has no history
      - global ratio        if neither match
      - cost_est × 1.0      if no actuals at all

    Returns list of dicts: [{shot_id, ep, cost_est, predicted_efc, ratio, source}, ...]
    Also returns summary dict with season totals.
    """
    # Build ratio table from all shots with both cost_est and efc
    actuals = conn.execute(
        """SELECT id, ep, shot_type, award_vendor,
                  COALESCE(cost_est, 0) AS cost_est,
                  COALESCE(efc, 0)      AS efc
           FROM shots
           WHERE omit=0 AND cost_est > 0 AND efc > 0"""
    ).fetchall()

    # Buckets keyed by (vendor_upper, type_upper) → list of ratios
    vt_ratios = defaultdict(list)   # (vendor, type)
    v_ratios  = defaultdict(list)   # (vendor,)
    t_ratios  = defaultdict(list)   # (type,)
    g_ratios  = []                  # global

    for a in actuals:
        ratio = a['efc'] / a['cost_est']
        if ratio <= 0 or ratio > 10:   # sanity-cap outliers
            continue
        vendor = (a['award_vendor'] or '').strip().upper()
        stype  = (a['shot_type']    or '').strip().upper()
        if vendor and stype:
            vt_ratios[(vendor, stype)].append(ratio)
        if vendor:
            v_ratios[vendor].append(ratio)
        if stype:
            t_ratios[stype].append(ratio)
        g_ratios.append(ratio)

    def _mean(lst):
        return sum(lst) / len(lst) if lst else None

    # For forecast, query target shots
    where = 'WHERE ep=? AND omit=0 AND cost_est > 0' if ep else 'WHERE omit=0 AND cost_est > 0'
    params = (ep,) if ep else ()
    shots = conn.execute(
        f"SELECT id, ep, shot_type, award_vendor, cost_est FROM shots {where} ORDER BY ep, shot_num",
        params
    ).fetchall()

    global_ratio = _mean(g_ratios) or 1.0
    results = []

    for s in shots:
        vendor = (s['award_vendor'] or '').strip().upper()
        stype  = (s['shot_type']    or '').strip().upper()
        ce     = s['cost_est']

        # Pick best ratio with source label
        ratio, source = None, 'global'
        if vendor and stype:
            r = _mean(vt_ratios.get((vendor, stype), []))
            if r and len(vt_ratios.get((vendor, stype), [])) >= 2:
                ratio, source = r, 'vendor+type'
        if ratio is None and vendor:
            r = _mean(v_ratios.get(vendor, []))
            if r and len(v_ratios.get(vendor, [])) >= 2:
                ratio, source = r, 'vendor'
        if ratio is None and stype:
            r = _mean(t_ratios.get(stype, []))
            if r and len(t_ratios.get(stype, [])) >= 2:
                ratio, source = r, 'type'
        if ratio is None:
            ratio, source = global_ratio, 'global'

        predicted = round(ce * ratio, 2)
        results.append({
            'shot_id':       s['id'],
            'ep':            s['ep'],
            'cost_est':      ce,
            'predicted_efc': predicted,
            'ratio':         round(ratio, 3),
            'source':        source,
        })

    total_est       = sum(r['cost_est']      for r in results)
    total_predicted = sum(r['predicted_efc'] for r in results)
    summary = {
        'total_est':       round(total_est,       2),
        'total_predicted': round(total_predicted, 2),
        'predicted_variance': round(total_predicted - total_est, 2),
        'global_ratio':    round(global_ratio, 3),
        'actuals_used':    len(actuals),
        'shots_forecast':  len(results),
    }

    return results, summary
