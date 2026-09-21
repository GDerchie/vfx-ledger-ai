"""
services/game_theory.py — Game Theory engine for VFX budget forecasting
and vendor assessment.

Models:
  1. Sealed-Bid Auction Model       → budget P10 / P50 (Nash) / P90 forecast
  2. Shapley Value Assessment        → each vendor's marginal contribution to savings
  3. Defection Risk (Prisoner's Dilemma) → vendor reliability under strain
  4. Nash Equilibrium Allocation     → best-response stable assignment
  5. Repeated Game Memory            → historical overrun penalty across seasons
  6. Coalition Blocking              → Shapley × capacity collision detection
  7. Auction Type Comparison         → First-price vs Second-price (Vickrey) simulation

All functions are read-only; no DB writes.
"""
import json
import math
import random
import sqlite3
import os
from itertools import combinations


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_bid_matrix(conn):
    """Return {scene_code: {vendor: amount}} — latest version per scene, novfx=0."""
    rows = conn.execute(
        'SELECT sc, scount, vendor_bids, version FROM bid_compare WHERE novfx=0'
        ' ORDER BY sc, version DESC'
    ).fetchall()
    scene_bids = {}
    for r in rows:
        sc = str(r['sc'] or '').strip()
        if not sc or sc in scene_bids:
            continue
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        bids = {}
        for v, amt in raw.items():
            try:
                bids[v.strip()] = float(amt) / scount
            except (TypeError, ValueError):
                pass
        if bids:
            scene_bids[sc] = bids
    return scene_bids


def _load_bid_matrix_ep(conn, ep_filter=None):
    """Like _load_bid_matrix but filtered (optionally) by episode."""
    q = 'SELECT sc, scount, vendor_bids, version, ep FROM bid_compare WHERE novfx=0 ORDER BY sc, version DESC'
    rows = conn.execute(q).fetchall()
    scene_bids = {}
    for r in rows:
        if ep_filter is not None and int(r['ep'] or 0) != ep_filter:
            continue
        sc = str(r['sc'] or '').strip()
        if not sc or sc in scene_bids:
            continue
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        bids = {}
        for v, amt in raw.items():
            try:
                bids[v.strip()] = float(amt) / scount
            except (TypeError, ValueError):
                pass
        if bids:
            scene_bids[sc] = bids
    return scene_bids


def _vendor_bid_history(conn):
    """Return {vendor_upper: [amount, ...]} across all scenes."""
    rows = conn.execute('SELECT vendor_bids, scount FROM bid_compare WHERE novfx=0').fetchall()
    buckets = {}
    for r in rows:
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        for v, amt in raw.items():
            try:
                buckets.setdefault(v.strip().upper(), []).append(float(amt) / scount)
            except (TypeError, ValueError):
                pass
    return buckets


def _stats(vals):
    """Return (mean, std, lo, hi) for a list of floats."""
    if not vals:
        return 0.0, 0.0, 0.0, 0.0
    n = len(vals)
    m = sum(vals) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / max(n - 1, 1)) if n > 1 else 0.0
    return m, sd, min(vals), max(vals)


