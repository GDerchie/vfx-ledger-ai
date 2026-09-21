"""
services/optimizer.py — Season optimizer (lowest-cost vendor assignment).
"""
import json


def run_season_optimizer(conn, settings):
    """Propose lowest-cost vendor assignments across all shots (or one EP).

    Algorithm (VFX Ledger SeasonOptimizer):
      For each shot -> match to bid_compare row by scene_code
      For each vendor in that scene's bids:
        - Skip if confidence < min_confidence
        - Skip if vendor share would exceed max_vendor_share
        - Skip if preferred_vendors set AND a preferred vendor bid this scene
      Choose vendor with minimum per-shot cost.

    Returns:
      assignments        {shot_id: {vendor, cost, scene_code, ep, shot_type,
                                    complexity, current_vendor}}
      vendor_summary     {vendor: {total_shots, total_cost, avg_confidence,
                                   workload_ratio, confidence_label}}
      total_cost         float
      overall_confidence float  (0-1)
      total_shots        int
      assigned_shots     int
      unassigned_shots   [{shot_id, scene_code, ep, reason}]
      settings_used      dict
    """
    min_confidence = float(settings.get('min_confidence', 0.5))
    max_share      = float(settings.get('max_vendor_share', 1.0))
    preferred_raw  = settings.get('preferred_vendors') or []
    preferred      = {v.strip().upper() for v in preferred_raw if v.strip()}
    ep_filter      = settings.get('ep_filter') or None

    # Vendor confidence scores (CV formula)
    bid_rows = conn.execute(
        'SELECT vendor_bids FROM bid_compare WHERE novfx=0'
    ).fetchall()
    buckets = {}
    for r in bid_rows:
        try:
            bids = json.loads(r['vendor_bids'] or '{}')
            for v, amt in bids.items():
                try:
                    buckets.setdefault(v.strip(), []).append(float(amt))
                except Exception:
                    pass
        except Exception:
            pass

    vendor_conf = {}
    for v, amounts in buckets.items():
        n = len(amounts)
        m = sum(amounts) / n if n else 0
        sd = (sum((x - m) ** 2 for x in amounts) / max(n - 1, 1)) ** 0.5 if n > 1 else 0
        cv = (sd / m) if m else 1.0
        vendor_conf[v] = round(min(n / 30.0, 1.0) * max(0.0, 1.0 - cv), 3)

    # Bid lookup: scene_code -> {vendor -> per-shot cost}
    bc_rows = conn.execute(
        'SELECT sc, scount, vendor_bids, version FROM bid_compare WHERE novfx=0'
        ' ORDER BY sc, version DESC'
    ).fetchall()

    scene_bids = {}
    for r in bc_rows:
        sc = str(r['sc'] or '').strip()
        if not sc or sc in scene_bids:
            continue
        try:
            bids = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            bids = {}
        scount = max(int(r['scount'] or 1), 1)
        scene_bids[sc] = {
            v: round(float(amt) / scount, 2)
            for v, amt in bids.items()
            if amt is not None and str(amt).strip() not in ('', 'None')
        }

    # Load shots
    q = ('SELECT id, ep, scene_code, shot_type, complexity, award_vendor'
         ' FROM shots WHERE omit=0')
    params = []
    if ep_filter:
        q += ' AND ep=?'
        params.append(ep_filter)
    shots = conn.execute(q, params).fetchall()
    total_shots = len(shots)

    vendor_shots    = {}
    vendor_cost_sum = {}
    vendor_conf_sum = {}
    assignments     = {}
    unassigned      = []

    for shot in shots:
        shot_id       = shot['id']
        sc            = str(shot['scene_code'] or '').strip()
        bids_for_sc   = scene_bids.get(sc, {})

        if not bids_for_sc:
            unassigned.append({
                'shot_id': shot_id, 'scene_code': sc,
                'ep': shot['ep'], 'reason': 'No bid data for this scene',
            })
            continue

        best_vendor = None
        best_cost   = None

        for vendor, per_shot_cost in sorted(bids_for_sc.items()):
            conf = vendor_conf.get(vendor, 0.0)

            if conf < min_confidence:
                continue

            if max_share < 1.0:
                current_share = vendor_shots.get(vendor, 0) / max(total_shots, 1)
                if current_share >= max_share:
                    continue

            if preferred:
                vendors_upper = {vv.upper() for vv in bids_for_sc}
                has_preferred = bool(preferred & vendors_upper)
                if has_preferred and vendor.upper() not in preferred:
                    continue

            if best_cost is None or per_shot_cost < best_cost:
                best_cost   = per_shot_cost
                best_vendor = vendor

        if best_vendor is None:
            unassigned.append({
                'shot_id': shot_id, 'scene_code': sc,
                'ep': shot['ep'],
                'reason': 'No vendor met confidence/share/preferred constraints',
            })
            continue

        assignments[shot_id] = {
            'vendor':          best_vendor,
            'cost':            best_cost,
            'scene_code':      sc,
            'ep':              shot['ep'],
            'shot_type':       shot['shot_type'] or '',
            'complexity':      shot['complexity'] or '',
            'current_vendor':  shot['award_vendor'] or '',
        }
        vendor_shots[best_vendor]    = vendor_shots.get(best_vendor, 0) + 1
        vendor_cost_sum[best_vendor] = vendor_cost_sum.get(best_vendor, 0.0) + best_cost
        vendor_conf_sum[best_vendor] = vendor_conf_sum.get(best_vendor, 0.0) + conf

    # Build summaries
    assigned_total = len(assignments)
    total_cost     = sum(vendor_cost_sum.values())

    vendor_summary = {}
    for v, shots_v in vendor_shots.items():
        avg_conf = vendor_conf_sum[v] / shots_v if shots_v else 0.0
        vendor_summary[v] = {
            'total_shots':       shots_v,
            'total_cost':        round(vendor_cost_sum[v], 2),
            'avg_confidence':    round(avg_conf, 3),
            'workload_ratio':    round(shots_v / max(assigned_total, 1), 3),
            'confidence_label':  'HIGH' if avg_conf >= 0.7 else ('MED' if avg_conf >= 0.4 else 'LOW'),
        }

    overall_conf = (
        sum(d['avg_confidence'] for d in vendor_summary.values()) / len(vendor_summary)
        if vendor_summary else 0.0
    )

    return {
        'assignments':        assignments,
        'vendor_summary':     vendor_summary,
        'total_cost':         round(total_cost, 2),
        'overall_confidence': round(overall_conf, 3),
        'total_shots':        total_shots,
        'assigned_shots':     assigned_total,
        'unassigned_shots':   unassigned,
        'settings_used': {
            'min_confidence':   min_confidence,
            'max_vendor_share': max_share,
            'preferred_vendors': list(preferred),
            'ep_filter':        ep_filter,
        },
    }
