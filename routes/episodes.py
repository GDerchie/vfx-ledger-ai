"""routes/episodes.py — Episode, shots, sequences, distribution Blueprint."""
import io
import json
import os
import re
import string
from collections import Counter
from datetime import datetime
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, session, Response, stream_with_context, send_file)
import core

bp = Blueprint('episodes', __name__)


# ── Page routes ─────────────────────────────────────────────────────────────

@bp.route('/distribution')
def distribution():
    r = core.require_project()
    if r: return r
    return render_template('distribution.html')


@bp.route('/ep/<int:ep_num>')
def ep_page(ep_num):
    r = core.require_project()
    if r: return r
    return render_template('ep.html', ep_num=ep_num)


# ── API – episodes list (nav) ────────────────────────────────────────────────

@bp.route('/api/episodes')
def get_episodes_list():
    return jsonify(core.get_episodes())


# ── API – shots ──────────────────────────────────────────────────────────────

@bp.route('/api/shots/<int:ep>', methods=['GET'])
def get_shots(ep):
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute(
        'SELECT * FROM shots WHERE ep=? ORDER BY shot_num, id', (ep,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['budget_est'] = (d.get('cost_est') or 0) * (d.get('shot_est') or 0)
        result.append(d)
    return jsonify(result)


@bp.route('/api/shots', methods=['POST'])
def create_shot():
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO shots
        (ep, shot_num, scene_code, s_code, location, ext_int, pg, img, asset,
         script_desc, vfx_desc, shot_type, omit, history_notes, shot_est,
         cost_est, budget_est, award_vendor, edit_count, budget_award_cost, efc, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d.get('ep'), d.get('shot_num'), d.get('scene_code'), d.get('s_code'),
         d.get('location'), d.get('ext_int'), d.get('pg'), d.get('img'), d.get('asset'),
         d.get('script_desc'), d.get('vfx_desc'), d.get('shot_type'), d.get('omit', 0),
         d.get('history_notes'), d.get('shot_est', 1), d.get('cost_est', 0),
         d.get('budget_est', 0), d.get('award_vendor'), d.get('edit_count', 0),
         d.get('budget_award_cost', 0), d.get('efc', 0), d.get('notes')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@bp.route('/api/shots/<int:shot_id>', methods=['PUT'])
def update_shot(shot_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['shot_num', 'scene_code', 's_code', 'location', 'ext_int', 'pg',
               'img', 'asset', 'script_desc', 'vfx_desc', 'shot_type', 'omit',
               'complexity', 'history_notes', 'shot_est', 'cost_est', 'budget_est',
               'award_vendor', 'edit_count', 'budget_award_cost', 'efc', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    for f in ('cost_est', 'budget_est', 'budget_award_cost', 'efc'):
        if f in updates:
            cleaned = core.clean_cost(updates[f])
            if cleaned is None:
                return jsonify({'error': f'Value for {f} exceeds maximum allowed (${core._MAX_COST:,.0f})'}), 400
            updates[f] = cleaned
    fin_fields = {'cost_est', 'efc', 'award_vendor', 'status'}
    old_row = conn.execute('SELECT * FROM shots WHERE id=?', (shot_id,)).fetchone()
    for f in fin_fields:
        if f in updates and old_row and str(old_row[f]) != str(updates[f]):
            core.log_change('shots', shot_id, f, old_row[f], updates[f])
    if old_row and 'efc' in updates:
        est = old_row['cost_est'] or 0
        new_efc = updates['efc']
        alert_threshold = core.get_project_setting('efc_alert_threshold', 1.2)
        if est > 0 and new_efc > est * alert_threshold:
            core.slack_alert(
                f'[VFX Budget] EFC exceeds EST\u00d71.2 \u2014 Shot {shot_id} EP{old_row["ep"]} '
                f'SC {old_row["scene_code"]}: EFC ${new_efc:,.0f} vs EST ${est:,.0f}'
            )
    updates['updated_at'] = datetime.now().isoformat()
    sql = 'UPDATE shots SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
    conn.execute(sql, list(updates.values()) + [shot_id])
    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'status': 'ok'})


@bp.route('/api/shots/<int:shot_id>', methods=['DELETE'])
def delete_shot(shot_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM shots WHERE id=?', (shot_id,))
    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'status': 'ok'})


@bp.route('/api/shots/bulk', methods=['PUT'])
def bulk_update_shots():
    data  = request.json
    ids   = data.get('ids', [])
    field = data.get('field')
    value = data.get('value')
    ALLOWED = {'status', 'vendor', 'complexity', 'omit'}
    if not ids or field not in ALLOWED:
        return jsonify({'error': 'invalid'}), 400
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.executemany(f'UPDATE shots SET {field}=? WHERE id=?', [(value, i) for i in ids])
    conn.commit()
    conn.close()
    core.cache.clear()
    return jsonify({'updated': len(ids)})


@bp.route('/api/shots/<int:shot_id>/history')
def shot_history(shot_id):
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute(
        'SELECT * FROM change_log WHERE table_name="shots" AND row_id=? ORDER BY timestamp DESC LIMIT 20',
        (shot_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/shots/suggest')
def shots_suggest():
    conn = core.get_db()
    if not conn: return jsonify({})
    location   = (request.args.get('location') or '').strip()
    exclude_id = request.args.get('exclude_id', type=int)
    if not location or len(location) < 3:
        conn.close()
        return jsonify({})
    tokens = [t for t in re.split(r'[\s\.\-/,]+', location.upper())
              if len(t) >= 4 and t not in ('CONT','CONTINUOUS','NIGHT','DAY','DUSK','DAWN')]
    if not tokens:
        conn.close()
        return jsonify({})
    like_clauses = ' OR '.join(['UPPER(location) LIKE ?' for _ in tokens])
    params = ['%' + t + '%' for t in tokens]
    base_q = f'SELECT shot_type, complexity, award_vendor, cost_est, scene_code, ep FROM shots WHERE omit=0 AND ({like_clauses})'
    if exclude_id:
        base_q += ' AND id != ?'
        params.append(exclude_id)
    rows = conn.execute(base_q, params).fetchall()
    if not rows:
        conn.close()
        return jsonify({'matches': 0})
    types        = Counter(r['shot_type']    for r in rows if r['shot_type'])
    complexities = Counter(r['complexity']   for r in rows if r['complexity'])
    vendors      = Counter(r['award_vendor'] for r in rows if r['award_vendor'])
    costs        = [r['cost_est'] for r in rows if r['cost_est'] and r['cost_est'] > 0]
    scene_codes  = list({r['scene_code'] for r in rows if r['scene_code']})
    assets = []
    if scene_codes:
        placeholders = ','.join(['?' for _ in scene_codes])
        asset_rows = conn.execute(
            f'SELECT asset_name, asset_type, ep FROM assets WHERE scene_code IN ({placeholders}) AND omit=0',
            scene_codes
        ).fetchall()
        seen_assets = set()
        for a in asset_rows:
            key = a['asset_name']
            if key and key not in seen_assets:
                seen_assets.add(key)
                assets.append({'asset_name': a['asset_name'], 'asset_type': a['asset_type'] or '', 'ep': a['ep']})
    conn.close()
    avg_cost = round(sum(costs) / len(costs), 0) if costs else 0
    return jsonify({
        'matches':    len(rows),
        'shot_type':  types.most_common(3),
        'complexity': complexities.most_common(3),
        'vendor':     vendors.most_common(3),
        'cost_avg':   avg_cost,
        'cost_min':   round(min(costs), 0) if costs else 0,
        'cost_max':   round(max(costs), 0) if costs else 0,
        'assets':     assets[:6],
        'top_shot_type':  types.most_common(1)[0][0]       if types        else '',
        'top_complexity': complexities.most_common(1)[0][0] if complexities else '',
        'top_vendor':     vendors.most_common(1)[0][0]     if vendors      else '',
    })


@bp.route('/api/shots/scene_counts')
def shots_scene_counts():
    conn = core.get_db()
    if not conn: return jsonify({})
    ep = request.args.get('ep', type=int)
    q, params = 'SELECT scene_code, COUNT(*) as cnt FROM shots WHERE omit=0', []
    if ep:
        q += ' AND ep=?'; params.append(ep)
    q += ' GROUP BY scene_code'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify({r['scene_code']: r['cnt'] for r in rows if r['scene_code']})


@bp.route('/api/shots/duplicates')
def shots_duplicates():
    """Return groups of non-omitted shots sharing the same scene_code+shot_num."""
    conn = core.get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    params = []
    q = '''
        SELECT ep, scene_code, shot_num,
               COUNT(*) AS count,
               GROUP_CONCAT(id) AS ids
        FROM shots WHERE omit=0
    '''
    if ep:
        q += ' AND ep=?'; params.append(ep)
    q += ' GROUP BY ep, scene_code, shot_num HAVING COUNT(*) > 1 ORDER BY ep, scene_code'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── API – ep_meta ────────────────────────────────────────────────────────────

@bp.route('/api/ep_meta/<int:ep>', methods=['GET'])
def get_ep_meta(ep):
    conn = core.get_db()
    if not conn: return jsonify({})
    row = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
    conn.close()
    return jsonify(dict(row) if row else {})


@bp.route('/api/ep_meta/<int:ep>', methods=['PUT'])
def update_ep_meta(ep):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['script_v', 'edit_v', 'status', 'est_reduction', 'reduction_notes', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE ep_meta SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE ep=?'
        conn.execute(sql, list(updates.values()) + [ep])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ── API – distribution ───────────────────────────────────────────────────────

@bp.route('/api/distribution', methods=['GET'])
def get_distribution():
    conn = core.get_db()
    if not conn: return jsonify([])
    cache_key = 'dist_' + (session.get('project_db') or '')
    cached = core.cache.get(cache_key)
    if cached is not None:
        conn.close()
        return jsonify(cached)
    result = []
    for ep in core.get_episodes():
        agg = conn.execute('''
            SELECT
                COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
                SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS edit_shots,
                SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)  ELSE 0 END)  AS est_budget,
                SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)       ELSE 0 END)  AS efc_budget
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        meta = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        asset_agg = conn.execute('''
            SELECT
                SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0)    ELSE 0 END) AS asset_est,
                SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0)  ELSE 0 END) AS asset_actual
            FROM assets WHERE ep=?''', (ep,)).fetchone()
        shot_est  = agg['est_budget'] or 0
        shot_efc  = agg['efc_budget'] or 0
        asset_est = (asset_agg['asset_est']    or 0) if asset_agg else 0
        asset_efc = (asset_agg['asset_actual'] or 0) if asset_agg else 0
        combined_est = shot_est + asset_est
        combined_efc = shot_efc + asset_efc
        risk_shots = conn.execute(
            'SELECT shot_type, complexity, cost_est, efc FROM shots WHERE ep=? AND omit=0', (ep,)
        ).fetchall()
        total_s = len(risk_shots)
        heavy_types = {'CG','CREATURE','CROWD','FX','EXTENSION'}
        hero_high = sum(1 for s in risk_shots if
            (s['shot_type'] or '').upper() in heavy_types or
            (s['complexity'] or '').upper() in ('HERO','HIGH'))
        complexity_risk = hero_high / total_s if total_s else 0
        budget_risk = max(0, min(1, (combined_efc - combined_est) / max(combined_est, 1)))
        risk_score = round(0.55 * complexity_risk + 0.45 * budget_risk, 3)
        if risk_score < 0.2:    risk_label, risk_cls = 'SAFE',      'safe'
        elif risk_score < 0.45: risk_label, risk_cls = 'WATCH',     'watch'
        elif risk_score < 0.70: risk_label, risk_cls = 'AT RISK',   'atrisk'
        else:                   risk_label, risk_cls = 'HIGH RISK', 'highrisk'
        result.append({
            'ep':              ep,
            'script_v':        meta['script_v']        if meta else '',
            'edit_v':          meta['edit_v']          if meta else '',
            'est_shots':       agg['est_shots']        or 0,
            'edit_shots':      agg['edit_shots']       or 0,
            'shot_est':        shot_est,
            'shot_efc':        shot_efc,
            'asset_est':       asset_est,
            'asset_efc':       asset_efc,
            'est_budget':      combined_est,
            'efc_budget':      combined_efc,
            'variance':        combined_efc - combined_est,
            'status':          meta['status']          if meta else '',
            'est_reduction':   meta['est_reduction']   if meta else 0,
            'reduction_notes': meta['reduction_notes'] if meta else '',
            'notes':           meta['notes']           if meta else '',
            'risk_score':      risk_score,
            'risk_label':      risk_label,
            'risk_cls':        risk_cls,
        })
    conn.close()
    core.cache.set(cache_key, result, timeout=30)
    return jsonify(result)


# ── API – sequences ──────────────────────────────────────────────────────────

@bp.route('/api/sequences', methods=['GET'])
def get_sequences():
    conn = core.get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    if ep:
        rows = conn.execute('SELECT * FROM sequences WHERE ep=? ORDER BY id', (ep,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM sequences ORDER BY ep, id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/sequences', methods=['POST'])
def create_sequence():
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO sequences
        (ep, seq_name, location, omit, est_shots, current_cut, lbudget,
         efc, variance_val, status, est_reductions, est_ctd, turnover_deadline, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d.get('ep'), d.get('seq_name'), d.get('location'), d.get('omit', 0),
         d.get('est_shots', 0), d.get('current_cut', 0), d.get('lbudget', 0),
         d.get('efc', 0), d.get('variance_val', 0), d.get('status'),
         d.get('est_reductions'), d.get('est_ctd', 0), d.get('turnover_deadline'), d.get('notes')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@bp.route('/api/sequences/<int:seq_id>', methods=['PUT'])
def update_sequence(seq_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['seq_name', 'location', 'omit', 'est_shots', 'current_cut', 'lbudget',
               'efc', 'variance_val', 'status', 'est_reductions', 'est_ctd',
               'turnover_deadline', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE sequences SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [seq_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@bp.route('/api/sequences/aggregate/<int:ep>', methods=['GET'])
def aggregate_sequences(ep):
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute('''
        SELECT
            COALESCE(NULLIF(scene_code,''), '?')       AS scene_code,
            COALESCE(NULLIF(location,''), '(no loc)')  AS location,
            COUNT(CASE WHEN omit=0 THEN 1 END)                              AS est_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END)   AS current_cut,
            SUM(CASE WHEN omit=0 THEN COALESCE(budget_est,0) ELSE 0 END)   AS lbudget,
            SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)   ELSE 0 END)   AS cost_total,
            SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)        ELSE 0 END)   AS efc
        FROM shots WHERE ep=?
        GROUP BY scene_code, location
        ORDER BY CAST(scene_code AS REAL), location
    ''', (ep,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        efc = r['efc'] or 0; lbudget = r['lbudget'] or 0
        result.append({'ep': ep, 'seq_name': r['scene_code'], 'location': r['location'],
                       'est_shots': r['est_shots'] or 0, 'current_cut': r['current_cut'] or 0,
                       'lbudget': lbudget, 'efc': efc, 'variance_val': efc - lbudget,
                       'cost_total': r['cost_total'] or 0})
    return jsonify(result)


@bp.route('/api/sequences/sync', methods=['POST'])
def sync_sequences():
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    eps = d.get('eps', []); mode = d.get('mode', 'replace'); inserted = 0
    for ep in eps:
        agg_rows = conn.execute('''
            SELECT COALESCE(NULLIF(scene_code,''), '?') AS scene_code,
                   COALESCE(NULLIF(location,''), '(no loc)') AS location,
                   COUNT(CASE WHEN omit=0 THEN 1 END) AS est_shots,
                   SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS current_cut,
                   SUM(CASE WHEN omit=0 THEN COALESCE(budget_est,0) ELSE 0 END) AS lbudget,
                   SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)   ELSE 0 END) AS cost_total,
                   SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)        ELSE 0 END) AS efc
            FROM shots WHERE ep=?
            GROUP BY scene_code, location ORDER BY CAST(scene_code AS REAL), location
        ''', (ep,)).fetchall()
        if mode == 'replace':
            conn.execute('DELETE FROM sequences WHERE ep=? AND auto_sync=1', (ep,))
        for r in agg_rows:
            efc = r['efc'] or 0; lbudget = r['lbudget'] or 0
            conn.execute('''INSERT INTO sequences
                (ep, seq_name, location, omit, est_shots, current_cut, lbudget, efc, variance_val, status, auto_sync)
                VALUES (?,?,?,0,?,?,?,?,?,?,1)''',
                (ep, r['scene_code'], r['location'], r['est_shots'] or 0,
                 r['current_cut'] or 0, lbudget, efc, efc - lbudget, ''))
            inserted += 1
    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted, 'eps': eps})


@bp.route('/api/sequences/<int:seq_id>', methods=['DELETE'])
def delete_sequence(seq_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM sequences WHERE id=?', (seq_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ── API – budget history ─────────────────────────────────────────────────────

@bp.route('/api/history/<int:ep>', methods=['GET'])
def get_history(ep):
    conn = core.get_db()
    if not conn: return jsonify([])
    rows = conn.execute('SELECT * FROM budget_history WHERE ep=? ORDER BY id DESC', (ep,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/history/<int:ep>', methods=['POST'])
def add_history(ep):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json; c = conn.cursor()
    c.execute('''INSERT INTO budget_history
        (ep, record_date, version_label, script_v, edit_v, est_shots, edit_shots,
         est_budget, efc_budget, variance_val, status, est_reduction, reduction_notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (ep, d.get('record_date', datetime.now().strftime('%Y-%m-%d')),
         d.get('version_label', ''), d.get('script_v', ''), d.get('edit_v', ''),
         d.get('est_shots', 0), d.get('edit_shots', 0), d.get('est_budget', 0),
         d.get('efc_budget', 0), d.get('variance_val', 0), d.get('status', ''),
         d.get('est_reduction', 0), d.get('reduction_notes', '')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@bp.route('/api/history/<int:hist_id>', methods=['DELETE'])
def delete_history(hist_id):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM budget_history WHERE id=?', (hist_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ── API – global search ──────────────────────────────────────────────────────

@bp.route('/api/search')
def global_search():
    conn = core.get_db()
    if not conn: return jsonify({'shots': [], 'assets': [], 'notes': [], 'query': ''})
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        conn.close()
        return jsonify({'shots': [], 'assets': [], 'notes': [], 'query': q})
    like = f'%{q}%'
    shots = conn.execute('''
        SELECT id, ep, shot_num, scene_code, location, script_desc, vfx_desc, asset, award_vendor
        FROM shots WHERE omit=0 AND (
            scene_code LIKE ? OR location LIKE ? OR script_desc LIKE ?
            OR vfx_desc LIKE ? OR asset LIKE ? OR award_vendor LIKE ? OR s_code LIKE ?
        ) LIMIT 30''', (like,)*7).fetchall()
    assets = conn.execute('''
        SELECT id, ep, scene_code, asset_name, asset_type, description, award_vendor
        FROM assets WHERE omit=0 AND (
            asset_name LIKE ? OR scene_code LIKE ? OR description LIKE ?
            OR asset_type LIKE ? OR award_vendor LIKE ?
        ) LIMIT 20''', (like,)*5).fetchall()
    notes = conn.execute('''
        SELECT id, item_num, author, note_text, note_date FROM vfx_notes
        WHERE note_text LIKE ? OR author LIKE ? LIMIT 10''', (like, like)).fetchall()
    conn.close()
    return jsonify({'shots': [dict(r) for r in shots], 'assets': [dict(r) for r in assets],
                    'notes': [dict(r) for r in notes], 'query': q})


# ── API – import ─────────────────────────────────────────────────────────────

@bp.route('/api/import/preview/<int:ep>', methods=['POST'])
def import_preview(ep):
    f = request.files.get('file')
    if not f: return jsonify({'error': 'No file'}), 400
    fname = f.filename.lower()
    file_bytes = f.read()
    if fname.endswith('.xlsx') or fname.endswith('.xls'):
        sheet = request.form.get('sheet', '')
        rows, sheets = core._parse_rows_from_excel(file_bytes, ep, sheet or None)
        return jsonify({'rows': rows, 'sheets': sheets, 'count': len(rows)})
    return jsonify({'error': 'Use .xlsx files'}), 400


@bp.route('/api/import/commit/<int:ep>', methods=['POST'])
def import_commit(ep):
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    rows = d.get('rows', []); mode = d.get('mode', 'append')
    if not rows: return jsonify({'error': 'No rows'}), 400
    if mode == 'replace':
        conn.execute('DELETE FROM shots WHERE ep=?', (ep,))
    inserted = 0
    for rec in rows:
        rec['ep'] = ep
        fields = [f for f in core.DB_FIELDS if f in rec]
        fields_ep = ['ep'] + fields
        placeholders = ','.join('?' for _ in fields_ep)
        values = [rec.get(f) for f in fields_ep]
        conn.execute(f"INSERT INTO shots ({','.join(fields_ep)}) VALUES ({placeholders})", values)
        inserted += 1
    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted, 'mode': mode})


