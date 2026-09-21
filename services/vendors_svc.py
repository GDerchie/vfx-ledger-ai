"""
services/vendors_svc.py — Vendor helper functions.
"""
import json


def _sfloat(v):
    """Safe float — returns None for error strings/None."""
    if v is None: return None
    s = str(v).strip()
    if not s or s.startswith('#') or s.startswith('\u26a0'): return None
    try: return float(s)
    except: return None


def sync_tracker_paid(conn, vendor, ep):
    """Recalculate paid/pending/remaining from invoices and update tracker row."""
    if not vendor or ep is None:
        return
    tracker = conn.execute(
        'SELECT id, tot_award FROM vendor_tracker WHERE UPPER(vendor)=UPPER(?) AND ep=?',
        (vendor, ep)
    ).fetchone()
    if not tracker:
        c = conn.cursor()
        c.execute(
            'INSERT INTO vendor_tracker (vendor, ep, tot_award, paid, pending, remaining) VALUES (?,?,0,0,0,0)',
            (vendor, ep)
        )
        tracker_id = c.lastrowid
        tot_award = 0
    else:
        tracker_id = tracker['id']
        tot_award = tracker['tot_award'] or 0
    paid_sum = conn.execute(
        'SELECT COALESCE(SUM(amount),0) FROM invoice_log WHERE UPPER(vendor)=UPPER(?) AND episode=? AND UPPER(status)="PAID"',
        (vendor, ep)
    ).fetchone()[0]
    pending_sum = conn.execute(
        'SELECT COALESCE(SUM(amount),0) FROM invoice_log WHERE UPPER(vendor)=UPPER(?) AND episode=? AND UPPER(status) IN ("PENDING","APPROVED")',
        (vendor, ep)
    ).fetchone()[0]
    remaining = tot_award - paid_sum
    conn.execute(
        'UPDATE vendor_tracker SET paid=?, pending=?, remaining=? WHERE id=?',
        (paid_sum, pending_sum, remaining, tracker_id)
    )


def get_vendor_loads(conn):
    """Per-vendor shot load vs capacity.
    Returns dict keyed by vendor name (original case):
      {vendor, assigned, capacity, utilization, overload, has_capacity}
    utilization = assigned_shots / (shots_per_month * efficiency_pct)
    """
    caps = {}
    for r in conn.execute(
        'SELECT vendor, shots_per_month, efficiency_pct FROM vendor_capacity'
    ).fetchall():
        effective = (r['shots_per_month'] or 100) * (r['efficiency_pct'] or 0.95)
        caps[r['vendor'].strip().upper()] = {'vendor': r['vendor'], 'capacity': effective}

    assigned = {}
    for r in conn.execute(
        '''SELECT award_vendor, SUM(COALESCE(shot_est, 1)) AS shots
           FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor != ""
           GROUP BY award_vendor'''
    ).fetchall():
        key = r['award_vendor'].strip().upper()
        assigned[key] = {'vendor': r['award_vendor'], 'shots': r['shots'] or 0}

    result = {}
    for key in set(list(caps.keys()) + list(assigned.keys())):
        vendor_name = (caps.get(key) or assigned.get(key) or {}).get('vendor', key)
        shots = (assigned.get(key) or {}).get('shots', 0)
        capacity = (caps.get(key) or {}).get('capacity', 0)
        util = (shots / capacity) if capacity > 0 else None
        result[vendor_name] = {
            'vendor':      vendor_name,
            'assigned':    shots,
            'capacity':    round(capacity),
            'utilization': round(util, 3) if util is not None else None,
            'overload':    (util > 1.0) if util is not None else False,
            'has_capacity': capacity > 0,
        }
    return result


def get_vendor_perf_scores(conn):
    """Composite vendor performance score combining three signals.

    Components (weights adjust when data is absent):
      bid_confidence   (0-1)  CV-based price consistency from bid_compare  [w=0.50]
      invoice_accuracy (0-1)  1 - |tot_award - paid| / tot_award           [w=0.30]
      edit_efficiency  (0-1)  1 - (avg_edit_count / 20).clamp(0,1)         [w=0.20]

    Label: STRONG >=0.65 | MED >=0.40 | WEAK <0.40
    Returns list of dicts sorted by composite_score desc.
    """
    # 1. Bid confidence (CV formula)
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

    bid_conf = {}
    for v_key, amounts in buckets.items():
        n = len(amounts)
        if n < 2:
            cv = 1.0
        else:
            m  = sum(amounts) / n
            sd = (sum((x - m) ** 2 for x in amounts) / (n - 1)) ** 0.5
            cv = (sd / m) if m else 1.0
        sample_factor = min(n / 30.0, 1.0)
        bid_conf[v_key] = round(sample_factor * max(0.0, 1.0 - cv), 3)

    # 2. Invoice accuracy
    tracker_rows = conn.execute(
        'SELECT UPPER(vendor) as v, SUM(tot_award) as award '
        'FROM vendor_tracker WHERE vendor IS NOT NULL GROUP BY UPPER(vendor)'
    ).fetchall()
    invoice_paid = conn.execute(
        "SELECT UPPER(vendor) as v, SUM(amount) as paid "
        "FROM invoice_log WHERE UPPER(status)='PAID' AND vendor IS NOT NULL GROUP BY UPPER(vendor)"
    ).fetchall()
    award_map = {r['v']: float(r['award'] or 0) for r in tracker_rows}
    paid_map  = {r['v']: float(r['paid']  or 0) for r in invoice_paid}

    inv_accuracy = {}
    for v_key, award in award_map.items():
        if award <= 0:
            continue
        paid = paid_map.get(v_key, 0)
        inv_accuracy[v_key] = round(max(0.0, 1.0 - abs(award - paid) / award), 3)

    # 3. Edit efficiency
    shot_rows = conn.execute(
        'SELECT UPPER(award_vendor) as v, AVG(edit_count) as avg_edits '
        'FROM shots WHERE award_vendor IS NOT NULL AND omit=0 GROUP BY UPPER(award_vendor)'
    ).fetchall()
    edit_eff = {}
    for r in shot_rows:
        avg_edits = float(r['avg_edits'] or 0)
        edit_eff[r['v']] = round(max(0.0, 1.0 - avg_edits / 20.0), 3)

    # 4. Composite score
    all_vendors = set(bid_conf) | set(inv_accuracy) | set(edit_eff)
    results = []
    for v_key in all_vendors:
        bc = bid_conf.get(v_key, 0.0)
        ia = inv_accuracy.get(v_key)
        ee = edit_eff.get(v_key)

        if ia is not None and ee is not None:
            score = round(bc * 0.50 + ia * 0.30 + ee * 0.20, 3)
        elif ia is not None:
            score = round(bc * 0.60 + ia * 0.40, 3)
        elif ee is not None:
            score = round(bc * 0.70 + ee * 0.30, 3)
        else:
            score = bc

        results.append({
            'vendor':           v_key,
            'bid_confidence':   bc,
            'invoice_accuracy': ia,
            'edit_efficiency':  ee,
            'composite_score':  score,
            'label':            'STRONG' if score >= 0.65 else ('MED' if score >= 0.40 else 'WEAK'),
            'bid_samples':      len(buckets.get(v_key, [])),
        })

    results.sort(key=lambda x: -x['composite_score'])
    return results
