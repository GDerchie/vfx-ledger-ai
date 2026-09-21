"""routes/notes.py — VFX Notes Blueprint."""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
import core
import llm as llm_module
from services.llm_helpers import complete_json

bp = Blueprint('notes', __name__)


@bp.route('/notes')
def notes_page():
    r = core.require_project()
    if r: return r
    return render_template('notes.html')


@bp.route('/api/notes', methods=['GET'])
def get_notes():
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute('SELECT * FROM vfx_notes ORDER BY item_num').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/notes', methods=['POST'])
def add_note():
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json; c = conn.cursor()
    max_item = conn.execute('SELECT COALESCE(MAX(item_num),0) FROM vfx_notes').fetchone()[0]
    c.execute('INSERT INTO vfx_notes (item_num, author, note_text, note_date, resolved) VALUES (?,?,?,?,?)',
              (max_item + 1, d.get('author', ''), d.get('note_text', ''),
               d.get('note_date', datetime.now().strftime('%Y-%m-%d')), d.get('resolved', 0)))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['author', 'note_text', 'note_date', 'resolved']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE vfx_notes SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [note_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM vfx_notes WHERE id=?', (note_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@bp.route('/api/llm/notes_summarize', methods=['POST'])
def notes_summarize():
    """Summarize all VFX notes and return prioritized action list."""
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    rows = conn.execute('SELECT * FROM vfx_notes ORDER BY item_num').fetchall()
    conn.close()

    if not rows:
        return jsonify({'error': 'No notes to summarize'}), 404

    unresolved = [r for r in rows if not r['resolved']]
    notes_text = '\n'.join(
        f"  [{r['item_num']}] {'[RESOLVED] ' if r['resolved'] else ''}"
        f"{r['note_date'] or ''} — {r['note_text'] or ''}"
        for r in rows
    )

    ctx = {
        'project':         session.get('project_name', 'Unknown'),
        'season':          session.get('project_season', ''),
        'total_count':     len(rows),
        'unresolved_count': len(unresolved),
        'notes_text':      notes_text,
    }
    prompt = llm_module.build_prompt('notes_summarize', ctx)
    if not prompt:
        return jsonify({'error': 'prompt build failed'}), 400

    client = core.get_llm_client()
    result = complete_json(prompt, client,
                           cache_task='notes_summarize',
                           cache_ctx={'n': str(len(rows))})
    if result is None:
        return jsonify({'error': 'LLM unavailable'}), 503
    result['unresolved_count'] = len(unresolved)
    return jsonify(result)
