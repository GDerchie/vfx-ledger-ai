"""routes/audit.py — Audit log Blueprint."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import core
import llm as llm_module
from services.llm_helpers import stream_llm

bp = Blueprint('audit', __name__)

@bp.route('/audit')
def audit_log():
    conn = core.get_db()
    if not conn:
        return redirect(url_for('projects.home'))
    table_filter = request.args.get('table', '')
    limit = min(int(request.args.get('limit', 200)), 1000)
    if table_filter:
        rows = conn.execute(
            'SELECT * FROM change_log WHERE table_name=? ORDER BY timestamp DESC LIMIT ?',
            (table_filter, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM change_log ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        ).fetchall()
    tables = [r[0] for r in conn.execute(
        'SELECT DISTINCT table_name FROM change_log ORDER BY table_name'
    ).fetchall()]
    conn.close()
    return render_template('audit.html',
                           rows=[dict(r) for r in rows],
                           tables=tables,
                           table_filter=table_filter,
                           limit=limit)

@bp.route('/api/audit')
def api_audit():
    conn = core.get_db()
    if not conn: return jsonify([])
    table_filter = request.args.get('table', '')
    limit  = min(int(request.args.get('limit', 200)), 1000)
    offset = int(request.args.get('offset', 0))
    if table_filter:
        rows = conn.execute(
            'SELECT * FROM change_log WHERE table_name=? ORDER BY timestamp DESC LIMIT ? OFFSET ?',
            (table_filter, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM change_log ORDER BY timestamp DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/llm/audit_explain', methods=['POST'])
def audit_explain():
    """
    Generate a plain-English explanation of audit log entries for a row.
    Streams the response.

    POST body: { table_name, row_id, limit (optional, default 10) }
    """
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    d          = request.json or {}
    table_name = d.get('table_name', '')
    row_id     = d.get('row_id')
    limit      = min(int(d.get('limit', 10)), 50)

    if not table_name or row_id is None:
        return jsonify({'error': 'table_name and row_id required'}), 400

    rows = conn.execute(
        'SELECT field, old_value, new_value, timestamp FROM change_log '
        'WHERE table_name=? AND row_id=? ORDER BY timestamp DESC LIMIT ?',
        (table_name, str(row_id), limit)
    ).fetchall()
    conn.close()

    if not rows:
        return jsonify({'error': 'No audit entries found for this row'}), 404

    # Build audit_entries text
    entries_text = '\n'.join(
        f"  [{r['timestamp']}] {r['field']}: {r['old_value']!r} → {r['new_value']!r}"
        for r in rows
    )
    timestamps = [r['timestamp'] for r in rows if r['timestamp']]
    time_range = f"{timestamps[-1]} to {timestamps[0]}" if len(timestamps) > 1 else (timestamps[0] if timestamps else 'unknown')

    ctx = {
        'table_name':    table_name,
        'row_id':        str(row_id),
        'audit_entries': entries_text,
        'user':          'production team',
        'time_range':    time_range,
    }
    prompt = llm_module.build_prompt('audit_explain', ctx)
    if not prompt:
        return jsonify({'error': 'prompt build failed'}), 400

    client = core.get_llm_client()
    return stream_llm(prompt, client,
                      cache_task='audit_explain',
                      cache_ctx={'table_name': table_name, 'row_id': str(row_id), 'n': str(len(rows))})
