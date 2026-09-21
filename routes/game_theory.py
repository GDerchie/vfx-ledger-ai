"""
routes/game_theory.py — Game Theory Blueprint.

Endpoints:
  GET  /game_theory                          — page
  POST /api/game_theory/budget_forecast      — auction budget forecast (P10/P50/P90)
  GET  /api/game_theory/vendor_shapley       — Shapley value vendor assessment
  GET  /api/game_theory/defection_risk       — Prisoner's Dilemma defection risk
  GET  /api/game_theory/nash_allocation      — Nash Equilibrium allocation vs current
  GET  /api/game_theory/repeated_memory      — historical overrun memory across seasons
  GET  /api/game_theory/coalition_blocking   — Shapley × capacity collision detection
  POST /api/game_theory/auction_comparison   — First-price vs Vickrey (SPA) simulation
  POST /api/game_theory/mc/budget            — Monte Carlo budget distribution
  POST /api/game_theory/mc/defection         — Monte Carlo overrun simulation
  POST /api/game_theory/mc/frontier          — Monte Carlo efficient frontier
"""
from flask import Blueprint, render_template, request, jsonify, session
import core
from services.game_theory import (
    budget_game_forecast,
    shapley_vendor_assessment,
    defection_risk,
    defection_risk_with_memory,
    nash_equilibrium_allocation,
    repeated_game_memory,
    coalition_blocking,
    auction_type_comparison,
)

bp = Blueprint('game_theory', __name__)


@bp.route('/game_theory')
def game_theory_page():
    r = core.require_project()
    if r:
        return r
    return render_template('game_theory.html')


@bp.route('/api/game_theory/budget_forecast', methods=['POST'])
def api_budget_forecast():
    """
    Run auction-theory budget forecast.
    Body (optional): { ep: int }
    Returns P10 / P50 (Nash equilibrium) / P90 totals + per-scene breakdown.
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400
    d         = request.json or {}
    ep_filter = d.get('ep') or None
    if ep_filter is not None:
        try:
            ep_filter = int(ep_filter)
        except (TypeError, ValueError):
            ep_filter = None
    result = budget_game_forecast(conn, ep_filter=ep_filter)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/vendor_shapley', methods=['GET'])
def api_vendor_shapley():
    """
    Shapley value assessment — each vendor's marginal savings contribution.
    Query param: max_vendors (default 12)
    """
    conn = core.get_db()
    if not conn:
        return jsonify([])
    max_v = request.args.get('max_vendors', 12, type=int)
    result = shapley_vendor_assessment(conn, max_vendors=max_v)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/defection_risk', methods=['GET'])
def api_defection_risk():
    """
    Prisoner's Dilemma defection risk per vendor.
    Combines utilization strain, payment accuracy gap, and quality track record.
    """
    conn = core.get_db()
    if not conn:
        return jsonify([])
    result = defection_risk(conn)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/nash_allocation', methods=['GET'])
def api_nash_allocation():
    """
    Nash Equilibrium allocation via best-response iteration.
    Returns scene-level assignments, total cost vs. current, savings.
    Query param: max_iter (default 50)
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400
    max_iter = request.args.get('max_iter', 50, type=int)
    result   = nash_equilibrium_allocation(conn, max_iter=max_iter)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/repeated_memory', methods=['GET'])
def api_repeated_memory():
    """
    Repeated-game memory: scan all registered projects for historical
    vendor overrun patterns and return per-vendor reputation scores.
    Optionally enriches defection risk with memory signal.
    Query param: with_defection=1 — include full defection_risk_with_memory output
    """
    conn          = core.get_db()
    current_path  = session.get('project_db')
    with_defection = request.args.get('with_defection', '0') == '1'

    if with_defection:
        if not conn:
            return jsonify({'error': 'No project'}), 400
        result = defection_risk_with_memory(conn, current_db_path=current_path)
        if conn:
            conn.close()
        return jsonify(result)

    # Memory only — no active project required
    result = repeated_game_memory(current_db_path=current_path)
    if conn:
        conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/coalition_blocking', methods=['GET'])
def api_coalition_blocking():
    """
    Coalition blocking: identify vendor pairs where simultaneous capacity
    strain collapses studio negotiating leverage.
    Query params:
      capacity_threshold  float  default 0.70
      top_n               int    default 10
    """
    conn = core.get_db()
    if not conn:
        return jsonify([])
    threshold = request.args.get('capacity_threshold', 0.70, type=float)
    top_n     = request.args.get('top_n', 10, type=int)
    result    = coalition_blocking(conn, capacity_threshold=threshold, top_n=top_n)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/auction_comparison', methods=['POST'])
def api_auction_comparison():
    """
    Auction type comparison: First-price vs Second-price (Vickrey) vs Negotiated.
    Body (optional): { ep: int }
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400
    d         = request.json or {}
    ep_filter = d.get('ep') or None
    if ep_filter is not None:
        try:
            ep_filter = int(ep_filter)
        except (TypeError, ValueError):
            ep_filter = None
    result = auction_type_comparison(conn, ep_filter=ep_filter)
    conn.close()
    return jsonify(result)


# ── Monte Carlo endpoints ─────────────────────────────────────────────────────

@bp.route('/api/game_theory/mc/budget', methods=['POST'])
def api_mc_budget():
    """
    Monte Carlo season budget distribution.
    Body: { n_simulations: int (100–20000), ep: int|null, correlated: bool }

    Runs N trials sampling each vendor's bid from their empirical distribution,
    optionally with correlated Cholesky sampling.  Returns full distribution
    with P5–P95, VaR(95%), CVaR(95%), probability of overrun, and histogram.
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400

    from services.monte_carlo import budget_monte_carlo

    d            = request.json or {}
    n_sim        = max(100, min(int(d.get('n_simulations', 5000)), 20_000))
    ep_filter    = d.get('ep') or None
    correlated   = bool(d.get('correlated', True))

    if ep_filter is not None:
        try:
            ep_filter = int(ep_filter)
        except (TypeError, ValueError):
            ep_filter = None

    result = budget_monte_carlo(conn, n_simulations=n_sim,
                                ep_filter=ep_filter, correlated=correlated)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/mc/defection', methods=['POST'])
def api_mc_defection():
    """
    Monte Carlo vendor defection / overrun simulation.
    Body: { n_simulations: int (100–20000) }

    Each trial: each vendor defects with probability = their defection_prob,
    drawing an overrun cost proportional to their workload and utilisation risk.
    Returns total overrun distribution + per-vendor breakdown.
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400

    from services.monte_carlo import defection_monte_carlo

    d     = request.json or {}
    n_sim = max(100, min(int(d.get('n_simulations', 5000)), 20_000))

    result = defection_monte_carlo(conn, n_simulations=n_sim)
    conn.close()
    return jsonify(result)


@bp.route('/api/game_theory/mc/frontier', methods=['POST'])
def api_mc_frontier():
    """
    Monte Carlo efficient frontier: expected cost vs budget risk (std dev).
    Body: { n_simulations: int (100–5000) }

    Generates random vendor preference weight vectors, runs mini-MC for each,
    plots the Pareto-optimal cost/risk frontier.
    """
    conn = core.get_db()
    if not conn:
        return jsonify({'error': 'No project'}), 400

    from services.monte_carlo import portfolio_frontier

    d     = request.json or {}
    n_sim = max(100, min(int(d.get('n_simulations', 2000)), 5_000))

    result = portfolio_frontier(conn, n_simulations=n_sim)
    conn.close()
    return jsonify(result)
