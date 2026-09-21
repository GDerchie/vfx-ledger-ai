"""
services/monte_carlo.py — Monte Carlo simulation engine for VFX budget risk.

Three simulation models:

  1. budget_monte_carlo()      — full season budget distribution (P5–P95, VaR, CVaR)
                                  with optional correlated vendor sampling
  2. defection_monte_carlo()   — overrun cost distribution under vendor defection
  3. portfolio_frontier()      — cost vs risk efficient frontier across allocations

Theory
------
Each vendor's per-shot cost is modelled as a random variable drawn from an
empirical distribution (mean and std derived from historical bid data).

In each simulation trial we:
  - Sample every bidding vendor's cost per scene from their distribution
  - Select the winner (minimum bid) per scene
  - Sum across scenes → one season budget realisation

Running N such trials gives the full budget distribution from which we extract
standard risk metrics used in financial VaR analysis.

Correlated sampling (optional):
  Vendor costs are not independent — market conditions, labour costs, and VFX
  demand shocks affect all vendors simultaneously. We estimate an empirical
  correlation matrix from bid data and apply Cholesky decomposition to generate
  correlated Gaussian samples.

All functions are read-only; no DB writes.
"""
import json
import math
import random


# ── Low-level math helpers ────────────────────────────────────────────────────

def _stats(vals):
    if not vals:
        return 0.0, 0.0
    n = len(vals)
    m = sum(vals) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / max(n - 1, 1)) if n > 1 else 0.0
    return m, sd


def _percentile(sorted_vals, p):
    """Percentile from a pre-sorted list (linear interpolation)."""
    if not sorted_vals:
        return 0.0
    n   = len(sorted_vals)
    idx = (n - 1) * p / 100.0
    lo  = int(idx)
    hi  = min(lo + 1, n - 1)
    return sorted_vals[lo] + (idx - lo) * (sorted_vals[hi] - sorted_vals[lo])


def _skewness(vals, mean, std):
    """Sample skewness (Fisher's definition)."""
    n = len(vals)
    if n < 3 or std < 1e-9:
        return 0.0
    s3 = sum(((x - mean) / std) ** 3 for x in vals)
    return s3 * n / ((n - 1) * (n - 2))


def _histogram(sorted_vals, n_buckets=30):
    """Build histogram as list of {lo, hi, count, pct}."""
    if not sorted_vals:
        return []
    lo  = _percentile(sorted_vals, 2)
    hi  = _percentile(sorted_vals, 98)
    if hi <= lo:
        hi = lo + 1.0
    width  = (hi - lo) / n_buckets
    counts = [0] * n_buckets
    n      = len(sorted_vals)
    for v in sorted_vals:
        idx = int((v - lo) / width)
        idx = max(0, min(n_buckets - 1, idx))
        counts[idx] += 1
    return [
        {
            'lo':    round(lo + i * width, 2),
            'hi':    round(lo + (i + 1) * width, 2),
            'mid':   round(lo + (i + 0.5) * width, 2),
            'count': counts[i],
            'pct':   round(counts[i] / max(n, 1) * 100, 2),
        }
        for i in range(n_buckets)
    ]


# ── Cholesky decomposition (pure Python) ─────────────────────────────────────

def _cholesky(matrix):
    """
    Lower-triangular Cholesky decomposition of a positive-definite matrix.
    Returns L such that L @ L.T = matrix.
    Falls back to identity if matrix is not positive definite.
    """
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    try:
        for i in range(n):
            for j in range(i + 1):
                s = sum(L[i][k] * L[j][k] for k in range(j))
                if i == j:
                    val = matrix[i][i] - s
                    if val < 1e-12:
                        raise ValueError('not positive definite')
                    L[i][j] = math.sqrt(val)
                else:
                    L[i][j] = (matrix[i][j] - s) / L[j][j]
    except (ValueError, ZeroDivisionError):
        # Fall back to identity (independent sampling)
        L = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    return L


