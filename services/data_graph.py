"""
services/data_graph.py — Cross-module data graph.
Links shots -> assets -> vendor_bids -> invoices for enriched analytics.
"""
import json
from services.db import get_db


def build_shot_graph(conn, ep=None):
    """
    Return a list of shot dicts enriched with:
    - payment_progress: sum of invoice payments / awarded amount (0-1)
    - overbid_risk: (efc - min_bid) / min_bid if bid data available
    - vendor_exposure: total awarded to vendor across season not yet invoiced
    """
    where = "WHERE s.ep=?" if ep else ""
    params = (ep,) if ep else ()
    shots = conn.execute(
        f"SELECT s.*, bt.vendor_bids FROM shots s "
        f"LEFT JOIN bid_compare bt ON bt.sc=s.scene_code AND bt.ep=s.ep "
        f"{where} ORDER BY s.ep, s.shot_num", params
    ).fetchall()

    # Build invoice payment map: {(vendor_upper, ep): paid_sum}
    inv_rows = conn.execute(
        "SELECT UPPER(vendor) as v, episode, COALESCE(SUM(amount),0) as paid "
        "FROM invoice_log WHERE UPPER(status)='PAID' GROUP BY UPPER(vendor), episode"
    ).fetchall()
    paid_map = {(r['v'], r['episode']): r['paid'] for r in inv_rows}

    # Build tracker award map: {(vendor_upper, ep): tot_award}
    trk_rows = conn.execute(
        "SELECT UPPER(vendor) as v, ep, COALESCE(tot_award,0) as tot_award "
        "FROM vendor_tracker"
    ).fetchall()
    award_map = {(r['v'], r['ep']): r['tot_award'] for r in trk_rows}

    result = []
    for s in shots:
        d = dict(s)
        vendor = (d.get('award_vendor') or '').upper()
        ep_num = d.get('ep')

        # payment_progress
        paid = paid_map.get((vendor, ep_num), 0) if vendor else 0
        awarded = award_map.get((vendor, ep_num), 0) if vendor else 0
        d['payment_progress'] = round(paid / awarded, 3) if awarded > 0 else 0

        # overbid_risk: compare efc vs min vendor bid
        try:
            bids_raw = d.get('vendor_bids')
            bids = json.loads(bids_raw) if isinstance(bids_raw, str) else (bids_raw or {})
            bid_vals = [float(v) for v in bids.values() if v]
            if bid_vals and d.get('efc'):
                min_bid = min(bid_vals)
                d['overbid_risk'] = round((float(d['efc']) - min_bid) / min_bid, 3) if min_bid > 0 else 0
            else:
                d['overbid_risk'] = 0
        except Exception:
            d['overbid_risk'] = 0

        # vendor_exposure: total awarded to vendor - total paid
        d['vendor_exposure'] = max(0, awarded - paid)

        result.append(d)
    return result


def get_season_risk_context(conn):
    """Return a dict with season-level risk data for LLM prompts."""
    eps = conn.execute("SELECT DISTINCT ep FROM shots ORDER BY ep").fetchall()
    ep_data = []
    for row in eps:
        ep = row['ep']
        shots = conn.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(cost_est*shot_est),0) as est, "
            "COALESCE(SUM(efc),0) as efc FROM shots WHERE ep=? AND omit=0", (ep,)
        ).fetchone()
        ep_data.append({
            'ep': ep,
            'shots': shots['cnt'],
            'est': shots['est'],
            'efc': shots['efc'],
            'variance': shots['efc'] - shots['est'],
        })

    vendors = conn.execute(
        "SELECT vendor, COALESCE(SUM(tot_award),0) as total FROM vendor_tracker GROUP BY UPPER(vendor) ORDER BY total DESC LIMIT 5"
    ).fetchall()

    return {
        'ep_breakdown': ep_data,
        'top_vendors': [dict(r) for r in vendors],
        'total_est': sum(e['est'] for e in ep_data),
        'total_efc': sum(e['efc'] for e in ep_data),
        'variance': sum(e['variance'] for e in ep_data),
        'total_shots': sum(e['shots'] for e in ep_data),
    }
