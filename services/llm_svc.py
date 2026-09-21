"""
services/llm_svc.py — LLM client helpers and cost actuals.
"""
import llm as llm_module
from services.db import BASE_DIR

_llm_client = None


def get_llm_client():
    global _llm_client
    if _llm_client is None:
        cfg = llm_module.load_config(BASE_DIR)
        _llm_client = llm_module.LLMClient(cfg)
    return _llm_client


def reset_llm_client():
    global _llm_client
    _llm_client = None


def get_cost_actuals(conn, shot_type=None, complexity=None, award_vendor=None):
    """Build historical cost context for LLM cost estimation.

    Uses shots.efc (expected final cost) when > 0 as the project "actual";
    falls back to shots.cost_est for shots not yet EFC'd.
    Returns a formatted string ready to inject into the cost_est prompt.
    """
    def _stats(where_clause, params):
        row = conn.execute(f'''
            SELECT COUNT(*) AS n,
                   AVG(CASE WHEN efc > 0 THEN efc ELSE cost_est END) AS avg_cost,
                   MIN(CASE WHEN efc > 0 THEN efc ELSE cost_est END) AS min_cost,
                   MAX(CASE WHEN efc > 0 THEN efc ELSE cost_est END) AS max_cost
            FROM shots
            WHERE omit=0 AND (efc > 0 OR cost_est > 0)
              AND {where_clause}
        ''', params).fetchone()
        return row if (row and row['n'] and row['n'] >= 2) else None

    lines = []

    if shot_type:
        r = _stats('UPPER(shot_type)=UPPER(?)', (shot_type,))
        if r:
            lines.append(
                f"All {shot_type} shots this project: "
                f"n={r['n']}, avg=${r['avg_cost']:,.0f}, "
                f"range ${r['min_cost']:,.0f}–${r['max_cost']:,.0f}"
            )

    if shot_type and complexity:
        r = _stats('UPPER(shot_type)=UPPER(?) AND UPPER(complexity)=UPPER(?)',
                   (shot_type, complexity))
        if r:
            lines.append(
                f"{shot_type} / {complexity}: "
                f"n={r['n']}, avg=${r['avg_cost']:,.0f}, "
                f"range ${r['min_cost']:,.0f}–${r['max_cost']:,.0f}"
            )

    if shot_type and award_vendor:
        r = _stats('UPPER(shot_type)=UPPER(?) AND UPPER(award_vendor)=UPPER(?)',
                   (shot_type, award_vendor))
        if r:
            lines.append(
                f"{award_vendor} avg for {shot_type}: "
                f"${r['avg_cost']:,.0f} ({r['n']} shots)"
            )

    if not lines:
        return ""

    return "Project actuals (use to calibrate estimate):\n" + \
           "\n".join(f"  • {l}" for l in lines)