def _correlated_sample(means, stds, chol, rng):
    """
    Generate one correlated Gaussian sample vector.
    z ~ N(0, I) → x = μ + L @ z * σ  (element-wise σ scaling)
    """
    n   = len(means)
    z   = [rng.gauss(0.0, 1.0) for _ in range(n)]
    # Lz = L @ z
    Lz  = [sum(chol[i][j] * z[j] for j in range(i + 1)) for i in range(n)]
    return [max(0.0, means[i] + stds[i] * Lz[i]) for i in range(n)]


# ── Data loading helpers ──────────────────────────────────────────────────────

def _load_scene_bid_data(conn, ep_filter=None):
    """
    Returns (scene_list, vendor_list, vendor_idx_map, bid_matrix)

    scene_list   [str]             — scene codes in order
    vendor_list  [str]             — all vendor names in order
    vendor_idx   {vendor: int}     — index into vendor_list
    bid_matrix   [[float|None]]    — bid_matrix[scene_idx][vendor_idx], None = no bid
    scene_eps    [int]             — ep per scene
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
        return [], [], {}, [], []

    # Collect all vendors
    all_vendors = set()
    for sd in scene_data:
        all_vendors.update(sd['bids'].keys())
    vendor_list = sorted(all_vendors)
    vendor_idx  = {v: i for i, v in enumerate(vendor_list)}

    n_scenes  = len(scene_data)
    n_vendors = len(vendor_list)

    bid_matrix = [[None] * n_vendors for _ in range(n_scenes)]
    scene_list = []
    scene_eps  = []

    for s_idx, sd in enumerate(scene_data):
        scene_list.append(sd['sc'])
        scene_eps.append(sd['ep'])
        for v, amt in sd['bids'].items():
            bid_matrix[s_idx][vendor_idx[v]] = amt

    return scene_list, vendor_list, vendor_idx, bid_matrix, scene_eps


def _vendor_distributions(conn, vendor_list):
    """
    Compute per-vendor bid distribution: {vendor: (mean, std)}.
    Uses per-shot bid amounts across all scenes.
    """
    rows = conn.execute(
        'SELECT vendor_bids, scount FROM bid_compare WHERE novfx=0'
    ).fetchall()
    buckets = {}
    for r in rows:
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        for v, amt in raw.items():
            try:
                buckets.setdefault(v.strip(), []).append(float(amt) / scount)
            except (TypeError, ValueError):
                pass

    dist = {}
    for v in vendor_list:
        amounts = buckets.get(v, [])
        if amounts:
            m, sd = _stats(amounts)
            # Minimum std = 5% of mean (prevents degenerate distributions)
            dist[v] = (m, max(sd, m * 0.05))
        else:
            dist[v] = (0.0, 0.0)
    return dist


def _empirical_correlation(bid_matrix, vendor_list, min_shared_scenes=3):
    """
    Compute empirical correlation matrix between vendors from normalised bid rows.

    For each scene where ≥2 vendors bid, we have a bid vector.
    We normalise within each row (subtract mean, divide by std) then compute
    pairwise Pearson correlation across all shared scenes.

    If a pair shares fewer than min_shared_scenes, correlation = 0 (independent).
    """
    n = len(vendor_list)
    if n < 2:
        return [[1.0]]

    # Collect normalised vectors per scene
    norm_rows = []
    for row in bid_matrix:
        vals = [v for v in row if v is not None]
        if len(vals) < 2:
            continue
        m  = sum(vals) / len(vals)
        sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
        if sd < 1e-9:
            continue
        norm_row = [(v - m) / sd if v is not None else None for v in row]
        norm_rows.append(norm_row)

    # Pairwise correlation
    corr = [[0.0] * n for _ in range(n)]
    for i in range(n):
        corr[i][i] = 1.0
        for j in range(i + 1, n):
            pairs = [
                (row[i], row[j])
                for row in norm_rows
                if row[i] is not None and row[j] is not None
            ]
            if len(pairs) < min_shared_scenes:
                c = 0.0
            else:
                xi = [p[0] for p in pairs]
                xj = [p[1] for p in pairs]
                mi, si = _stats(xi)
                mj, sj = _stats(xj)
                if si < 1e-9 or sj < 1e-9:
                    c = 0.0
                else:
                    k  = len(pairs)
                    c  = sum((xi[t] - mi) * (xj[t] - mj) for t in range(k)) / ((k - 1) * si * sj)
                    c  = max(-1.0, min(1.0, c))
            corr[i][j] = c
            corr[j][i] = c

    return corr


def _corr_to_cov(corr, stds):
    """Convert correlation matrix + std vector to covariance matrix."""
    n = len(stds)
    return [[corr[i][j] * stds[i] * stds[j] for j in range(n)] for i in range(n)]


# ── 1. Budget Monte Carlo ─────────────────────────────────────────────────────

def budget_monte_carlo(conn, n_simulations=10_000, ep_filter=None, correlated=True):
    """
    Simulate the season budget N times, sampling each vendor's bid from their
    empirical distribution.  Optionally applies correlated sampling via
    Cholesky decomposition of the empirical vendor correlation matrix.

    Returns
    -------
    {
      n_simulations       int
      correlated          bool
      current_budget      float    — deterministic baseline (sum of min bids)
      mean                float
      std                 float
      skewness            float
      p5, p10, p25, p50, p75, p90, p95  float
      var_95              float    — 95th percentile (Value at Risk)
      cvar_95             float    — Expected Shortfall above VaR(95%)
      prob_overrun        float    — P(season cost > current_budget)
      budget_cushion      float    — current_budget - mean (headroom)
      histogram           [{lo, hi, mid, count, pct}]
      ep_breakdown        {ep: {mean, p10, p90, current}}
      by_vendor           {vendor: {mean_cost, std_cost, share_pct}}
      correlation_matrix  [[float]]  — vendor × vendor (for heatmap)
      vendor_list         [str]
    }
    """
    scene_list, vendor_list, vendor_idx, bid_matrix, scene_eps = \
        _load_scene_bid_data(conn, ep_filter=ep_filter)

    if not scene_list:
        return _empty_budget_result(n_simulations)

    n_scenes  = len(scene_list)
    n_vendors = len(vendor_list)

    # ── Per-vendor distributions ────────────────────────────────────────
    dist = _vendor_distributions(conn, vendor_list)
    means_v = [dist[v][0] for v in vendor_list]
    stds_v  = [dist[v][1] for v in vendor_list]

    # ── Correlation + Cholesky ──────────────────────────────────────────
    if correlated and n_vendors >= 2:
        corr_mat = _empirical_correlation(bid_matrix, vendor_list)
        cov_mat  = _corr_to_cov(corr_mat, stds_v)
        chol     = _cholesky(cov_mat)
        # Re-extract per-vendor std from cov diagonal (Cholesky path uses cov)
        # stds already embedded in chol; we'll sample z ~ N(0,I) and apply L
        use_chol = True
    else:
        corr_mat = [[1.0 if i == j else 0.0 for j in range(n_vendors)]
                    for i in range(n_vendors)]
        chol     = [[max(stds_v[i], 1e-9) if i == j else 0.0 for j in range(n_vendors)]
                    for i in range(n_vendors)]
        use_chol = False

    # ── Deterministic baseline (current budget = sum of min bids) ──────
    current_budget = 0.0
    scene_min_bids = []  # current min bid per scene
    for row in bid_matrix:
        actuals = [v for v in row if v is not None]
        if actuals:
            lo = min(actuals)
            current_budget += lo
            scene_min_bids.append(lo)
        else:
            scene_min_bids.append(0.0)

    # ── Simulation loop ─────────────────────────────────────────────────
    rng      = random.Random(42)
    totals   = []
    ep_totals = {}   # ep -> [total_per_sim]
    vendor_costs = {v: [] for v in vendor_list}   # vendor -> [cost per sim]

    for _ in range(n_simulations):
        # Sample a correlated cost vector for all vendors this trial
        sampled_vendor_costs = _correlated_sample(means_v, stds_v, chol, rng)

        season_total = 0.0
        ep_sub       = {}

        for s_idx in range(n_scenes):
            row = bid_matrix[s_idx]
            ep  = scene_eps[s_idx]

            # Find competing vendors for this scene and get their sampled cost
            min_cost    = None
            winning_v   = None
            for v_idx, base_bid in enumerate(row):
                if base_bid is None:
                    continue
                # Scale global vendor sample to this scene's bid level
                v = vendor_list[v_idx]
                gm = means_v[v_idx]
                if gm > 0:
                    scale = base_bid / gm
                else:
                    scale = 1.0
                sampled = max(0.0, sampled_vendor_costs[v_idx] * scale)
                if min_cost is None or sampled < min_cost:
                    min_cost  = sampled
                    winning_v = v

            if min_cost is None:
                continue

            season_total += min_cost
            if winning_v:
                vendor_costs[winning_v].append(min_cost)

            ep_sub[ep] = ep_sub.get(ep, 0.0) + min_cost

        totals.append(season_total)
        for ep, val in ep_sub.items():
            ep_totals.setdefault(ep, []).append(val)

    # ── Aggregate results ───────────────────────────────────────────────
    totals.sort()
    n   = len(totals)
    m   = sum(totals) / n
    sd  = math.sqrt(sum((x - m) ** 2 for x in totals) / max(n - 1, 1))
    sk  = _skewness(totals, m, sd)

    p  = lambda q: _percentile(totals, q)
    var_95  = p(95)
    tail    = [x for x in totals if x > var_95]
    cvar_95 = sum(tail) / len(tail) if tail else var_95
    prob_ov = sum(1 for x in totals if x > current_budget) / n

    # EP breakdown
    ep_breakdown = {}
    for ep, vals in ep_totals.items():
        vals.sort()
        # Current EP cost (sum of min bids for that EP's scenes)
        ep_cur = sum(
            scene_min_bids[s_idx]
            for s_idx, ep2 in enumerate(scene_eps) if ep2 == ep
        )
        ep_breakdown[ep] = {
            'mean':    round(sum(vals) / len(vals), 2),
            'p10':     round(_percentile(vals, 10), 2),
            'p90':     round(_percentile(vals, 90), 2),
            'current': round(ep_cur, 2),
        }

    # By-vendor cost share
    by_vendor = {}
    for v in vendor_list:
        vc = vendor_costs[v]
        if vc:
            vm, vs = _stats(vc)
            by_vendor[v] = {
                'mean_cost': round(vm, 2),
                'std_cost':  round(vs, 2),
                'share_pct': round(sum(vc) / max(sum(totals), 1) * 100, 2),
                'win_count': len(vc),
            }

    return {
        'n_simulations':    n_simulations,
        'correlated':       use_chol,
        'current_budget':   round(current_budget, 2),
        'mean':             round(m, 2),
        'std':              round(sd, 2),
        'skewness':         round(sk, 3),
        'p5':               round(p(5),  2),
        'p10':              round(p(10), 2),
        'p25':              round(p(25), 2),
        'p50':              round(p(50), 2),
        'p75':              round(p(75), 2),
        'p90':              round(p(90), 2),
        'p95':              round(p(95), 2),
        'var_95':           round(var_95,  2),
        'cvar_95':          round(cvar_95, 2),
        'prob_overrun':     round(prob_ov, 4),
        'budget_cushion':   round(current_budget - m, 2),
        'histogram':        _histogram(totals),
        'ep_breakdown':     ep_breakdown,
        'by_vendor':        by_vendor,
        'correlation_matrix': [[round(c, 3) for c in row] for row in corr_mat],
        'vendor_list':      vendor_list,
        'scenes_modelled':  n_scenes,
    }


def _empty_budget_result(n_simulations):
    return {
        'n_simulations': n_simulations, 'correlated': False,
        'current_budget': 0.0, 'mean': 0.0, 'std': 0.0, 'skewness': 0.0,
        'p5': 0.0, 'p10': 0.0, 'p25': 0.0, 'p50': 0.0,
        'p75': 0.0, 'p90': 0.0, 'p95': 0.0,
        'var_95': 0.0, 'cvar_95': 0.0, 'prob_overrun': 0.0,
        'budget_cushion': 0.0, 'histogram': [], 'ep_breakdown': {},
        'by_vendor': {}, 'correlation_matrix': [], 'vendor_list': [],
        'scenes_modelled': 0,
    }


# ── 2. Defection Monte Carlo ──────────────────────────────────────────────────

def defection_monte_carlo(conn, n_simulations=10_000):
    """
    Simulate total season overrun cost under stochastic vendor defection.

    Each trial:
      For each vendor v with defection_prob p_v:
        defects_v ~ Bernoulli(p_v)
        if defects: overrun_v ~ U[overrun_lo, overrun_hi] × shots_v × avg_cost_v

    Overrun rate when defecting:
      - utilization_risk drives the magnitude: high util → larger overrun
      - base range: [10%, 40%] of vendor's total awarded cost

    Returns
    -------
    {
      n_simulations     int
      total: {
        mean, p50, p75, p90, p95, var_95, cvar_95,
        prob_any_defection,  — P(at least one vendor defects)
        prob_major_overrun,  — P(total overrun > 15% of season budget)
        worst_case,
      }
      per_vendor: [{
        vendor, defection_prob, shots_assigned, avg_cost,
        mean_overrun, p50_overrun, p90_overrun, p95_overrun,
        prob_defects,     — fraction of simulations where this vendor defected
      }]
      histogram: [{lo, hi, mid, count, pct}]
      season_budget: float
    }
    """
    from services.game_theory import defection_risk as _defect_risk

    # Load defection risk base data
    risk_rows = _defect_risk(conn)

    # Load season budget baseline
    bid_rows = conn.execute(
        'SELECT vendor_bids, scount FROM bid_compare WHERE novfx=0'
    ).fetchall()
    all_bids = []
    vendor_avg_cost = {}
    for r in bid_rows:
        try:
            raw = json.loads(r['vendor_bids'] or '{}')
        except Exception:
            raw = {}
        scount = max(int(r['scount'] or 1), 1)
        for v, amt in raw.items():
            try:
                per_shot = float(amt) / scount
                all_bids.append(per_shot)
                vendor_avg_cost.setdefault(v.strip().upper(), []).append(per_shot)
            except (TypeError, ValueError):
                pass

    # Average cost per shot per vendor
    v_avg = {vk: sum(vals) / len(vals) for vk, vals in vendor_avg_cost.items() if vals}
    season_budget = sum(all_bids) / max(len(all_bids), 1) * max(
        conn.execute("SELECT COUNT(*) FROM shots WHERE omit=0").fetchone()[0], 1
    ) if all_bids else 0.0

    if not risk_rows:
        return {
            'n_simulations': n_simulations,
            'total': {
                'mean': 0.0, 'p50': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0,
                'var_95': 0.0, 'cvar_95': 0.0,
                'prob_any_defection': 0.0, 'prob_major_overrun': 0.0, 'worst_case': 0.0,
            },
            'per_vendor': [], 'histogram': [], 'season_budget': season_budget,
        }

    rng = random.Random(42)

    # Per-vendor overrun parameters
    vendor_params = []
    for row in risk_rows:
        vk     = row['vendor'].strip().upper()
        p_def  = row['defection_prob']
        shots  = row.get('shots_assigned', 0) or 0
        avg_c  = v_avg.get(vk, 0.0)
        # Overrun range: proportional to utilization_risk
        util_r = row.get('utilization_risk', 0.0) or 0.0
        lo_r   = 0.10 + util_r * 0.10   # 10–20% overrun floor
        hi_r   = 0.25 + util_r * 0.30   # 25–55% overrun ceiling
        vendor_params.append({
            'vendor':   row['vendor'],
            'p_def':    p_def,
            'shots':    shots,
            'avg_cost': avg_c,
            'lo_r':     lo_r,
            'hi_r':     hi_r,
        })

    # Simulation loop
    total_overruns = []
    defection_counts = [0] * len(vendor_params)
    vendor_overrun_totals = [[] for _ in vendor_params]
    any_defect_count = 0

    for _ in range(n_simulations):
        trial_total  = 0.0
        any_defected = False

        for i, vp in enumerate(vendor_params):
            if vp['p_def'] <= 0 or vp['shots'] == 0:
                vendor_overrun_totals[i].append(0.0)
                continue

            defected = rng.random() < vp['p_def']
            if defected:
                defection_counts[i] += 1
                any_defected = True
                rate     = rng.uniform(vp['lo_r'], vp['hi_r'])
                overrun  = vp['shots'] * vp['avg_cost'] * rate
                trial_total += overrun
                vendor_overrun_totals[i].append(overrun)
            else:
                vendor_overrun_totals[i].append(0.0)

        total_overruns.append(trial_total)
        if any_defected:
            any_defect_count += 1

    total_overruns.sort()
    n   = len(total_overruns)
    tm  = sum(total_overruns) / n
    var_95  = _percentile(total_overruns, 95)
    tail    = [x for x in total_overruns if x > var_95]
    cvar_95 = sum(tail) / len(tail) if tail else var_95
    major_threshold = season_budget * 0.15
    prob_major = sum(1 for x in total_overruns if x > major_threshold) / n

    # Per-vendor summary
    per_vendor = []
    for i, vp in enumerate(vendor_params):
        ov = sorted(vendor_overrun_totals[i])
        per_vendor.append({
            'vendor':        vp['vendor'],
            'defection_prob': vp['p_def'],
            'shots_assigned': vp['shots'],
            'avg_cost':       round(vp['avg_cost'], 2),
            'mean_overrun':   round(sum(ov) / max(len(ov), 1), 2),
            'p50_overrun':    round(_percentile(ov, 50), 2),
            'p90_overrun':    round(_percentile(ov, 90), 2),
            'p95_overrun':    round(_percentile(ov, 95), 2),
            'prob_defects':   round(defection_counts[i] / n_simulations, 4),
        })
    per_vendor.sort(key=lambda x: -x['mean_overrun'])

    return {
        'n_simulations': n_simulations,
        'total': {
            'mean':                round(tm, 2),
            'p50':                 round(_percentile(total_overruns, 50), 2),
            'p75':                 round(_percentile(total_overruns, 75), 2),
            'p90':                 round(_percentile(total_overruns, 90), 2),
            'p95':                 round(_percentile(total_overruns, 95), 2),
            'var_95':              round(var_95,  2),
            'cvar_95':             round(cvar_95, 2),
            'prob_any_defection':  round(any_defect_count / n_simulations, 4),
            'prob_major_overrun':  round(prob_major, 4),
            'worst_case':          round(total_overruns[-1], 2),
        },
        'per_vendor':   per_vendor,
        'histogram':    _histogram(total_overruns),
        'season_budget': round(season_budget, 2),
    }


# ── 3. Portfolio Efficient Frontier ──────────────────────────────────────────

def portfolio_frontier(conn, n_simulations=3_000, n_frontier_points=12):
    """
    Monte Carlo efficient frontier: expected season cost vs budget risk (std dev).

    Method:
      - Generate n_frontier_points random vendor weight vectors (Dirichlet samples)
        each representing a preference for different vendor mixes
      - For each weight vector: run a mini Monte Carlo to get (mean_cost, std_cost)
      - Build the frontier: min std_cost at each cost level

    Each "weight vector" biases the winner-selection: in a scene, instead of
    always picking the minimum bid, we pick the vendor with probability
    proportional to (1 / (bid × weight_v)).  Higher weight → vendor preferred.

    This gives us the Pareto-optimal set of vendor preference policies.

    Returns
    -------
    {
      frontier: [{expected_cost, risk_std, vendor_weights, label}]
      all_points: [{expected_cost, risk_std}]
      min_cost_point: {expected_cost, risk_std, vendor_weights}
      min_risk_point: {expected_cost, risk_std, vendor_weights}
      vendor_list: [str]
    }
    """
    scene_list, vendor_list, vendor_idx, bid_matrix, scene_eps = \
        _load_scene_bid_data(conn)

    if not scene_list or not vendor_list:
        return {
            'frontier': [], 'all_points': [],
            'min_cost_point': None, 'min_risk_point': None,
            'vendor_list': [],
        }

    n_vendors = len(vendor_list)
    dist      = _vendor_distributions(conn, vendor_list)
    means_v   = [dist[v][0] for v in vendor_list]
    stds_v    = [dist[v][1] for v in vendor_list]

    rng = random.Random(42)

    def _simulate_with_weights(weights, n_trials):
        """Run mini MC with vendor preference weights. Returns (mean, std)."""
        trial_totals = []
        for _ in range(n_trials):
            total = 0.0
            for s_idx, row in enumerate(bid_matrix):
                eligible = [(v_idx, bid) for v_idx, bid in enumerate(row) if bid is not None]
                if not eligible:
                    continue
                # Sample bids
                sampled = []
                for v_idx, base_bid in eligible:
                    v  = vendor_list[v_idx]
                    gm = means_v[v_idx]
                    scale   = base_bid / gm if gm > 0 else 1.0
                    s_cost  = max(0.0, rng.gauss(means_v[v_idx], stds_v[v_idx]) * scale)
                    w       = max(weights[v_idx], 1e-9)
                    sampled.append((v_idx, s_cost, w))
                # Weighted selection: pick vendor with min (cost / weight)
                winner = min(sampled, key=lambda x: x[1] / x[2])
                total += winner[1]
            trial_totals.append(total)
        m  = sum(trial_totals) / len(trial_totals)
        sd = math.sqrt(sum((x - m) ** 2 for x in trial_totals) / max(len(trial_totals) - 1, 1))
        return m, sd

    # Equal-weight baseline
    equal_w = [1.0] * n_vendors
    base_m, base_sd = _simulate_with_weights(equal_w, n_simulations)

    # Generate random weight vectors + the equal-weight baseline
    all_points  = [{'expected_cost': round(base_m, 2), 'risk_std': round(base_sd, 2),
                    'weights': equal_w, 'label': 'Equal weight'}]

    n_random = 60  # sample 60 random policies
    for _ in range(n_random):
        # Dirichlet-like: gamma variables normalised
        gammas = [rng.expovariate(1.0) for _ in range(n_vendors)]
        s_g    = sum(gammas)
        weights = [g / s_g * n_vendors for g in gammas]  # scale so mean=1
        m, sd   = _simulate_with_weights(weights, max(n_simulations // 5, 200))
        all_points.append({'expected_cost': round(m, 2), 'risk_std': round(sd, 2),
                           'weights': [round(w, 3) for w in weights], 'label': ''})

    # Build efficient frontier: for each cost quantile, find min risk
    costs = sorted(set(p['expected_cost'] for p in all_points))
    n_pts = min(n_frontier_points, len(costs))
    step  = max(len(costs) // n_pts, 1)
    frontier = []
    seen_costs = set()
    for i in range(0, len(costs), step):
        c = costs[i]
        if c in seen_costs:
            continue
        seen_costs.add(c)
        candidates = [p for p in all_points if p['expected_cost'] <= c * 1.01]
        if not candidates:
            continue
        best = min(candidates, key=lambda p: p['risk_std'])
        frontier.append({
            'expected_cost': best['expected_cost'],
            'risk_std':      best['risk_std'],
            'vendor_weights': {vendor_list[i]: best['weights'][i]
                               for i in range(n_vendors)},
            'label':          best['label'],
        })

    frontier.sort(key=lambda x: x['expected_cost'])

    min_cost = min(all_points, key=lambda p: p['expected_cost'])
    min_risk = min(all_points, key=lambda p: p['risk_std'])

    def _enrich(p):
        return {
            'expected_cost': p['expected_cost'],
            'risk_std':      p['risk_std'],
            'vendor_weights': {vendor_list[i]: p['weights'][i] for i in range(n_vendors)},
        }

    return {
        'frontier':       frontier,
        'all_points':     [{'expected_cost': p['expected_cost'], 'risk_std': p['risk_std']}
                           for p in all_points],
        'min_cost_point': _enrich(min_cost),
        'min_risk_point': _enrich(min_risk),
        'vendor_list':    vendor_list,
        'baseline':       {'expected_cost': round(base_m, 2), 'risk_std': round(base_sd, 2)},
    }
