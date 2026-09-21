"""routes/optimizer.py — Season Optimizer Blueprint."""
from flask import Blueprint, render_template, request, jsonify
import core

bp = Blueprint('optimizer', __name__)


@bp.route('/optimizer')
def optimizer_page():
    r = core.require_project()
    if r: return r
    return render_template('optimizer.html')


@bp.route('/api/optimizer/run', methods=['POST'])
def optimizer_run():
    """Run optimizer and return proposed assignments (read-only, no DB writes)."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    settings = request.json or {}
    result = core.run_season_optimizer(conn, settings)
    conn.close()
    return jsonify(result)


@bp.route('/api/optimizer/vendors')
def optimizer_vendors():
    """Return all vendors that appear in bid_compare — for preferred-vendor checklist."""
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute(
        'SELECT vendor_bids FROM bid_compare WHERE novfx=0'
    ).fetchall()
    import json
    seen = set()
    vendors = []
    for r in rows:
        try:
            bids = json.loads(r['vendor_bids'] or '{}')
            for v in bids:
                key = v.strip()
                if key and key.upper() not in seen:
                    seen.add(key.upper())
                    vendors.append(key)
        except Exception:
            pass
    conn.close()
    return jsonify(sorted(vendors))


@bp.route('/api/optimizer/apply', methods=['POST'])
def optimizer_apply():
    """Write optimizer assignments back to shots.award_vendor.

    Body: { assignments: {shot_id: vendor, ...} }
    Logs each change to change_log for audit trail.
    """
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d           = request.json or {}
    assignments = d.get('assignments', {})   # {str(shot_id): vendor}
    applied     = 0
    skipped     = 0

    for shot_id_str, vendor in assignments.items():
        try:
            shot_id = int(shot_id_str)
        except (ValueError, TypeError):
            skipped += 1
            continue
        old = conn.execute(
            'SELECT award_vendor FROM shots WHERE id=?', (shot_id,)
        ).fetchone()
        if not old:
            skipped += 1
            continue
        conn.execute(
            'UPDATE shots SET award_vendor=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
            (vendor, shot_id)
        )
        core.log_change(
            'shots', shot_id, 'award_vendor',
            old['award_vendor'] or '', vendor
        )
        applied += 1

    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'applied': applied, 'skipped': skipped})