# ── API – export ─────────────────────────────────────────────────────────────

@bp.route('/api/export/distribution.xlsx')
def export_distribution_xlsx():
    conn = core.get_db()
    if not conn: return 'No project', 400
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment
    except ImportError:
        conn.close(); return 'openpyxl not installed', 500
    wb = openpyxl.Workbook()
    H_FILL = PatternFill('solid', fgColor='1F2035')
    H_FONT = Font(color='F0B429', bold=True, size=10)
    C_FONT = Font(color='DCE1F0', size=10)
    T_FONT = Font(color='F0B429', bold=True, size=10)
    def style_header(ws):
        for cell in ws[1]:
            cell.fill = H_FILL; cell.font = H_FONT
            cell.alignment = Alignment(horizontal='center')
    def col_widths(ws, widths):
        for col, w in zip(string.ascii_uppercase, widths):
            ws.column_dimensions[col].width = w
    ws1 = wb.active; ws1.title = 'Distribution'
    ws1.append(['EP','Script V','Edit V','Est Shots','Edit Shots',
                'Shot EST ($)','Asset EST ($)','Total EST ($)',
                'Shot EFC ($)','Asset EFC ($)','Total EFC ($)',
                'Variance ($)','Status','Reduction Notes','Notes'])
    style_header(ws1)
    dist_rows = []
    for ep in core.get_episodes():
        agg  = conn.execute('''SELECT COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS edit_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS est_budget,
            SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS efc_budget
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        meta = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        aa   = conn.execute('''SELECT
            SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS asset_est,
            SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS asset_actual
            FROM assets WHERE ep=?''', (ep,)).fetchone()
        se = agg['est_budget'] or 0; sf = agg['efc_budget'] or 0
        ae = (aa['asset_est'] or 0) if aa else 0; af = (aa['asset_actual'] or 0) if aa else 0
        row = [ep, meta['script_v'] if meta else '', meta['edit_v'] if meta else '',
               agg['est_shots'] or 0, agg['edit_shots'] or 0, se, ae, se+ae, sf, af, sf+af,
               (sf+af)-(se+ae), meta['status'] if meta else '',
               meta['reduction_notes'] if meta else '', meta['notes'] if meta else '']
        dist_rows.append(row); ws1.append(row)
        for cell in ws1[ws1.max_row]: cell.font = C_FONT
    tot = ['TOTAL','','', sum(r[3] for r in dist_rows), sum(r[4] for r in dist_rows),
           sum(r[5] for r in dist_rows), sum(r[6] for r in dist_rows), sum(r[7] for r in dist_rows),
           sum(r[8] for r in dist_rows), sum(r[9] for r in dist_rows), sum(r[10] for r in dist_rows),
           sum(r[11] for r in dist_rows), '', '', '']
    ws1.append(tot)
    for cell in ws1[ws1.max_row]: cell.font = T_FONT; cell.fill = H_FILL
    col_widths(ws1, [6,10,10,10,10,14,14,14,14,14,14,14,20,22,22])
    ws2 = wb.create_sheet('All Shots')
    ws2.append(['EP','Shot#','SC','S_Code','Location','EXT/INT','PG','IMG','Asset',
                'Script Desc','VFX Desc','Type','OMIT','Shot EST','Cost EST ($)',
                'Budget EST ($)','Award Vendor','Edit#','Budget Award ($)','EFC ($)','Notes'])
    style_header(ws2)
    for s in conn.execute('SELECT * FROM shots ORDER BY ep, shot_num, id').fetchall():
        ws2.append([s['ep'],s['shot_num'],s['scene_code'],s['s_code'],s['location'],
                    s['ext_int'],s['pg'],s['img'],s['asset'],s['script_desc'],s['vfx_desc'],
                    s['shot_type'],s['omit'],s['shot_est'],s['cost_est'],s['budget_est'],
                    s['award_vendor'],s['edit_count'],s['budget_award_cost'],s['efc'],s['notes']])
        for cell in ws2[ws2.max_row]: cell.font = C_FONT
    col_widths(ws2, [6,8,8,10,18,8,5,5,14,28,28,10,6,8,12,12,16,7,14,12,22])
    ws3 = wb.create_sheet('Assets')
    ws3.append(['EP','SC','Asset Name','Type','Description','Est Budget ($)',
                'Actual Spend ($)','Variance ($)','Award Vendor','Lidar','Photogrammetry','Notes'])
    style_header(ws3)
    for a in conn.execute('SELECT * FROM assets WHERE omit=0 ORDER BY ep, orig_id, id').fetchall():
        est = a['est_budget'] or 0; act = a['actual_spend'] or 0
        ws3.append([a['ep'],a['scene_code'],a['asset_name'],a['asset_type'],a['description'],
                    est,act,act-est,a['award_vendor'],a['lidar'],a['photogrammetry'],a['notes']])
        for cell in ws3[ws3.max_row]: cell.font = C_FONT
    col_widths(ws3, [6,8,18,10,24,14,14,12,16,7,12,20])
    conn.close()
    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)

    # Apply ForDistribution layout style
    try:
        import tempfile, os as _os
        from apply_export_layout import apply_layout
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        tmp.write(buf.getvalue()); tmp.close()
        apply_layout(tmp.name, sheet_name='Distribution')
        with open(tmp.name, 'rb') as f:
            styled = f.read()
        _os.unlink(tmp.name)
        buf = io.BytesIO(styled)
    except Exception as _e:
        print(f"[apply_layout] skipped: {_e}")
        buf.seek(0)

    return send_file(buf, as_attachment=True, download_name='vfx_distribution.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ── API – per-episode export ──────────────────────────────────────────────────

@bp.route('/api/export/ep/<int:ep_num>.xlsx')
def export_ep_xlsx(ep_num):
    conn = core.get_db()
    if not conn: return 'No project', 400
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment
    except ImportError:
        conn.close(); return 'openpyxl not installed', 500

    wb = openpyxl.Workbook()
    H_FILL = PatternFill('solid', fgColor='1F2035')
    H_FONT = Font(color='F0B429', bold=True, size=10)
    C_FONT = Font(color='DCE1F0', size=10)
    T_FONT = Font(color='F0B429', bold=True, size=10)

    def style_header(ws):
        for cell in ws[1]:
            cell.fill = H_FILL; cell.font = H_FONT
            cell.alignment = Alignment(horizontal='center')

    def col_widths(ws, widths):
        for col, w in zip(string.ascii_uppercase, widths):
            ws.column_dimensions[col].width = w

    # Sheet 1: Shots
    ws1 = wb.active; ws1.title = f'EP{ep_num} Shots'
    ws1.append(['Shot#', 'SC', 'S_Code', 'Location', 'EXT/INT', 'PG', 'IMG', 'Asset',
                'Script Desc', 'VFX Desc', 'Type', 'Complexity', 'OMIT', 'Shot EST',
                'Cost EST ($)', 'Budget EST ($)', 'Award Vendor',
                'Edit#', 'Budget Award ($)', 'EFC ($)', 'Notes'])
    style_header(ws1)
    shots = conn.execute(
        'SELECT * FROM shots WHERE ep=? ORDER BY shot_num, id', (ep_num,)
    ).fetchall()
    for s in shots:
        ws1.append([s['shot_num'], s['scene_code'], s['s_code'], s['location'],
                    s['ext_int'], s['pg'], s['img'], s['asset'],
                    s['script_desc'], s['vfx_desc'], s['shot_type'], s['complexity'],
                    s['omit'], s['shot_est'], s['cost_est'], s['budget_est'],
                    s['award_vendor'], s['edit_count'], s['budget_award_cost'],
                    s['efc'], s['notes']])
        for cell in ws1[ws1.max_row]: cell.font = C_FONT

    # Totals row
    active = [s for s in shots if not s['omit']]
    totals = ['TOTAL', '', '', '', '', '', '', '', '', '', '', '',
              '', sum(s['shot_est'] or 0 for s in active),
              sum(s['cost_est'] or 0 for s in active),
              sum(s['budget_est'] or 0 for s in active), '',
              sum(s['edit_count'] or 0 for s in active),
              sum(s['budget_award_cost'] or 0 for s in active),
              sum(s['efc'] or 0 for s in active), '']
    ws1.append(totals)
    for cell in ws1[ws1.max_row]: cell.font = T_FONT; cell.fill = H_FILL
    col_widths(ws1, [8,8,10,18,8,5,5,14,28,28,10,10,6,8,12,12,16,7,14,12,22])

    # Sheet 2: Assets for this EP
    ws2 = wb.create_sheet(f'EP{ep_num} Assets')
    ws2.append(['SC', 'Asset Name', 'Type', 'Description', 'Est Budget ($)',
                'Actual Spend ($)', 'Variance ($)', 'Award Vendor',
                'Lidar', 'Photogrammetry', 'Notes'])
    style_header(ws2)
    assets = conn.execute(
        'SELECT * FROM assets WHERE ep=? AND omit=0 ORDER BY orig_id, id', (ep_num,)
    ).fetchall()
    for a in assets:
        est = a['est_budget'] or 0; act = a['actual_spend'] or 0
        ws2.append([a['scene_code'], a['asset_name'], a['asset_type'],
                    a['description'], est, act, act - est,
                    a['award_vendor'], a['lidar'], a['photogrammetry'], a['notes']])
        for cell in ws2[ws2.max_row]: cell.font = C_FONT
    col_widths(ws2, [8,18,10,24,14,14,12,16,7,12,20])

    # Sheet 3: EP summary header block
    ws3 = wb.create_sheet('Summary')
    meta = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep_num,)).fetchone()
    agg = conn.execute('''
        SELECT COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS edit_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS est_budget,
               SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS efc_budget
        FROM shots WHERE ep=?''', (ep_num,)).fetchone()
    aa = conn.execute('''
        SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS asset_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS asset_actual
        FROM assets WHERE ep=?''', (ep_num,)).fetchone()
    se = agg['est_budget'] or 0; sf = agg['efc_budget'] or 0
    ae = (aa['asset_est'] or 0) if aa else 0; af = (aa['asset_actual'] or 0) if aa else 0
    summary_rows = [
        ['Episode', ep_num],
        ['Script Version', meta['script_v'] if meta else ''],
        ['Edit Version', meta['edit_v'] if meta else ''],
        ['Status', meta['status'] if meta else ''],
        ['Est Shots', agg['est_shots'] or 0],
        ['Edit Shots', agg['edit_shots'] or 0],
        ['Shot EST ($)', se],
        ['Asset EST ($)', ae],
        ['Total EST ($)', se + ae],
        ['Shot EFC ($)', sf],
        ['Asset EFC ($)', af],
        ['Total EFC ($)', sf + af],
        ['Variance ($)', (sf + af) - (se + ae)],
        ['Est Reduction', meta['est_reduction'] if meta else 0],
        ['Reduction Notes', meta['reduction_notes'] if meta else ''],
        ['Notes', meta['notes'] if meta else ''],
    ]
    for row in summary_rows:
        ws3.append(row)
        ws3[ws3.max_row][0].font = Font(color='8898C0', size=10)
        ws3[ws3.max_row][1].font = Font(color='DCE1F0', size=10)
    ws3.column_dimensions['A'].width = 20
    ws3.column_dimensions['B'].width = 30

    conn.close()
    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'ep{ep_num}_shots.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ── API – per-episode PDF one-pager ──────────────────────────────────────────

@bp.route('/api/export/ep/<int:ep_num>.pdf')
def export_ep_pdf(ep_num):
    conn = core.get_db()
    if not conn: return 'No project', 400
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        conn.close(); return 'reportlab not installed', 500

    W, H = landscape(A4)
    C_GOLD   = colors.HexColor('#f0b429')
    C_DARK   = colors.HexColor('#0d0e18')
    C_PANEL  = colors.HexColor('#12152a')
    C_BORDER = colors.HexColor('#2e3050')
    C_TEXT   = colors.HexColor('#d0d8f0')
    C_MUTED  = colors.HexColor('#7880a0')
    C_GREEN  = colors.HexColor('#52c46a')
    C_RED    = colors.HexColor('#e05252')

    # Pull data
    meta = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep_num,)).fetchone()
    agg = conn.execute('''
        SELECT COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) AS edit_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) AS est_budget,
               SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) AS efc_budget,
               COUNT(CASE WHEN omit=0 THEN 1 END) AS total_shots
        FROM shots WHERE ep=?''', (ep_num,)).fetchone()
    aa = conn.execute('''
        SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS asset_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS asset_actual,
               COUNT(CASE WHEN omit=0 THEN 1 END) AS asset_count
        FROM assets WHERE ep=?''', (ep_num,)).fetchone()
    top_shots = conn.execute('''
        SELECT scene_code, location, vfx_desc, award_vendor, efc, cost_est
        FROM shots WHERE ep=? AND omit=0 AND efc > 0
        ORDER BY efc DESC LIMIT 8''', (ep_num,)).fetchall()
    vendor_summary = conn.execute('''
        SELECT award_vendor, COUNT(*) as cnt,
               SUM(COALESCE(efc,0)) as total_efc
        FROM shots WHERE ep=? AND omit=0 AND award_vendor IS NOT NULL AND award_vendor != ''
        GROUP BY award_vendor ORDER BY total_efc DESC LIMIT 6''', (ep_num,)).fetchall()
    conn.close()

    se = agg['est_budget'] or 0
    sf = agg['efc_budget'] or 0
    ae = (aa['asset_est'] or 0) if aa else 0
    af = (aa['asset_actual'] or 0) if aa else 0
    total_est = se + ae
    total_efc = sf + af
    variance  = total_efc - total_est

    def fmt(v):
        if not v: return '$0'
        return f'${v:,.0f}'

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=10*mm, rightMargin=10*mm,
                            topMargin=8*mm, bottomMargin=8*mm)

    def P(text, size=9, color=C_TEXT, bold=False, align=TA_LEFT):
        return Paragraph(text, ParagraphStyle('x', fontSize=size, leading=size+3,
            textColor=color, fontName='Helvetica-Bold' if bold else 'Helvetica',
            alignment=align))

    story = []

    # Title bar
    proj_name = session.get('project_name', 'Project')
    story.append(P(f'{proj_name}  —  EPISODE {ep_num}  —  VFX ONE-PAGER',
                   size=14, color=C_GOLD, bold=True, align=TA_CENTER))
    story.append(Spacer(1, 3*mm))

    # Top summary table
    script_v = meta['script_v'] if meta else '—'
    edit_v   = meta['edit_v']   if meta else '—'
    status   = meta['status']   if meta else '—'
    var_color = C_RED if variance > 0 else C_GREEN

    summary_data = [
        ['SCRIPT V', 'EDIT V', 'STATUS', 'EST SHOTS', 'EDIT SHOTS',
         'SHOT EST', 'ASSET EST', 'TOTAL EST', 'TOTAL EFC', 'VARIANCE'],
        [script_v, edit_v, status,
         str(agg['est_shots'] or 0), str(agg['edit_shots'] or 0),
         fmt(se), fmt(ae), fmt(total_est), fmt(total_efc), fmt(variance)],
    ]
    hdr_style = [('BACKGROUND', (0, 0), (-1, 0), C_PANEL),
                 ('TEXTCOLOR',  (0, 0), (-1, 0), C_GOLD),
                 ('TEXTCOLOR',  (0, 1), (-1, 1), C_TEXT),
                 ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                 ('FONTSIZE',   (0, 0), (-1,-1), 8),
                 ('ALIGN',      (0, 0), (-1,-1), 'CENTER'),
                 ('GRID',       (0, 0), (-1,-1), 0.3, C_BORDER),
                 ('BACKGROUND', (0, 1), (-1, 1), C_DARK),
                 ('TEXTCOLOR',  (9, 1), (9, 1), var_color),
                 ('ROWBACKGROUNDS', (0, 1), (-1,-1), [C_DARK])]
    col_w = [18*mm]*10
    story.append(Table(summary_data, colWidths=col_w,
                        style=TableStyle(hdr_style)))
    story.append(Spacer(1, 4*mm))

    # Two-column layout: top shots + vendor breakdown
    # Top shots at risk
    shots_data = [['SC', 'LOCATION', 'VFX DESC', 'VENDOR', 'EFC', 'EST', 'OVER']]
    for s in top_shots:
        over = (s['efc'] or 0) - (s['cost_est'] or 0)
        over_c = '#e05252' if over > 0 else '#52c46a'
        shots_data.append([
            str(s['scene_code'] or ''),
            str((s['location'] or '')[:28]),
            str((s['vfx_desc'] or '')[:35]),
            str(s['award_vendor'] or '—'),
            fmt(s['efc']),
            fmt(s['cost_est']),
            fmt(over),
        ])
    if len(shots_data) == 1:
        shots_data.append(['—', '—', 'No EFC data', '', '', '', ''])

    shots_tbl = Table(shots_data,
                      colWidths=[14*mm, 42*mm, 58*mm, 28*mm, 18*mm, 18*mm, 18*mm],
                      style=TableStyle([
                          ('BACKGROUND',   (0, 0), (-1, 0), C_PANEL),
                          ('TEXTCOLOR',    (0, 0), (-1, 0), C_GOLD),
                          ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
                          ('FONTSIZE',     (0, 0), (-1,-1), 7.5),
                          ('GRID',         (0, 0), (-1,-1), 0.3, C_BORDER),
                          ('TEXTCOLOR',    (0, 1), (-1,-1), C_TEXT),
                          ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_DARK, C_PANEL]),
                          ('ALIGN',        (4, 0), (6,-1), 'RIGHT'),
                      ]))

    # Vendor breakdown
    vend_data = [['VENDOR', 'SHOTS', 'TOTAL EFC']]
    for v in vendor_summary:
        vend_data.append([str(v['award_vendor']), str(v['cnt']), fmt(v['total_efc'])])
    if len(vend_data) == 1:
        vend_data.append(['No vendor data', '', ''])

    vend_tbl = Table(vend_data, colWidths=[44*mm, 16*mm, 24*mm],
                     style=TableStyle([
                         ('BACKGROUND',   (0, 0), (-1, 0), C_PANEL),
                         ('TEXTCOLOR',    (0, 0), (-1, 0), C_GOLD),
                         ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('FONTSIZE',     (0, 0), (-1,-1), 7.5),
                         ('GRID',         (0, 0), (-1,-1), 0.3, C_BORDER),
                         ('TEXTCOLOR',    (0, 1), (-1,-1), C_TEXT),
                         ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_DARK, C_PANEL]),
                         ('ALIGN',        (1, 0), (2,-1), 'RIGHT'),
                     ]))

    combined = Table([[shots_tbl, Spacer(4*mm, 1), vend_tbl]],
                     colWidths=[196*mm, 4*mm, 84*mm])
    story.append(P('TOP SHOTS BY EFC', size=8, color=C_MUTED, bold=True))
    story.append(Spacer(1, 1*mm))
    story.append(combined)

    # Notes footer
    notes = (meta['notes'] or '') if meta else ''
    if notes:
        story.append(Spacer(1, 3*mm))
        story.append(P(f'NOTES: {notes}', size=7.5, color=C_MUTED))

    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'ep{ep_num}_one_pager.pdf',
                     mimetype='application/pdf')


# ── API – Background LLM batch jobs ─────────────────────────────────────────

@bp.route('/api/ai/batch_job', methods=['POST'])
def start_batch_ai_job():
    """Start a background job for batch LLM operations."""
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400
    data = request.get_json(force=True)
    task = data.get('task')   # 'batch_complexity' | 'batch_vfx_desc'
    ep   = data.get('ep')
    shot_ids = data.get('shot_ids', [])
    if not task or not ep:
        return jsonify({'error': 'task and ep required'}), 400

    import jobs.queue as jq
    from flask import session as flask_session
    db_path = flask_session.get('project_db')
    label = f'{task} EP{ep} ({len(shot_ids)} shots)'

    def _run(job_id, db_path=db_path, task=task, ep=ep, shot_ids=shot_ids):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            if shot_ids:
                placeholders = ','.join('?' * len(shot_ids))
                shots = conn.execute(
                    f'SELECT * FROM shots WHERE id IN ({placeholders})', shot_ids
                ).fetchall()
            else:
                shots = conn.execute(
                    'SELECT * FROM shots WHERE ep=? AND omit=0', (ep,)
                ).fetchall()

            client = core.get_llm_client()
            results = {}
            total = len(shots)

            for idx, shot in enumerate(shots):
                pct = int((idx / total) * 90) + 5
                jq.update_progress(job_id, pct, 'running',
                                   f'Processing shot {idx+1}/{total}')
                try:
                    import llm as llm_mod
                    if task == 'batch_complexity':
                        prompt = llm_mod.build_prompt('complexity_tag', {
                            'vfx_desc': shot['vfx_desc'] or '',
                            'shot_type': shot['shot_type'] or '',
                        })
                        result_text = ''.join(client.stream(prompt)).strip()
                        word = result_text.upper()
                        if word in ('SIMPLE', 'MEDIUM', 'HEAVY'):
                            conn.execute(
                                'UPDATE shots SET complexity=? WHERE id=?',
                                (word, shot['id'])
                            )
                            conn.commit()
                            results[str(shot['id'])] = word
                    elif task == 'batch_vfx_desc':
                        prompt = llm_mod.build_prompt('vfx_desc', {
                            'scene_code': shot['scene_code'] or '',
                            'location': shot['location'] or '',
                            'ext_int': shot['ext_int'] or '',
                            'script_desc': shot['script_desc'] or '',
                            'asset': shot['asset'] or '',
                        })
                        result_text = ''.join(client.stream(prompt)).strip()
                        if result_text and not result_text.startswith('['):
                            conn.execute(
                                'UPDATE shots SET vfx_desc=? WHERE id=?',
                                (result_text, shot['id'])
                            )
                            conn.commit()
                            results[str(shot['id'])] = result_text
                except Exception as e:
                    results[str(shot['id'])] = f'error: {e}'

            jq.complete(job_id, {'updated': len(results), 'results': results})
        finally:
            conn.close()

    job_id = jq.submit(_run, label=label)
    return jsonify({'job_id': job_id})


# ── API – Predictive EFC (actuals-anchored delivery ratio model) ──────────────

@bp.route('/api/predictive_efc/<int:ep>', methods=['GET'])
def predictive_efc_ep(ep):
    """
    Return predicted final cost per shot for one episode.
    Uses vendor×type delivery ratios computed from historical EFC vs cost_est.
    Response: { shots: [...], summary: {...} }
    """
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    try:
        from services.distribution import compute_predictive_efc
        shots, summary = compute_predictive_efc(conn, ep=ep)
        return jsonify({'shots': shots, 'summary': summary, 'ep': ep})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/predictive_efc/season', methods=['GET'])
def predictive_efc_season():
    """
    Return predicted final cost for all episodes (season-level).
    Response: { shots: [...], summary: {...}, by_ep: { ep: summary, ... } }
    """
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    try:
        from services.distribution import compute_predictive_efc
        all_shots, season_summary = compute_predictive_efc(conn, ep=None)

        # Roll up per-episode summaries
        from collections import defaultdict
        by_ep = defaultdict(lambda: {'total_est': 0, 'total_predicted': 0, 'shots': 0})
        for s in all_shots:
            ep = s['ep']
            by_ep[ep]['total_est']       += s['cost_est']
            by_ep[ep]['total_predicted'] += s['predicted_efc']
            by_ep[ep]['shots']           += 1

        for ep_data in by_ep.values():
            ep_data['predicted_variance'] = round(
                ep_data['total_predicted'] - ep_data['total_est'], 2
            )
            ep_data['total_est']       = round(ep_data['total_est'], 2)
            ep_data['total_predicted'] = round(ep_data['total_predicted'], 2)

        return jsonify({
            'shots':          all_shots,
            'summary':        season_summary,
            'by_ep':          dict(by_ep),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/llm/bid_analysis', methods=['POST'])
def bid_analysis():
    """
    Analyze bid data for an episode: outliers, concentration risk, health summary.
    POST body: { ep }
    """
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    d  = request.json or {}
    ep = d.get('ep')
    if not ep:
        return jsonify({'error': 'ep required'}), 400

    import json as _json
    import llm as llm_module
    from services.llm_helpers import complete_json

    shots = conn.execute(
        "SELECT scene_code, award_vendor, cost_est, efc, vendor_bids FROM shots "
        "WHERE ep=? AND omit=0 ORDER BY scene_code", (ep,)
    ).fetchall()

    outlier_lines = []
    spread_vals   = []
    for s in shots:
        try:
            bids = _json.loads(s['vendor_bids']) if s['vendor_bids'] else {}
            vals = [float(v) for v in bids.values() if v and float(v) > 0]
            if len(vals) >= 2:
                ratio = max(vals) / min(vals)
                spread_vals.append(ratio)
                if ratio > 2.5:
                    low_v  = sorted(bids.items(), key=lambda x: float(x[1] or 0))[0]
                    high_v = sorted(bids.items(), key=lambda x: float(x[1] or 0))[-1]
                    outlier_lines.append(
                        f"  SC {s['scene_code']}: spread {ratio:.1f}x "
                        f"(low: {low_v[0]} ${float(low_v[1]):,.0f} | "
                        f"high: {high_v[0]} ${float(high_v[1]):,.0f})"
                    )
        except Exception:
            pass

    vendor_agg = conn.execute(
        "SELECT award_vendor, COUNT(*) as n, SUM(COALESCE(efc,0)) as total_efc "
        "FROM shots WHERE ep=? AND omit=0 AND award_vendor IS NOT NULL AND award_vendor!='' "
        "GROUP BY award_vendor ORDER BY total_efc DESC", (ep,)
    ).fetchall()
    vendor_awards = '\n'.join(
        f"  {r['award_vendor']}: {r['n']} shots, ${r['total_efc']:,.0f} EFC"
        for r in vendor_agg
    ) or '  (no awards yet)'

    conn.close()

    avg_spread = round(sum(spread_vals) / len(spread_vals), 2) if spread_vals else 1.0
    ctx = {
        'ep':            ep,
        'shot_count':    len(shots),
        'avg_spread':    avg_spread,
        'outlier_list':  '\n'.join(outlier_lines) or '  (no major outliers)',
        'vendor_awards': vendor_awards,
    }
    prompt = llm_module.build_prompt('bid_analysis', ctx)
    if not prompt:
        return jsonify({'error': 'prompt build failed'}), 400

    client = core.get_llm_client()
    result = complete_json(prompt, client,
                           cache_task='bid_analysis',
                           cache_ctx={'ep': str(ep)})
    if result is None:
        return jsonify({'error': 'LLM unavailable'}), 503
    return jsonify(result)