def _normal_ppf(p):
    """Rational approximation of the inverse normal CDF (Beasley-Springer-Moro)."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
        return -(((0.010328 * t + 0.802853) * t + 2.515517) /
                 (((0.001308 * t + 0.189269) * t + 1.432788) * t + 1.0) - t)
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    return (((0.010328 * t + 0.802853) * t + 2.515517) /
            (((0.001308 * t + 0.189269) * t + 1.432788) * t + 1.0) - t)


def _expected_min_normal(means, stds):
    """
    Approximate expected minimum of K independent normal distributions.
    Uses 1000-sample Monte Carlo for accuracy with small K.
    Returns (expected_min, p10, p90).
    """
    if not means:
        return 0.0, 0.0, 0.0
    rng = random.Random(42)
    samples = []
    for _ in range(1000):
        mins = [rng.gauss(m, max(s, 0.01)) for m, s in zip(means, stds)]
        samples.append(min(mins))
    samples.sort()
    n = len(samples)
    return (
        sum(samples) / n,
        samples[max(0, int(n * 0.10))],
        samples[min(n - 1, int(n * 0.90))],
    )


# ── 1. Budget Game Forecast ───────────────────────────────────────────────────

def budget_game_forecast(conn, ep_filter=None):
    """
    Auction-theory budget forecast across all scenes.

    For each scene modelled as a sealed-bid first-price auction among the vendors
    that submitted bids, we compute three budget scenarios:

      competitive  (P10)  — aggressive competition; expect the minimum bid
      equilibrium  (P50)  — Nash equilibrium bidding; vendors mark up above cost
      ceiling      (P90)  — thin competition / market ceiling

    Returns
    -------
    {
      scenes_analysed    int
      competitive_total  float   # P10 sum
      equilibrium_total  float   # P50 sum — headline figure
      ceiling_total      float   # P90 sum
      scenes             [{ sc, n_vendors, competitive, equilibrium, ceiling,
                             equilibrium_vendor, spread_pct }]
      ep_breakdown       { ep: { competitive, equilibrium, ceiling, scenes } }
      vendor_aggression  { vendor: { win_rate, avg_markup, aggression_label } }
    }
    """
    # Load scene bids with ep info for breakdown
    rows = conn.execute(
        'SELECT sc, scount, vendor_bids, version, ep FROM bid_compare WHERE novfx=0'
        ' ORDER BY sc, version DESC'
    ).fetchall()

    seen_sc  = set()
    scene_data = []  # [{sc, ep, bids:{vendor:per_shot}}]
    for r in rows:
        if ep_filter is not None and int(r['ep'] or 0) != ep_filter:
            continue
        sc = str(r['sc'] or '').strip()
        if not sc or sc in seen_sc:
            continue
        seen_sc.add(sc)
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        bids = {}
        for v, amt in raw.items():
            try:
                bids[v.strip()] = float(amt) / scount
            except (TypeError, ValueError):
                pass
        if bids:
            scene_data.append({'sc': sc, 'ep': int(r['ep'] or 0), 'bids': bids})

    if not scene_data:
        return {
            'scenes_analysed': 0,
            'competitive_total': 0.0,
            'equilibrium_total': 0.0,
            'ceiling_total': 0.0,
            'scenes': [],
            'ep_breakdown': {},
            'vendor_aggression': {},
        }

    # Vendor bid history for std estimation
    hist = _vendor_bid_history(conn)
    vendor_stats = {}
    for v_upper, amounts in hist.items():
        m, sd, lo, hi = _stats(amounts)
        vendor_stats[v_upper] = {'mean': m, 'std': sd, 'lo': lo, 'hi': hi}

    scenes_out    = []
    ep_agg        = {}   # ep -> {competitive, equilibrium, ceiling, scenes}
    vendor_wins   = {}   # vendor_upper -> {wins, total_bids, total_markup}

    for sd in scene_data:
        sc    = sd['sc']
        ep    = sd['ep']
        bids  = sd['bids']   # {vendor: per_shot_cost}
        n     = len(bids)

        sorted_bids = sorted(bids.items(), key=lambda x: x[1])
        lo_vendor, lo_bid = sorted_bids[0]
        hi_bid = sorted_bids[-1][1]
        avg_bid = sum(bids.values()) / n

        # ── Competitive (P10): expected minimum given bid distributions
        means_list = []
        stds_list  = []
        for v, amt in bids.items():
            vk = v.upper()
            sd_v = vendor_stats.get(vk, {}).get('std', amt * 0.05)
            means_list.append(amt)
            stds_list.append(sd_v)

        exp_min, p10_val, _ = _expected_min_normal(means_list, stds_list)
        competitive = round(max(p10_val, lo_bid * 0.85), 2)

        # ── Nash Equilibrium (P50): first-price auction NE markup
        # With N symmetric bidders, NE bid = cost + (cost - cost_floor) / (N-1)
        # We use the lowest bid as proxy for "true cost" and markup accordingly
        if n >= 2:
            cost_floor = lo_bid * 0.90   # assume 10% margin floor
            markup = (lo_bid - cost_floor) / max(n - 1, 1)
            equilibrium = round(lo_bid + markup, 2)
        else:
            equilibrium = round(lo_bid * 1.08, 2)  # single vendor: 8% premium

        # ── Ceiling (P90): reduced competition scenario
        # Model: only top-2 vendors bid → expected price is higher
        if n >= 3:
            top2_avg = (sorted_bids[0][1] + sorted_bids[1][1]) / 2.0
            ceiling = round(top2_avg * 1.12, 2)
        else:
            ceiling = round(hi_bid * 1.05, 2)

        spread_pct = round((ceiling - competitive) / max(competitive, 1) * 100.0, 1)

        scenes_out.append({
            'sc':                sc,
            'ep':                ep,
            'n_vendors':         n,
            'competitive':       competitive,
            'equilibrium':       equilibrium,
            'ceiling':           ceiling,
            'equilibrium_vendor': lo_vendor,
            'spread_pct':        spread_pct,
            'all_bids':          {v: round(a, 2) for v, a in bids.items()},
        })

        # EP aggregation
        if ep not in ep_agg:
            ep_agg[ep] = {'competitive': 0.0, 'equilibrium': 0.0, 'ceiling': 0.0, 'scenes': 0}
        ep_agg[ep]['competitive']  += competitive
        ep_agg[ep]['equilibrium']  += equilibrium
        ep_agg[ep]['ceiling']      += ceiling
        ep_agg[ep]['scenes']       += 1

        # Vendor aggression tracking
        for v, amt in bids.items():
            vk = v.upper()
            if vk not in vendor_wins:
                vendor_wins[vk] = {'wins': 0, 'total_bids': 0, 'total_markup': 0.0, 'name': v}
            vendor_wins[vk]['total_bids'] += 1
            markup_ratio = (amt - lo_bid) / max(lo_bid, 1.0)
            vendor_wins[vk]['total_markup'] += markup_ratio
            if v == lo_vendor:
                vendor_wins[vk]['wins'] += 1

    # Round EP agg
    for ep_key in ep_agg:
        ep_agg[ep_key]['competitive']  = round(ep_agg[ep_key]['competitive'], 2)
        ep_agg[ep_key]['equilibrium']  = round(ep_agg[ep_key]['equilibrium'], 2)
        ep_agg[ep_key]['ceiling']      = round(ep_agg[ep_key]['ceiling'], 2)

    # Vendor aggression labels
    vendor_aggression = {}
    for vk, data in vendor_wins.items():
        n_bids  = max(data['total_bids'], 1)
        win_r   = round(data['wins'] / n_bids, 3)
        avg_mkp = round(data['total_markup'] / n_bids, 3)
        label   = ('AGGRESSIVE' if win_r >= 0.4 else
                   ('COMPETITIVE' if win_r >= 0.2 else 'PASSIVE'))
        vendor_aggression[data['name']] = {
            'win_rate':       win_r,
            'avg_markup':     avg_mkp,
            'aggression_label': label,
            'total_bids':     n_bids,
        }

    total_competitive  = round(sum(s['competitive']  for s in scenes_out), 2)
    total_equilibrium  = round(sum(s['equilibrium']  for s in scenes_out), 2)
    total_ceiling      = round(sum(s['ceiling']       for s in scenes_out), 2)

    return {
        'scenes_analysed':   len(scenes_out),
        'competitive_total': total_competitive,
        'equilibrium_total': total_equilibrium,
        'ceiling_total':     total_ceiling,
        'scenes':            scenes_out,
        'ep_breakdown':      ep_agg,
        'vendor_aggression': vendor_aggression,
    }


# ── 2. Shapley Value Assessment ───────────────────────────────────────────────

def _coalition_optimal_cost(scene_bids, vendor_set):
    """
    Given a scene->bids dict and a set of allowed vendors,
    return the sum of min bids across all scenes where at least one
    allowed vendor has bid.
    """
    total = 0.0
    covered = 0
    vendor_upper = {v.upper() for v in vendor_set}
    for sc, bids in scene_bids.items():
        eligible = {v: amt for v, amt in bids.items() if v.upper() in vendor_upper}
        if eligible:
            total += min(eligible.values())
            covered += 1
    return total, covered


def shapley_vendor_assessment(conn, max_vendors=12):
    """
    Compute Shapley values for each vendor.

    Shapley(v_i) measures how much vendor i reduces the total season cost
    (on average, marginal contribution across all subsets).

    Positive Shapley = vendor saves money vs. excluding them.
    High Shapley = critical vendor; removing them significantly raises costs.

    Returns list of dicts sorted by shapley_savings desc:
    [{ vendor, shapley_savings, shapley_pct, win_count, bid_count, coverage_pct,
       marginal_scenes, label }]
    """
    scene_bids = _load_bid_matrix(conn)
    if not scene_bids:
        return []

    # Collect all vendors
    all_vendors = set()
    for bids in scene_bids.values():
        all_vendors.update(bids.keys())
    all_vendors = sorted(all_vendors)

    # Cap at max_vendors (use top bidders by coverage)
    if len(all_vendors) > max_vendors:
        coverage = {v: sum(1 for bids in scene_bids.values() if v in bids) for v in all_vendors}
        all_vendors = sorted(all_vendors, key=lambda v: -coverage[v])[:max_vendors]

    n = len(all_vendors)
    if n == 0:
        return []

    n_scenes = len(scene_bids)

    # For large n use Monte Carlo sampling (~500 permutations)
    if n > 10:
        shapley_vals = _shapley_monte_carlo(scene_bids, all_vendors, n_permutations=600)
    else:
        shapley_vals = _shapley_exact(scene_bids, all_vendors)

    # Build per-vendor metrics
    win_counts = {v: 0 for v in all_vendors}
    bid_counts = {v: 0 for v in all_vendors}
    for sc, bids in scene_bids.items():
        if not bids:
            continue
        best_v = min(bids, key=bids.get)
        for v in all_vendors:
            if v in bids:
                bid_counts[v] += 1
                if v == best_v:
                    win_counts[v] += 1

    total_shapley = sum(abs(v) for v in shapley_vals.values()) or 1.0

    results = []
    for v in all_vendors:
        sv   = shapley_vals.get(v, 0.0)
        bc   = bid_counts.get(v, 0)
        cov  = round(bc / max(n_scenes, 1) * 100, 1)
        results.append({
            'vendor':          v,
            'shapley_savings': round(sv, 2),
            'shapley_pct':     round(sv / total_shapley * 100, 1),
            'win_count':       win_counts.get(v, 0),
            'bid_count':       bc,
            'coverage_pct':    cov,
            'label':           ('CRITICAL' if sv >= total_shapley * 0.25 else
                                ('IMPORTANT' if sv >= total_shapley * 0.10 else 'SUPPORT')),
        })

    results.sort(key=lambda x: -x['shapley_savings'])
    return results


def _shapley_exact(scene_bids, vendors):
    """Exact Shapley values via subset enumeration."""
    n = len(vendors)
    shapley = {v: 0.0 for v in vendors}

    for i, v in enumerate(vendors):
        others = [u for j, u in enumerate(vendors) if j != i]
        for size in range(n):  # size = |S| where S is subset WITHOUT v
            coeff = (
                math.factorial(size) * math.factorial(n - size - 1) / math.factorial(n)
            )
            for subset in combinations(others, size):
                s_with    = list(subset) + [v]
                s_without = list(subset)
                cost_with, _    = _coalition_optimal_cost(scene_bids, s_with)
                cost_without, _ = _coalition_optimal_cost(scene_bids, s_without)
                # Savings from adding v = cost_without - cost_with
                marginal = cost_without - cost_with
                shapley[v] += coeff * marginal

    return shapley


def _shapley_monte_carlo(scene_bids, vendors, n_permutations=600):
    """Monte Carlo Shapley approximation via random permutation sampling."""
    n = len(vendors)
    shapley = {v: 0.0 for v in vendors}
    rng = random.Random(42)

    for _ in range(n_permutations):
        perm = vendors[:]
        rng.shuffle(perm)
        prev_cost, _ = _coalition_optimal_cost(scene_bids, [])
        for i, v in enumerate(perm):
            coalition = perm[:i + 1]
            cur_cost, _ = _coalition_optimal_cost(scene_bids, coalition)
            shapley[v] += prev_cost - cur_cost
            prev_cost = cur_cost

    for v in shapley:
        shapley[v] /= n_permutations

    return shapley


# ── 3. Defection Risk (Prisoner's Dilemma) ────────────────────────────────────

def defection_risk(conn):
    """
    Model vendor reliability as a repeated Prisoner's Dilemma.

    A vendor "defects" when they overrun, deliver late, or raise costs mid-show.
    Three signals feed the defection probability:

      utilization_risk  — vendor capacity strain → over-commitment → delivery risk
      payment_risk      — invoice accuracy gap → financial tension → renegotiation risk
      quality_risk      — edit_count / performance score → rework burden risk

    Defection probability P(defect) = weighted combination of three signals.
    Payoff framing (per shot):
      Cooperate / Cooperate  → studio saves, vendor earns fair margin
      Vendor defects          → studio absorbs overrun cost, vendor short-term gains
      Studio withholds        → both lose (disputes, litigation)

    Returns list of dicts:
    [{ vendor, utilization_risk, payment_risk, quality_risk, defection_prob,
       risk_label, shots_at_risk, estimated_overrun, recommendation }]
    """
    # Capacity utilization
    cap_rows = conn.execute(
        'SELECT vendor, shots_per_month, efficiency_pct FROM vendor_capacity'
    ).fetchall()
    cap_map = {}
    for r in cap_rows:
        eff = (r['shots_per_month'] or 100) * (r['efficiency_pct'] or 0.95)
        cap_map[r['vendor'].strip().upper()] = eff

    assigned_rows = conn.execute(
        "SELECT UPPER(award_vendor) as v, COUNT(*) as shots, AVG(COALESCE(edit_count,0)) as avg_edits "
        "FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!='' "
        "GROUP BY UPPER(award_vendor)"
    ).fetchall()
    assigned_map = {r['v']: {'shots': r['shots'], 'avg_edits': float(r['avg_edits'] or 0)}
                    for r in assigned_rows}

    # Invoice accuracy
    award_rows = conn.execute(
        "SELECT UPPER(vendor) as v, SUM(tot_award) as award FROM vendor_tracker "
        "WHERE vendor IS NOT NULL GROUP BY UPPER(vendor)"
    ).fetchall()
    paid_rows = conn.execute(
        "SELECT UPPER(vendor) as v, SUM(amount) as paid FROM invoice_log "
        "WHERE UPPER(status)='PAID' AND vendor IS NOT NULL GROUP BY UPPER(vendor)"
    ).fetchall()
    award_map = {r['v']: float(r['award'] or 0) for r in award_rows}
    paid_map  = {r['v']: float(r['paid']  or 0) for r in paid_rows}

    # Bid confidence (re-use CV formula for quality proxy)
    bid_rows = conn.execute('SELECT vendor_bids FROM bid_compare WHERE novfx=0').fetchall()
    buckets  = {}
    for r in bid_rows:
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
            for v, amt in raw.items():
                try:
                    buckets.setdefault(v.strip().upper(), []).append(float(amt))
                except (TypeError, ValueError):
                    pass
        except Exception:
            pass

    bid_conf = {}
    for vk, amounts in buckets.items():
        n = len(amounts)
        m, sd, _, _ = _stats(amounts)
        cv = (sd / m) if m else 1.0
        bid_conf[vk] = round(min(n / 30.0, 1.0) * max(0.0, 1.0 - cv), 3)

    # All vendors union
    all_keys = set(assigned_map) | set(award_map) | set(bid_conf)

    results = []
    for vk in all_keys:
        asgn   = assigned_map.get(vk, {})
        shots  = asgn.get('shots', 0)
        avg_ed = asgn.get('avg_edits', 0.0)
        cap    = cap_map.get(vk, 0)

        # --- Utilization risk (0=low, 1=high)
        if cap > 0:
            util = shots / cap
            util_risk = round(min(max((util - 0.5) / 0.5, 0.0), 1.0), 3)
        else:
            util_risk = 0.5 if shots > 0 else 0.0
            util = None

        # --- Payment risk: invoice gap as fraction of award
        award = award_map.get(vk, 0)
        paid  = paid_map.get(vk, 0)
        if award > 0:
            gap_frac  = abs(award - paid) / award
            pay_risk  = round(min(gap_frac, 1.0), 3)
        else:
            pay_risk  = 0.0

        # --- Quality risk: edit count and bid inconsistency
        edit_risk = round(min(avg_ed / 20.0, 1.0), 3)
        conf      = bid_conf.get(vk, 0.5)
        qual_risk = round((edit_risk * 0.6 + (1.0 - conf) * 0.4), 3)

        # --- Composite defection probability (weighted)
        defect_prob = round(util_risk * 0.45 + pay_risk * 0.30 + qual_risk * 0.25, 3)

        # --- Payoff framing: estimated overrun if defection occurs
        # Simple model: defection costs 15-35% overrun proportional to defect_prob
        overrun_rate  = 0.15 + defect_prob * 0.20
        avg_cost      = (sum(buckets.get(vk, [0])) / max(len(buckets.get(vk, [1])), 1))
        est_overrun   = round(shots * avg_cost * overrun_rate, 2)

        risk_label = ('HIGH' if defect_prob >= 0.55 else
                      ('MEDIUM' if defect_prob >= 0.30 else 'LOW'))

        if defect_prob >= 0.55:
            rec = 'Reduce allocation; build in contingency; tighten milestones.'
        elif defect_prob >= 0.30:
            rec = 'Monitor closely; negotiate delivery schedule guarantees.'
        else:
            rec = 'Stable — continue normal oversight.'

        # Resolve display name (original case from any table)
        display_name = vk
        for r in assigned_rows:
            if r['v'] == vk:
                display_name = conn.execute(
                    "SELECT award_vendor FROM shots WHERE UPPER(award_vendor)=? AND award_vendor IS NOT NULL LIMIT 1", (vk,)
                ).fetchone()
                if display_name:
                    display_name = display_name[0]
                break

        results.append({
            'vendor':           display_name if isinstance(display_name, str) else vk,
            'shots_assigned':   shots,
            'utilization':      round(util, 3) if util is not None else None,
            'utilization_risk': util_risk,
            'payment_risk':     pay_risk,
            'quality_risk':     qual_risk,
            'defection_prob':   defect_prob,
            'risk_label':       risk_label,
            'shots_at_risk':    shots,
            'estimated_overrun': est_overrun,
            'recommendation':   rec,
        })

    results.sort(key=lambda x: -x['defection_prob'])
    return results


# ── 4. Nash Equilibrium Allocation (Best-Response Iteration) ─────────────────

def nash_equilibrium_allocation(conn, max_iter=50):
    """
    Compute Nash Equilibrium vendor allocation via Best-Response Dynamics.

    Each vendor is a "player" whose strategy is: which scenes to bid competitively on.
    Best-Response: vendor i undercuts the current winner on any scene where they can
    profit (i.e., their expected cost is below the current winner's bid).

    Convergence: iterate until no vendor can profitably change assignment.

    Returns
    -------
    {
      assignments      { sc: { vendor, cost, prev_vendor, prev_cost, changed } }
      nash_total       float
      prev_total       float
      savings          float
      savings_pct      float
      iterations       int
      converged        bool
      changed_scenes   int
    }
    """
    scene_bids = _load_bid_matrix(conn)
    if not scene_bids:
        return {
            'assignments': {}, 'nash_total': 0.0, 'prev_total': 0.0,
            'savings': 0.0, 'savings_pct': 0.0, 'iterations': 0,
            'converged': True, 'changed_scenes': 0,
        }

    # Load current awards from shots table: sc -> vendor
    current_awards = {}
    for r in conn.execute(
        "SELECT scene_code, award_vendor FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!='' "
        "GROUP BY scene_code"
    ).fetchall():
        sc = str(r['scene_code'] or '').strip()
        if sc:
            current_awards[sc] = r['award_vendor']

    # Initial assignment: current award or lowest bidder
    assignment = {}
    for sc, bids in scene_bids.items():
        if current_awards.get(sc) and current_awards[sc] in bids:
            assignment[sc] = (current_awards[sc], bids[current_awards[sc]])
        else:
            best_v = min(bids, key=bids.get)
            assignment[sc] = (best_v, bids[best_v])

    # Compute current vendor loads for share-cap logic
    def vendor_loads():
        loads = {}
        for sc, (v, _) in assignment.items():
            loads[v] = loads.get(v, 0) + 1
        return loads

    total_scenes = len(assignment)
    converged = False
    iterations = 0

    for _ in range(max_iter):
        iterations += 1
        changed = False

        for sc, bids in scene_bids.items():
            cur_v, cur_cost = assignment[sc]
            # Find best-response: any vendor that can undercut?
            best_v, best_cost = cur_v, cur_cost
            for v, amt in bids.items():
                if v == cur_v:
                    continue
                # Best-response bid: undercut by small epsilon
                undercut = amt * 0.998   # 0.2% undercut threshold
                if undercut < best_cost:
                    best_v    = v
                    best_cost = undercut

            if best_v != cur_v:
                assignment[sc] = (best_v, round(best_cost, 2))
                changed = True

        if not changed:
            converged = True
            break

    # Build output
    prev_total = 0.0
    nash_total = 0.0
    out = {}
    changed_scenes = 0

    for sc, (nash_v, nash_cost) in assignment.items():
        prev_v = current_awards.get(sc, '')
        bids   = scene_bids.get(sc, {})
        prev_cost = bids.get(prev_v, 0.0) if prev_v else 0.0
        if not prev_cost:
            # Use lowest bid as baseline
            prev_cost = min(bids.values()) if bids else 0.0

        prev_total += prev_cost
        nash_total += nash_cost
        changed_here = (nash_v.upper() != prev_v.upper() if prev_v else bool(nash_v))
        if changed_here:
            changed_scenes += 1
        out[sc] = {
            'vendor':      nash_v,
            'cost':        nash_cost,
            'prev_vendor': prev_v,
            'prev_cost':   round(prev_cost, 2),
            'changed':     changed_here,
        }

    savings     = round(prev_total - nash_total, 2)
    savings_pct = round(savings / max(prev_total, 1) * 100.0, 2)

    return {
        'assignments':   out,
        'nash_total':    round(nash_total, 2),
        'prev_total':    round(prev_total, 2),
        'savings':       savings,
        'savings_pct':   savings_pct,
        'iterations':    iterations,
        'converged':     converged,
        'changed_scenes': changed_scenes,
        'total_scenes':  total_scenes,
    }


# ── 5. Repeated Game Memory ───────────────────────────────────────────────────

def repeated_game_memory(current_db_path=None):
    """
    Scan all registered projects (except the active one) for historical
    vendor overrun patterns and build a "reputation memory" per vendor.

    Repeated game theory: a vendor's past behaviour in previous seasons is
    the best predictor of future defection. Vendors who over-charged in S1
    are more likely to do so in S2 — the studio should price that risk in.

    Per historical project we compute:
      overrun_rate  = (total_paid - total_award) / total_award
        > 0  → vendor over-billed vs award  (risk: cost inflation)
        < 0  → vendor under-delivered/unpaid (risk: payment dispute)

    Returns
    -------
    {
      vendors: {
        vendor_upper: {
          display_name       str
          seasons_seen       int     # number of past projects with this vendor
          avg_overrun_rate   float   # mean overrun across seasons (+ = over-budget)
          max_overrun_rate   float   # worst single season
          history            [{ project_name, season, overrun_rate, award, paid }]
          memory_risk        float   # 0-1 score fed into defection_risk()
          memory_label       str     # CHRONIC / MODERATE / CLEAN
        }
      },
      projects_scanned  int,
      vendors_found     int,
    }
    """
    from services.db import PROJECTS_DB

    # Load all project db_paths from projects.db
    try:
        pconn = sqlite3.connect(PROJECTS_DB)
        pconn.row_factory = sqlite3.Row
        projects = pconn.execute(
            'SELECT name, season, db_path FROM projects ORDER BY id'
        ).fetchall()
        pconn.close()
    except Exception:
        return {'vendors': {}, 'projects_scanned': 0, 'vendors_found': 0}

    vendor_history = {}   # vendor_upper -> list of season records
    projects_scanned = 0

    for proj in projects:
        db_path = proj['db_path']
        if not db_path or not os.path.exists(db_path):
            continue
        if current_db_path and os.path.abspath(db_path) == os.path.abspath(current_db_path):
            continue  # skip active project

        try:
            hconn = sqlite3.connect(db_path)
            hconn.row_factory = sqlite3.Row

            # Per-vendor award totals
            award_rows = hconn.execute(
                "SELECT UPPER(vendor) as v, vendor, SUM(tot_award) as award "
                "FROM vendor_tracker WHERE vendor IS NOT NULL GROUP BY UPPER(vendor)"
            ).fetchall()

            # Per-vendor paid totals
            paid_rows = hconn.execute(
                "SELECT UPPER(vendor) as v, SUM(amount) as paid "
                "FROM invoice_log WHERE UPPER(status)='PAID' AND vendor IS NOT NULL "
                "GROUP BY UPPER(vendor)"
            ).fetchall()
            hconn.close()

            paid_map = {r['v']: float(r['paid'] or 0) for r in paid_rows}

            for r in award_rows:
                vk      = r['v']
                vname   = r['vendor']
                award   = float(r['award'] or 0)
                paid    = paid_map.get(vk, 0.0)

                if award <= 0:
                    continue

                overrun = round((paid - award) / award, 4)

                if vk not in vendor_history:
                    vendor_history[vk] = {'name': vname, 'records': []}

                vendor_history[vk]['records'].append({
                    'project_name': proj['name'],
                    'season':       proj['season'],
                    'overrun_rate': overrun,
                    'award':        round(award, 2),
                    'paid':         round(paid, 2),
                })

            projects_scanned += 1

        except Exception:
            continue

    # Aggregate per vendor
    result_vendors = {}
    for vk, data in vendor_history.items():
        records = data['records']
        rates   = [r['overrun_rate'] for r in records]
        n       = len(rates)
        avg_or  = round(sum(rates) / n, 4)
        max_or  = round(max(rates), 4)

        # memory_risk: chronic over-billing drives score toward 1.0
        # Scaled: >30% avg overrun = score 1.0; clean (<=2%) = 0.0
        raw_risk = min(max(avg_or, 0.0) / 0.30, 1.0)
        # Also penalise for consistency (many seasons over-budget)
        consistency = sum(1 for r in rates if r > 0.05) / max(n, 1)
        memory_risk = round(raw_risk * 0.70 + consistency * 0.30, 3)

        label = ('CHRONIC'  if memory_risk >= 0.55 else
                 ('MODERATE' if memory_risk >= 0.25 else 'CLEAN'))

        result_vendors[vk] = {
            'display_name':     data['name'],
            'seasons_seen':     n,
            'avg_overrun_rate': avg_or,
            'max_overrun_rate': max_or,
            'history':          records,
            'memory_risk':      memory_risk,
            'memory_label':     label,
        }

    return {
        'vendors':          result_vendors,
        'projects_scanned': projects_scanned,
        'vendors_found':    len(result_vendors),
    }


def defection_risk_with_memory(conn, current_db_path=None):
    """
    Extended defection_risk() that folds in repeated-game memory.

    Weights (when memory data is available):
      utilization_risk  0.35  (was 0.45)
      payment_risk      0.25  (was 0.30)
      quality_risk      0.20  (was 0.25)
      memory_risk       0.20  (new — historical overrun penalty)

    When no memory data exists for a vendor, falls back to original weights.
    """
    base_results = defection_risk(conn)
    memory       = repeated_game_memory(current_db_path=current_db_path)
    mem_vendors  = memory.get('vendors', {})

    enriched = []
    for row in base_results:
        vk  = row['vendor'].strip().upper()
        mem = mem_vendors.get(vk)

        if mem:
            mr = mem['memory_risk']
            # Re-compute defection probability with memory weight
            defect_prob = round(
                row['utilization_risk'] * 0.35 +
                row['payment_risk']     * 0.25 +
                row['quality_risk']     * 0.20 +
                mr                      * 0.20,
                3
            )
            risk_label = ('HIGH'   if defect_prob >= 0.55 else
                          ('MEDIUM' if defect_prob >= 0.30 else 'LOW'))
            if defect_prob >= 0.55:
                rec = 'History of overruns — reduce allocation; require milestone escrow.'
            elif defect_prob >= 0.30:
                rec = 'Moderate historical risk — negotiate penalties; track closely.'
            else:
                rec = 'Clean history — standard oversight.'

            row = dict(row)
            row['memory_risk']    = mr
            row['memory_label']   = mem['memory_label']
            row['seasons_seen']   = mem['seasons_seen']
            row['avg_overrun']    = mem['avg_overrun_rate']
            row['defection_prob'] = defect_prob
            row['risk_label']     = risk_label
            row['recommendation'] = rec
        else:
            row = dict(row)
            row['memory_risk']  = None
            row['memory_label'] = 'NO DATA'
            row['seasons_seen'] = 0
            row['avg_overrun']  = None

        enriched.append(row)

    enriched.sort(key=lambda x: -x['defection_prob'])
    return {
        'results':          enriched,
        'projects_scanned': memory['projects_scanned'],
        'vendors_with_memory': memory['vendors_found'],
    }


# ── 6. Coalition Blocking ─────────────────────────────────────────────────────

def coalition_blocking(conn, capacity_threshold=0.70, top_n=10):
    """
    Identify dangerous vendor pairs (or triples) where multiple CRITICAL
    vendors are simultaneously at high capacity utilisation.

    When two CRITICAL vendors are both overloaded, the studio loses bidding
    leverage on any scene only those vendors cover — the negotiating position
    collapses (no credible outside option).

    Algorithm:
      1. Compute Shapley values → rank vendors by criticality
      2. Compute utilisation → flag vendors above capacity_threshold
      3. For every pair of top-N vendors: compute cost impact if both are
         unavailable (simulate scene coverage from remaining vendors)
      4. Also compute the "leverage gap": scenes where ONLY this pair bids
         (no fallback vendor)

    Returns
    -------
    [
      {
        vendors          [str, str]        pair
        combined_shapley float             sum of pair Shapley savings
        both_at_risk     bool              both above capacity_threshold
        utilisation      { vendor: float }
        exclusive_scenes int               scenes only this pair covers
        cost_if_blocked  float             season cost without this pair
        cost_increase    float             delta vs full-vendor baseline
        cost_increase_pct float
        severity         str              CRITICAL / HIGH / MEDIUM
        recommendation   str
      }
    ]
    Sorted by cost_increase desc.
    """
    scene_bids = _load_bid_matrix(conn)
    if not scene_bids:
        return []

    # ── Shapley values ────────────────────────────────────────────────────
    all_vendors = set()
    for bids in scene_bids.values():
        all_vendors.update(bids.keys())
    all_vendors = sorted(all_vendors)

    if len(all_vendors) < 2:
        return []

    # Cap to top_n by coverage
    if len(all_vendors) > top_n:
        cov = {v: sum(1 for b in scene_bids.values() if v in b) for v in all_vendors}
        all_vendors = sorted(all_vendors, key=lambda v: -cov[v])[:top_n]

    if len(all_vendors) > 10:
        shapley_vals = _shapley_monte_carlo(scene_bids, all_vendors, n_permutations=400)
    else:
        shapley_vals = _shapley_exact(scene_bids, all_vendors)

    # ── Capacity utilisation ──────────────────────────────────────────────
    cap_rows = conn.execute(
        'SELECT vendor, shots_per_month, efficiency_pct FROM vendor_capacity'
    ).fetchall()
    cap_map = {}
    for r in cap_rows:
        eff = (r['shots_per_month'] or 100) * (r['efficiency_pct'] or 0.95)
        cap_map[r['vendor'].strip().upper()] = eff

    assigned_rows = conn.execute(
        "SELECT UPPER(award_vendor) as v, COUNT(*) as shots "
        "FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!='' "
        "GROUP BY UPPER(award_vendor)"
    ).fetchall()
    assigned_map = {r['v']: r['shots'] for r in assigned_rows}

    util_map = {}
    for v in all_vendors:
        vk  = v.upper()
        cap = cap_map.get(vk, 0)
        asgn = assigned_map.get(vk, 0)
        util_map[v] = round(asgn / cap, 3) if cap > 0 else None

    # ── Baseline season cost (all vendors) ───────────────────────────────
    baseline_cost, _ = _coalition_optimal_cost(scene_bids, all_vendors)

    # ── Enumerate pairs ───────────────────────────────────────────────────
    results = []
    for v1, v2 in combinations(all_vendors, 2):
        sv1  = shapley_vals.get(v1, 0.0)
        sv2  = shapley_vals.get(v2, 0.0)
        combined_sv = sv1 + sv2

        u1 = util_map.get(v1)
        u2 = util_map.get(v2)

        both_at_risk = (
            (u1 is not None and u1 >= capacity_threshold) and
            (u2 is not None and u2 >= capacity_threshold)
        )

        # Scenes exclusively covered by this pair (no other vendor bid)
        remaining = [v for v in all_vendors if v != v1 and v != v2]
        exclusive_sc = 0
        for sc, bids in scene_bids.items():
            has_v1 = v1 in bids
            has_v2 = v2 in bids
            has_other = any(v in bids for v in remaining)
            if (has_v1 or has_v2) and not has_other:
                exclusive_sc += 1

        # Cost if this pair is blocked
        blocked_cost, _ = _coalition_optimal_cost(scene_bids, remaining)
        cost_increase    = round(blocked_cost - baseline_cost, 2)
        cost_inc_pct     = round(cost_increase / max(baseline_cost, 1) * 100, 2)

        # Severity: driven by exclusivity + combined Shapley + both at risk
        if exclusive_sc > 0 and both_at_risk:
            severity = 'CRITICAL'
        elif cost_inc_pct >= 10.0 or (combined_sv > 0 and both_at_risk):
            severity = 'HIGH'
        elif cost_inc_pct >= 3.0 or exclusive_sc > 0:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        if severity == 'CRITICAL':
            rec = (f'Both {v1} & {v2} are at capacity AND exclusively cover '
                   f'{exclusive_sc} scene(s). Immediate capacity negotiation required.')
        elif severity == 'HIGH':
            rec = (f'Losing both vendors raises season cost by {cost_inc_pct:.1f}%. '
                   f'Secure at least one before bidding closes.')
        elif severity == 'MEDIUM':
            rec = 'Monitor capacity. Consider pre-qualifying a backup vendor.'
        else:
            rec = 'Low risk — adequate fallback coverage exists.'

        results.append({
            'vendors':            [v1, v2],
            'combined_shapley':   round(combined_sv, 2),
            'shapley_v1':         round(sv1, 2),
            'shapley_v2':         round(sv2, 2),
            'both_at_risk':       both_at_risk,
            'utilisation':        {v1: u1, v2: u2},
            'exclusive_scenes':   exclusive_sc,
            'cost_if_blocked':    round(blocked_cost, 2),
            'baseline_cost':      round(baseline_cost, 2),
            'cost_increase':      cost_increase,
            'cost_increase_pct':  cost_inc_pct,
            'severity':           severity,
            'recommendation':     rec,
        })

    # Sort: CRITICAL → HIGH → MEDIUM → by cost_increase
    sev_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    results.sort(key=lambda x: (sev_order.get(x['severity'], 9), -x['cost_increase']))

    # Return top meaningful results (skip pure LOWs beyond 20)
    filtered = [r for r in results if r['severity'] != 'LOW']
    if len(filtered) < 5:
        filtered = results[:20]
    return filtered[:30]


# ── 7. Auction Type Comparison (First-price vs Vickrey) ───────────────────────

def auction_type_comparison(conn, ep_filter=None):
    """
    Simulate three auction formats and compare total season cost:

      FIRST-PRICE (FPA)  — winner pays their own bid (current standard)
        Price per scene = lowest bid from competing vendors
        Strategy: vendors shade bids above true cost (NE markup included)

      SECOND-PRICE / VICKREY (SPA) — winner pays the second-lowest bid
        Price per scene = second-lowest bid
        Strategy: truthful bidding is dominant → bids reflect true cost
        Net effect: winner pays more than FPA winner, but bids less → depends on spread

      NEGOTIATED / BILATERAL — no competition; vendor knows they're sole bidder
        Price per scene = avg bid * premium (or highest bid if N=1)
        Represents: direct award without competitive process

    Revenue Equivalence Theorem (Myerson 1981): FPA ≈ SPA in expectation with
    symmetric risk-neutral bidders. In VFX practice, asymmetric vendors and
    information gaps break this symmetry — this simulation shows the real delta.

    Returns
    -------
    {
      fpa_total          float   # sum of lowest bids
      spa_total          float   # sum of second-lowest bids
      negotiated_total   float   # sum of no-competition prices
      fpa_vs_spa_delta   float   # SPA - FPA  (positive = SPA costlier)
      fpa_vs_neg_delta   float   # Negotiated - FPA
      scenes_where_spa_wins  int  # scenes where second-price is cheaper than first
      scenes_analysed    int
      ep_breakdown       { ep: { fpa, spa, negotiated, scenes } }
      scenes             [{ sc, ep, n_vendors, fpa_price, spa_price, neg_price,
                             spa_delta, spa_delta_pct, auction_winner }]
      insight            str   # plain-language summary
    }
    """
    rows = conn.execute(
        'SELECT sc, scount, vendor_bids, version, ep FROM bid_compare WHERE novfx=0'
        ' ORDER BY sc, version DESC'
    ).fetchall()

    seen_sc    = set()
    scene_data = []
    for r in rows:
        if ep_filter is not None and int(r['ep'] or 0) != ep_filter:
            continue
        sc = str(r['sc'] or '').strip()
        if not sc or sc in seen_sc:
            continue
        seen_sc.add(sc)
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        bids = {}
        for v, amt in raw.items():
            try:
                bids[v.strip()] = float(amt) / scount
            except (TypeError, ValueError):
                pass
        if bids:
            scene_data.append({'sc': sc, 'ep': int(r['ep'] or 0), 'bids': bids})

    if not scene_data:
        return {
            'fpa_total': 0.0, 'spa_total': 0.0, 'negotiated_total': 0.0,
            'fpa_vs_spa_delta': 0.0, 'fpa_vs_neg_delta': 0.0,
            'scenes_where_spa_wins': 0, 'scenes_analysed': 0,
            'ep_breakdown': {}, 'scenes': [], 'insight': 'No bid data.',
        }

    scenes_out     = []
    ep_agg         = {}
    spa_wins       = 0

    for sd in scene_data:
        sc    = sd['sc']
        ep    = sd['ep']
        bids  = sd['bids']
        n     = len(bids)

        sorted_vals = sorted(bids.values())
        lo_v        = min(bids, key=bids.get)

        # ── First-price: winner pays lowest bid
        fpa_price = round(sorted_vals[0], 2)

        # ── Second-price: winner pays second-lowest bid
        # If only one bidder, no competition → apply single-vendor premium
        if n >= 2:
            spa_price = round(sorted_vals[1], 2)
        else:
            spa_price = round(sorted_vals[0] * 1.08, 2)  # 8% single-vendor premium

        # ── Negotiated: no competitive pressure
        # Model as average bid + 10% for single-vendor negotiation premium
        avg_bid   = sum(bids.values()) / n
        if n == 1:
            neg_price = round(sorted_vals[0] * 1.15, 2)
        else:
            neg_price = round(avg_bid * 1.10, 2)

        spa_delta     = round(spa_price - fpa_price, 2)
        spa_delta_pct = round(spa_delta / max(fpa_price, 1) * 100, 2)
        if spa_price < fpa_price:
            spa_wins += 1

        scenes_out.append({
            'sc':           sc,
            'ep':           ep,
            'n_vendors':    n,
            'fpa_price':    fpa_price,
            'spa_price':    spa_price,
            'neg_price':    neg_price,
            'spa_delta':    spa_delta,
            'spa_delta_pct': spa_delta_pct,
            'auction_winner': lo_v,
        })

        if ep not in ep_agg:
            ep_agg[ep] = {'fpa': 0.0, 'spa': 0.0, 'negotiated': 0.0, 'scenes': 0}
        ep_agg[ep]['fpa']        += fpa_price
        ep_agg[ep]['spa']        += spa_price
        ep_agg[ep]['negotiated'] += neg_price
        ep_agg[ep]['scenes']     += 1

    for k in ep_agg:
        ep_agg[k] = {ek: round(ev, 2) if isinstance(ev, float) else ev
                     for ek, ev in ep_agg[k].items()}

    fpa_total        = round(sum(s['fpa_price'] for s in scenes_out), 2)
    spa_total        = round(sum(s['spa_price'] for s in scenes_out), 2)
    neg_total        = round(sum(s['neg_price']  for s in scenes_out), 2)
    fpa_vs_spa_delta = round(spa_total - fpa_total, 2)
    fpa_vs_neg_delta = round(neg_total - fpa_total, 2)

    # Plain-language insight
    spa_pct = round(abs(fpa_vs_spa_delta) / max(fpa_total, 1) * 100, 1)
    neg_pct = round(fpa_vs_neg_delta / max(fpa_total, 1) * 100, 1)
    if fpa_vs_spa_delta > 0:
        insight = (
            f"Vickrey (second-price) bidding would cost {spa_pct:.1f}% MORE than "
            f"your current first-price process (${fpa_vs_spa_delta:,.0f}). "
            f"Your vendors price competitively — the second bid is meaningfully higher. "
            f"Stick with FPA. Negotiated awards would cost {neg_pct:.1f}% more vs FPA."
        )
    else:
        insight = (
            f"Vickrey (second-price) bidding would cost {spa_pct:.1f}% LESS than "
            f"your current first-price process (${abs(fpa_vs_spa_delta):,.0f} saving). "
            f"Vendors are bidding close to each other — switching to SPA "
            f"could encourage more truthful, lower bids. "
            f"Negotiated awards would cost {neg_pct:.1f}% more vs FPA."
        )

    return {
        'fpa_total':           fpa_total,
        'spa_total':           spa_total,
        'negotiated_total':    neg_total,
        'fpa_vs_spa_delta':    fpa_vs_spa_delta,
        'fpa_vs_neg_delta':    fpa_vs_neg_delta,
        'scenes_where_spa_wins': spa_wins,
        'scenes_analysed':     len(scenes_out),
        'ep_breakdown':        ep_agg,
        'scenes':              scenes_out,
        'insight':             insight,
    }
