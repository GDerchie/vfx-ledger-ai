from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import os
import csv
import io
import json
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DB = os.path.join(BASE_DIR, 'projects.db')

app = Flask(__name__)
app.secret_key = 'vfx-budget-system-2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ---------------------------------------------------------------------------
# Projects master DB
# ---------------------------------------------------------------------------

def get_projects_db():
    conn = sqlite3.connect(PROJECTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_projects_db():
    conn = get_projects_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS projects (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        season      TEXT NOT NULL DEFAULT 'S1',
        db_filename TEXT NOT NULL,
        db_path     TEXT NOT NULL,
        ep_start    INTEGER DEFAULT 101,
        ep_end      INTEGER DEFAULT 108,
        description TEXT DEFAULT '',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_opened TIMESTAMP
    )''')
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Active project DB  (session-scoped)
# ---------------------------------------------------------------------------

def get_db():
    db_path = session.get('project_db')
    if not db_path or not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_episodes():
    return list(range(session.get('ep_start', 101), session.get('ep_end', 108) + 1))


def require_project():
    if not session.get('project_db') or not os.path.exists(session['project_db']):
        session.clear()
        return redirect(url_for('project_list'))
    return None


@app.route('/projects')
def project_list():
    return render_template('home.html')


def init_project_db(db_path, ep_start=101, ep_end=108):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS shots (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        ep                INTEGER NOT NULL,
        shot_num          INTEGER,
        scene_code        TEXT,
        s_code            TEXT,
        location          TEXT,
        ext_int           TEXT,
        pg                TEXT,
        img               TEXT,
        asset             TEXT,
        script_desc       TEXT,
        vfx_desc          TEXT,
        shot_type         TEXT,
        omit              INTEGER DEFAULT 0,
        history_notes     TEXT,
        shot_est          INTEGER DEFAULT 1,
        cost_est          REAL    DEFAULT 0,
        budget_est        REAL    DEFAULT 0,
        award_vendor      TEXT,
        edit_count        INTEGER DEFAULT 0,
        budget_award_cost REAL    DEFAULT 0,
        efc               REAL    DEFAULT 0,
        notes             TEXT,
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ep_meta (
        ep               INTEGER PRIMARY KEY,
        script_v         TEXT DEFAULT '',
        edit_v           TEXT DEFAULT '',
        status           TEXT DEFAULT '',
        est_reduction    REAL DEFAULT 0,
        reduction_notes  TEXT DEFAULT '',
        notes            TEXT DEFAULT ''
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sequences (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        ep                INTEGER NOT NULL,
        seq_name          TEXT,
        location          TEXT,
        omit              INTEGER DEFAULT 0,
        est_shots         INTEGER DEFAULT 0,
        current_cut       INTEGER DEFAULT 0,
        lbudget           REAL    DEFAULT 0,
        efc               REAL    DEFAULT 0,
        variance_val      REAL    DEFAULT 0,
        status            TEXT,
        est_reductions    TEXT,
        est_ctd           REAL    DEFAULT 0,
        turnover_deadline TEXT,
        notes             TEXT,
        auto_sync         INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS budget_history (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        ep               INTEGER NOT NULL,
        record_date      TEXT,
        version_label    TEXT,
        script_v         TEXT,
        edit_v           TEXT,
        est_shots        INTEGER DEFAULT 0,
        edit_shots       INTEGER DEFAULT 0,
        est_budget       REAL    DEFAULT 0,
        efc_budget       REAL    DEFAULT 0,
        variance_val     REAL    DEFAULT 0,
        status           TEXT,
        est_reduction    REAL    DEFAULT 0,
        reduction_notes  TEXT,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vfx_notes (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        item_num  INTEGER,
        author    TEXT,
        note_text TEXT,
        note_date TEXT,
        resolved  INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        orig_id       INTEGER,
        ep            INTEGER,
        scene_code    TEXT,
        turnover      TEXT,
        asset_name    TEXT,
        description   TEXT,
        reference     TEXT,
        asset_type    TEXT,
        repeat_asset  INTEGER DEFAULT 0,
        hero_id       INTEGER DEFAULT 0,
        omit          INTEGER DEFAULT 0,
        ref           TEXT,
        notes         TEXT,
        lidar         INTEGER DEFAULT 0,
        photogrammetry INTEGER DEFAULT 0,
        est_budget    REAL DEFAULT 0,
        actual_spend  REAL DEFAULT 0,
        award_vendor  TEXT,
        vendor_bids   TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bid_compare (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        orig_id     INTEGER,
        ep          INTEGER,
        sc          TEXT,
        setting     TEXT,
        novfx       INTEGER DEFAULT 0,
        scount      INTEGER DEFAULT 0,
        edit_count  INTEGER DEFAULT 0,
        vfxtype     TEXT,
        version     INTEGER DEFAULT 1,
        award       TEXT,
        lockbudget  REAL DEFAULT 0,
        efc         REAL DEFAULT 0,
        vendor_bids TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendor_tracker (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor          TEXT,
        region          TEXT,
        ep              INTEGER,
        asset_award     REAL,
        award_ep        REAL,
        tot_award       REAL,
        paid            REAL DEFAULT 0,
        pending         REAL DEFAULT 0,
        remaining       REAL,
        tax_reb         REAL,
        gross_local     REAL,
        gross_usd       REAL,
        sale_tax_amount REAL,
        gross_plus_tax  REAL,
        tax_rebate_amt  REAL,
        net_after_rebate REAL,
        final_price     REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS invoice_log (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor       TEXT,
        episode      INTEGER,
        inv_num      TEXT,
        inv_date     TEXT,
        amount       REAL DEFAULT 0,
        status       TEXT,
        approve_date TEXT,
        notes        TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS budget_scenario (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_type TEXT    DEFAULT 'Conservative',
        ep            INTEGER DEFAULT 101,
        tax_pct       REAL    DEFAULT 0,
        eligible_pct  REAL    DEFAULT 0,
        net_cost      REAL    DEFAULT 0,
        notes         TEXT    DEFAULT ''
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ep_forecast (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        ep               INTEGER NOT NULL UNIQUE,
        contingency      REAL DEFAULT 0.2,
        budget           REAL DEFAULT 0,
        award            REAL DEFAULT 0,
        eligible         REAL DEFAULT 0,
        global_rebate_pct REAL DEFAULT 0,
        global_pct       REAL DEFAULT 0,
        notes            TEXT DEFAULT ''
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendor_forecast (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor       TEXT DEFAULT '',
        ep           INTEGER DEFAULT 101,
        gross_local  REAL DEFAULT 0,
        gross_usd    REAL DEFAULT 0,
        region       TEXT DEFAULT '',
        eligible_pct REAL DEFAULT 0,
        rebate_pct   REAL DEFAULT 0,
        notes        TEXT DEFAULT ''
    )''')

    for ep in range(ep_start, ep_end + 1):
        c.execute('INSERT OR IGNORE INTO ep_meta (ep) VALUES (?)', (ep,))
        c.execute('INSERT OR IGNORE INTO ep_forecast (ep) VALUES (?)', (ep,))

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Home / Project management routes
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    # If a valid project is already in session, go straight to distribution
    if session.get('project_db') and os.path.exists(session['project_db']):
        return redirect(url_for('distribution'))
    # Auto-open the most recently used project
    conn = get_projects_db()
    proj = conn.execute(
        '''SELECT * FROM projects WHERE last_opened IS NOT NULL
           ORDER BY last_opened DESC LIMIT 1'''
    ).fetchone()
    conn.close()
    if proj and os.path.exists(proj['db_path']):
        return redirect(url_for('open_project', project_id=proj['id']))
    return render_template('home.html')


@app.route('/api/projects', methods=['GET'])
def list_projects():
    conn = get_projects_db()
    rows = conn.execute(
        'SELECT * FROM projects ORDER BY last_opened DESC NULLS LAST, created_at DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/projects', methods=['POST'])
def create_project():
    d = request.json
    name    = d.get('name', '').strip().upper()
    season  = d.get('season', 'S1').strip().upper()
    ep_start = int(d.get('ep_start', 101))
    ep_end   = int(d.get('ep_end', 108))
    desc     = d.get('description', '')

    if not name:
        return jsonify({'error': 'Project name required'}), 400

    db_filename = f"{name}_{season}.vfxdb"
    db_path     = os.path.join(BASE_DIR, db_filename)

    # Handle filename collisions
    if os.path.exists(db_path):
        base = db_filename.replace('.vfxdb', '')
        i = 2
        while os.path.exists(os.path.join(BASE_DIR, f"{base}_v{i}.vfxdb")):
            i += 1
        db_filename = f"{base}_v{i}.vfxdb"
        db_path     = os.path.join(BASE_DIR, db_filename)

    init_project_db(db_path, ep_start, ep_end)

    conn = get_projects_db()
    c = conn.cursor()
    c.execute('''INSERT INTO projects
        (name, season, db_filename, db_path, ep_start, ep_end, description)
        VALUES (?,?,?,?,?,?,?)''',
        (name, season, db_filename, db_path, ep_start, ep_end, desc))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id, 'db_filename': db_filename})


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    d = request.json
    allowed = ['name', 'season', 'description']
    updates = {k: d[k] for k in allowed if k in d}
    if 'name' in updates:
        updates['name'] = updates['name'].strip().upper()
    if updates:
        sql = 'UPDATE projects SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn = get_projects_db()
        conn.execute(sql, list(updates.values()) + [project_id])
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = get_projects_db()
    proj = conn.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
    if proj:
        if os.path.exists(proj['db_path']):
            os.remove(proj['db_path'])
        conn.execute('DELETE FROM projects WHERE id=?', (project_id,))
        conn.commit()
        if session.get('project_id') == project_id:
            session.clear()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/projects/<int:project_id>/open')
def open_project(project_id):
    conn = get_projects_db()
    proj = conn.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
    if not proj:
        conn.close()
        return redirect(url_for('home'))
    conn.execute('UPDATE projects SET last_opened=? WHERE id=?',
                 (datetime.now().isoformat(), project_id))
    conn.commit()
    conn.close()

    session['project_id']     = project_id
    session['project_db']     = proj['db_path']
    session['project_name']   = proj['name']
    session['project_season'] = proj['season']
    session['ep_start']       = proj['ep_start']
    session['ep_end']         = proj['ep_end']
    return redirect(url_for('distribution'))


@app.route('/projects/close')
def close_project():
    session.clear()
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# Page routes (all require an active project)
# ---------------------------------------------------------------------------

@app.route('/distribution')
def distribution():
    r = require_project()
    if r: return r
    return render_template('distribution.html')


@app.route('/ep/<int:ep_num>')
def ep_page(ep_num):
    r = require_project()
    if r: return r
    return render_template('ep.html', ep_num=ep_num)


@app.route('/notes')
def notes_page():
    r = require_project()
    if r: return r
    return render_template('notes.html')


@app.route('/assets')
def assets_page():
    r = require_project()
    if r: return r
    return render_template('assets.html')


@app.route('/bidcompare')
def bidcompare_page():
    r = require_project()
    if r: return r
    return render_template('bidcompare.html')


@app.route('/vendortracker')
def vendortracker_page():
    r = require_project()
    if r: return r
    return render_template('vendortracker.html')


# ---------------------------------------------------------------------------
# API – shots
# ---------------------------------------------------------------------------

@app.route('/api/shots/<int:ep>', methods=['GET'])
def get_shots(ep):
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute(
        'SELECT * FROM shots WHERE ep=? ORDER BY shot_num, id', (ep,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/shots', methods=['POST'])
def create_shot():
    conn = get_db()
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


@app.route('/api/shots/<int:shot_id>', methods=['PUT'])
def update_shot(shot_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['shot_num', 'scene_code', 's_code', 'location', 'ext_int', 'pg',
               'img', 'asset', 'script_desc', 'vfx_desc', 'shot_type', 'omit',
               'history_notes', 'shot_est', 'cost_est', 'budget_est', 'award_vendor',
               'edit_count', 'budget_award_cost', 'efc', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    updates['updated_at'] = datetime.now().isoformat()
    sql = 'UPDATE shots SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
    conn.execute(sql, list(updates.values()) + [shot_id])
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/shots/<int:shot_id>', methods=['DELETE'])
def delete_shot(shot_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM shots WHERE id=?', (shot_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – ep_meta
# ---------------------------------------------------------------------------

@app.route('/api/ep_meta/<int:ep>', methods=['GET'])
def get_ep_meta(ep):
    conn = get_db()
    if not conn: return jsonify({})
    row = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
    conn.close()
    return jsonify(dict(row) if row else {})


@app.route('/api/ep_meta/<int:ep>', methods=['PUT'])
def update_ep_meta(ep):
    conn = get_db()
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


# ---------------------------------------------------------------------------
# API – distribution
# ---------------------------------------------------------------------------

@app.route('/api/distribution', methods=['GET'])
def get_distribution():
    conn = get_db()
    if not conn: return jsonify([])
    result = []
    for ep in get_episodes():
        agg = conn.execute('''
            SELECT
                COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) AS est_shots,
                SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END)  AS edit_shots,
                SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)  ELSE 0 END)   AS est_budget,
                SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)       ELSE 0 END)   AS efc_budget
            FROM shots WHERE ep=?''', (ep,)).fetchone()
        meta = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        # Asset totals for this EP
        asset_agg = conn.execute('''
            SELECT
                SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0)    ELSE 0 END) AS asset_est,
                SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0)  ELSE 0 END) AS asset_actual
            FROM assets WHERE ep=?''', (ep,)).fetchone()
        shot_est   = agg['est_budget']  or 0
        shot_efc   = agg['efc_budget']  or 0
        asset_est  = (asset_agg['asset_est']    or 0) if asset_agg else 0
        asset_efc  = (asset_agg['asset_actual'] or 0) if asset_agg else 0
        combined_est = shot_est + asset_est
        combined_efc = shot_efc + asset_efc
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
        })
    conn.close()
    return jsonify(result)


# ---------------------------------------------------------------------------
# API – sequences
# ---------------------------------------------------------------------------

@app.route('/api/sequences', methods=['GET'])
def get_sequences():
    conn = get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    if ep:
        rows = conn.execute('SELECT * FROM sequences WHERE ep=? ORDER BY id', (ep,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM sequences ORDER BY ep, id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sequences', methods=['POST'])
def create_sequence():
    conn = get_db()
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
         d.get('est_reductions'), d.get('est_ctd', 0),
         d.get('turnover_deadline'), d.get('notes')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@app.route('/api/sequences/<int:seq_id>', methods=['PUT'])
def update_sequence(seq_id):
    conn = get_db()
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


@app.route('/api/sequences/aggregate/<int:ep>', methods=['GET'])
def aggregate_sequences(ep):
    """Return shots for an EP aggregated by scene_code + location."""
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute('''
        SELECT
            COALESCE(NULLIF(scene_code,''), '?')           AS scene_code,
            COALESCE(NULLIF(location,''),  '(no loc)')     AS location,
            COUNT(CASE WHEN omit=0 THEN 1 END)                                  AS est_shots,
            SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0)  ELSE 0 END)       AS current_cut,
            SUM(CASE WHEN omit=0 THEN COALESCE(budget_est,0)  ELSE 0 END)       AS lbudget,
            SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)    ELSE 0 END)       AS cost_total,
            SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)         ELSE 0 END)       AS efc
        FROM shots
        WHERE ep=?
        GROUP BY scene_code, location
        ORDER BY CAST(scene_code AS REAL), location
    ''', (ep,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        efc     = r['efc']     or 0
        lbudget = r['lbudget'] or 0
        result.append({
            'ep':          ep,
            'seq_name':    r['scene_code'],
            'location':    r['location'],
            'est_shots':   r['est_shots']   or 0,
            'current_cut': r['current_cut'] or 0,
            'lbudget':     lbudget,
            'efc':         efc,
            'variance_val': efc - lbudget,
            'cost_total':  r['cost_total']  or 0,
        })
    return jsonify(result)


@app.route('/api/sequences/sync', methods=['POST'])
def sync_sequences():
    """Replace auto-imported sequence rows for selected EPs with fresh aggregation."""
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d        = request.json
    eps      = d.get('eps', [])
    mode     = d.get('mode', 'replace')   # replace | append
    inserted = 0

    for ep in eps:
        # Get aggregated shot data
        agg_rows = conn.execute('''
            SELECT
                COALESCE(NULLIF(scene_code,''), '?')          AS scene_code,
                COALESCE(NULLIF(location,''),  '(no loc)')    AS location,
                COUNT(CASE WHEN omit=0 THEN 1 END)                             AS est_shots,
                SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END)  AS current_cut,
                SUM(CASE WHEN omit=0 THEN COALESCE(budget_est,0) ELSE 0 END)  AS lbudget,
                SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0)   ELSE 0 END)  AS cost_total,
                SUM(CASE WHEN omit=0 THEN COALESCE(efc,0)        ELSE 0 END)  AS efc
            FROM shots WHERE ep=?
            GROUP BY scene_code, location
            ORDER BY CAST(scene_code AS REAL), location
        ''', (ep,)).fetchall()

        if mode == 'replace':
            conn.execute('DELETE FROM sequences WHERE ep=? AND auto_sync=1', (ep,))

        for r in agg_rows:
            efc     = r['efc']     or 0
            lbudget = r['lbudget'] or 0
            conn.execute('''INSERT INTO sequences
                (ep, seq_name, location, omit, est_shots, current_cut,
                 lbudget, efc, variance_val, status, auto_sync)
                VALUES (?,?,?,0,?,?,?,?,?,?,1)''',
                (ep, r['scene_code'], r['location'],
                 r['est_shots'] or 0, r['current_cut'] or 0,
                 lbudget, efc, efc - lbudget, ''))
            inserted += 1

    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted, 'eps': eps})


@app.route('/api/sequences/<int:seq_id>', methods=['DELETE'])
def delete_sequence(seq_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM sequences WHERE id=?', (seq_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – budget history
# ---------------------------------------------------------------------------

@app.route('/api/history/<int:ep>', methods=['GET'])
def get_history(ep):
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute(
        'SELECT * FROM budget_history WHERE ep=? ORDER BY id DESC', (ep,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/history/<int:ep>', methods=['POST'])
def add_history(ep):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO budget_history
        (ep, record_date, version_label, script_v, edit_v, est_shots, edit_shots,
         est_budget, efc_budget, variance_val, status, est_reduction, reduction_notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (ep, d.get('record_date', datetime.now().strftime('%Y-%m-%d')),
         d.get('version_label', ''), d.get('script_v', ''), d.get('edit_v', ''),
         d.get('est_shots', 0), d.get('edit_shots', 0),
         d.get('est_budget', 0), d.get('efc_budget', 0),
         d.get('variance_val', 0), d.get('status', ''),
         d.get('est_reduction', 0), d.get('reduction_notes', '')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@app.route('/api/history/<int:hist_id>', methods=['DELETE'])
def delete_history(hist_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM budget_history WHERE id=?', (hist_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – VFX notes
# ---------------------------------------------------------------------------

@app.route('/api/notes', methods=['GET'])
def get_notes():
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute('SELECT * FROM vfx_notes ORDER BY item_num').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/notes', methods=['POST'])
def add_note():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    c = conn.cursor()
    max_item = conn.execute('SELECT COALESCE(MAX(item_num),0) FROM vfx_notes').fetchone()[0]
    c.execute('''INSERT INTO vfx_notes (item_num, author, note_text, note_date, resolved)
        VALUES (?,?,?,?,?)''',
        (max_item + 1, d.get('author', ''), d.get('note_text', ''),
         d.get('note_date', datetime.now().strftime('%Y-%m-%d')), d.get('resolved', 0)))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    conn = get_db()
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


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM vfx_notes WHERE id=?', (note_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – Assets
# ---------------------------------------------------------------------------

@app.route('/api/assets', methods=['GET'])
def get_assets():
    conn = get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    show_omit = request.args.get('omit', '0') == '1'
    q = 'SELECT * FROM assets'
    params = []
    conds = []
    if ep: conds.append('ep=?'); params.append(ep)
    if not show_omit: conds.append('omit=0')
    if conds: q += ' WHERE ' + ' AND '.join(conds)
    q += ' ORDER BY ep, orig_id, id'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d['vendor_bids'] = json.loads(d['vendor_bids'] or '{}')
        except: d['vendor_bids'] = {}
        result.append(d)
    return jsonify(result)


@app.route('/api/assets/vendors', methods=['GET'])
def get_asset_vendors():
    conn = get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    q = 'SELECT vendor_bids FROM assets WHERE omit=0'
    params = []
    if ep: q += ' AND ep=?'; params.append(ep)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    vendors, seen = [], set()
    for r in rows:
        try:
            for v in json.loads(r['vendor_bids'] or '{}').keys():
                if v not in seen: seen.add(v); vendors.append(v)
        except: pass
    return jsonify(vendors)


@app.route('/api/assets/summary', methods=['GET'])
def get_assets_summary():
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute('''
        SELECT ep,
               COUNT(CASE WHEN omit=0 THEN 1 END) AS asset_count,
               SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) AS est_budget,
               SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) AS actual_spend
        FROM assets GROUP BY ep ORDER BY ep
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['award_vendor', 'est_budget', 'actual_spend', 'notes', 'omit', 'turnover']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE assets SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [asset_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/assets/import', methods=['POST'])
def import_assets():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    f = request.files.get('file')
    if not f: return jsonify({'error': 'No file'}), 400
    if not f.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Use .xlsx files'}), 400

    mode = request.form.get('mode', 'replace')
    ep_filter = request.form.get('ep', type=int)

    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(f.read()), data_only=True)
    ws = wb.active if 'Assets' not in wb.sheetnames else wb['Assets']

    # Find header row (contains 'ASSET NAME')
    header_row_idx = None
    headers = []
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        vals = [str(v).strip() if v is not None else '' for v in row]
        if 'ASSET NAME' in vals or 'ITEM' in vals:
            header_row_idx = i
            headers = vals
            break
    if header_row_idx is None:
        return jsonify({'error': 'Could not find header row (needs ASSET NAME column)'}), 400

    # Map fixed columns
    col_map = {}
    vendor_cols = []
    fixed = {
        'ITEM': 'orig_id', 'EP': 'ep', 'SCENE #': 'scene_code',
        'TURNOVER': 'turnover', 'ASSET NAME': 'asset_name',
        'DESCRIPTION': 'description', 'REFERENCE / IMAGE': 'reference',
        'ASSET TYPE (ENVIRO/CHAR/CREATURE/ PROP/WEAPON, ETC)': 'asset_type',
        'ASSET TYPE': 'asset_type',
        'REPEAT ASSET(SEASON ASSET)': 'repeat_asset', 'REPEAT ASSET': 'repeat_asset',
        'HERO ID': 'hero_id', 'OMIT': 'omit', 'REF': 'ref', 'NOTES': 'notes',
        'LIDAR': 'lidar', 'PHOTOGRAMATRY': 'photogrammetry', 'PHOTOGRAMMETRY': 'photogrammetry',
        'ESTBUDGET': 'est_budget', 'ACTUAL SPEND': 'actual_spend',
        'AWARD VENDOR': 'award_vendor',
    }
    for i, h in enumerate(headers):
        hu = h.strip().upper()
        if hu in fixed:
            col_map[fixed[hu]] = i
        elif hu and not hu.startswith('VARIANCE') and i > col_map.get('award_vendor', -1):
            # Vendor column: after award_vendor, not a variance column
            if 'award_vendor' in col_map and i > col_map['award_vendor'] + 1:
                vendor_cols.append((i, h.strip()))

    if mode == 'replace':
        if ep_filter:
            conn.execute('DELETE FROM assets WHERE ep=?', (ep_filter,))
        else:
            conn.execute('DELETE FROM assets')

    def gv(field, row, default=None):
        idx = col_map.get(field)
        return row[idx] if idx is not None and idx < len(row) else default

    def flt(v, d=0.0):
        try: return float(v) if v is not None else d
        except: return d

    def nt(v, d=0):
        try: return int(float(v)) if v is not None else d
        except: return d

    def bl(v):
        return 1 if v and str(v).strip().lower() in ('true','1','yes','x') else 0

    inserted = 0
    for r in range(header_row_idx + 1, ws.max_row + 1):
        row = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
        if all(v is None for v in row): continue
        ep_val = gv('ep', row)
        if ep_val is None: continue
        try: ep_int = int(ep_val)
        except: continue
        if ep_filter and ep_int != ep_filter: continue

        bids = {}
        for vi, vname in vendor_cols:
            val = row[vi] if vi < len(row) else None
            if val is not None and str(val).strip() not in ('', '---'):
                try: bids[vname] = float(val)
                except: pass

        sc = gv('scene_code', row)
        asset_name = gv('asset_name', row)
        if sc is None and asset_name is None: continue

        conn.execute('''INSERT INTO assets
            (orig_id, ep, scene_code, turnover, asset_name, description, reference,
             asset_type, repeat_asset, hero_id, omit, ref, notes, lidar, photogrammetry,
             est_budget, actual_spend, award_vendor, vendor_bids)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (nt(gv('orig_id', row)),
             ep_int,
             str(sc).strip() if sc is not None else '',
             str(gv('turnover', row, '') or '').strip(),
             str(asset_name or '').strip(),
             str(gv('description', row, '') or '').strip(),
             str(gv('reference', row, '') or '').strip(),
             str(gv('asset_type', row, '') or '').strip(),
             bl(gv('repeat_asset', row)),
             bl(gv('hero_id', row)),
             bl(gv('omit', row)),
             str(gv('ref', row, '') or '').strip(),
             str(gv('notes', row, '') or '').strip(),
             bl(gv('lidar', row)),
             bl(gv('photogrammetry', row)),
             flt(gv('est_budget', row)),
             flt(gv('actual_spend', row)),
             str(gv('award_vendor', row, '') or '').strip(),
             json.dumps(bids)))
        inserted += 1

    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted})


@app.route('/api/assets/clear', methods=['DELETE'])
def clear_assets():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    ep = request.args.get('ep', type=int)
    if ep: conn.execute('DELETE FROM assets WHERE ep=?', (ep,))
    else:   conn.execute('DELETE FROM assets')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – Bid Compare
# ---------------------------------------------------------------------------

@app.route('/api/bidcompare', methods=['GET'])
def get_bidcompare():
    conn = get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    show_novfx = request.args.get('novfx', '0') == '1'
    if ep:
        if show_novfx:
            rows = conn.execute('SELECT * FROM bid_compare WHERE ep=? ORDER BY id', (ep,)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM bid_compare WHERE ep=? AND novfx=0 ORDER BY id', (ep,)).fetchall()
    else:
        if show_novfx:
            rows = conn.execute('SELECT * FROM bid_compare ORDER BY ep, id').fetchall()
        else:
            rows = conn.execute('SELECT * FROM bid_compare WHERE novfx=0 ORDER BY ep, id').fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d['vendor_bids'] = json.loads(d['vendor_bids'] or '{}')
        except Exception:
            d['vendor_bids'] = {}
        result.append(d)
    return jsonify(result)


@app.route('/api/bidcompare/vendors', methods=['GET'])
def get_bidcompare_vendors():
    conn = get_db()
    if not conn: return jsonify([])
    ep = request.args.get('ep', type=int)
    if ep:
        rows = conn.execute('SELECT vendor_bids FROM bid_compare WHERE ep=? AND novfx=0', (ep,)).fetchall()
    else:
        rows = conn.execute('SELECT vendor_bids FROM bid_compare WHERE novfx=0').fetchall()
    conn.close()
    vendors = []
    seen = set()
    for r in rows:
        try:
            bids = json.loads(r['vendor_bids'] or '{}')
            for v in bids.keys():
                if v not in seen:
                    seen.add(v)
                    vendors.append(v)
        except Exception:
            pass
    return jsonify(vendors)


@app.route('/api/bidcompare/import', methods=['POST'])
def import_bidcompare():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file'}), 400
    if not f.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Use .xlsx files'}), 400

    mode = request.form.get('mode', 'replace')
    ep_filter = request.form.get('ep', type=int)

    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(f.read()), data_only=True)
    ws = wb.active

    # Find header row (contains 'ID' or 'EP')
    header_row_idx = None
    headers = []
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        vals = [str(v).strip() if v is not None else '' for v in row]
        if 'ID' in vals and 'EP' in vals:
            header_row_idx = i
            headers = vals
            break
    if header_row_idx is None:
        return jsonify({'error': 'Could not find header row (needs ID and EP columns)'}), 400

    # Map column indices
    col_map = {}
    vendor_cols = []
    fixed = {'ID':'orig_id','EP':'ep','SC':'sc','SETTING':'setting','NOVFX':'novfx',
             'SCOUNT':'scount','EDIT COUNT':'edit_count','VFXTYPE':'vfxtype',
             'VERSION':'version','AWARD':'award','LOCKBUDGET':'lockbudget','EFC':'efc'}
    for i, h in enumerate(headers):
        hu = h.strip().upper()
        if hu in fixed:
            col_map[fixed[hu]] = i
        elif hu and hu not in ('', 'NONE') and i > max(col_map.values(), default=-1):
            # Only add as vendor if after EFC column
            if 'efc' in col_map and i > col_map['efc']:
                vendor_cols.append((i, h.strip()))

    if mode == 'replace':
        if ep_filter:
            conn.execute('DELETE FROM bid_compare WHERE ep=?', (ep_filter,))
        else:
            conn.execute('DELETE FROM bid_compare')

    inserted = 0
    for r in range(header_row_idx + 1, ws.max_row + 1):
        row = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
        if all(v is None for v in row):
            continue
        ep_val = row[col_map['ep']] if 'ep' in col_map and col_map['ep'] < len(row) else None
        if ep_val is None:
            continue
        try:
            ep_int = int(ep_val)
        except Exception:
            continue
        if ep_filter and ep_int != ep_filter:
            continue

        def gv(field, default=None):
            idx = col_map.get(field)
            if idx is None or idx >= len(row): return default
            return row[idx]

        def flt(v, default=0.0):
            try: return float(v) if v is not None and str(v) != '#REF!' else default
            except: return default

        def nt(v):
            try: return int(float(v)) if v is not None else 0
            except: return 0

        bids = {}
        for vi, vname in vendor_cols:
            val = row[vi] if vi < len(row) else None
            if val is not None and str(val).strip() not in ('', '---', 'None'):
                try: bids[vname] = float(val)
                except: pass

        novfx_val = gv('novfx')
        novfx = 1 if novfx_val and str(novfx_val).strip().lower() in ('true','1','yes') else 0

        conn.execute('''INSERT INTO bid_compare
            (orig_id, ep, sc, setting, novfx, scount, edit_count, vfxtype,
             version, award, lockbudget, efc, vendor_bids)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (nt(gv('orig_id')), ep_int,
             str(gv('sc', '')).strip() if gv('sc') is not None else '',
             str(gv('setting', '')).strip() if gv('setting') is not None else '',
             novfx, nt(gv('scount')), nt(gv('edit_count')),
             str(gv('vfxtype', '')).strip() if gv('vfxtype') is not None else '',
             nt(gv('version', 1)),
             str(gv('award', '')).strip() if gv('award') is not None else '',
             flt(gv('lockbudget')), flt(gv('efc')),
             json.dumps(bids)))
        inserted += 1

    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted})


@app.route('/api/bidcompare/<int:bid_id>', methods=['PUT'])
def update_bidcompare(bid_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['award', 'lockbudget', 'efc', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE bid_compare SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [bid_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/bidcompare/clear', methods=['DELETE'])
def clear_bidcompare():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    ep = request.args.get('ep', type=int)
    if ep:
        conn.execute('DELETE FROM bid_compare WHERE ep=?', (ep,))
    else:
        conn.execute('DELETE FROM bid_compare')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# API – Vendor Tracker
# ---------------------------------------------------------------------------

def _sfloat(v):
    """Safe float — returns None for error strings/None."""
    if v is None: return None
    s = str(v).strip()
    if not s or s.startswith('#') or s.startswith('\u26a0'): return None
    try: return float(s)
    except: return None


@app.route('/api/vendortracker', methods=['GET', 'POST'])
def vendortracker_collection():
    conn = get_db()
    if not conn: return jsonify([]) if request.method == 'GET' else jsonify({'error': 'No project'}), 400
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM vendor_tracker ORDER BY ep, vendor').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    # POST — create new row
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO vendor_tracker
        (vendor, region, ep, asset_award, award_ep, tot_award,
         paid, pending, remaining,
         tax_reb, gross_local, gross_usd, sale_tax_amount,
         gross_plus_tax, tax_rebate_amt, net_after_rebate, final_price)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d.get('vendor',''), d.get('region',''),
         d.get('ep'), d.get('asset_award'), d.get('award_ep'), d.get('tot_award'),
         d.get('paid', 0), d.get('pending', 0), d.get('remaining'),
         d.get('tax_reb'), d.get('gross_local'), d.get('gross_usd'),
         d.get('sale_tax_amount'), d.get('gross_plus_tax'),
         d.get('tax_rebate_amt'), d.get('net_after_rebate'), d.get('final_price')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@app.route('/api/vendortracker/<int:row_id>', methods=['PUT'])
def update_vendortracker(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['vendor', 'region', 'ep', 'asset_award', 'award_ep', 'tot_award',
               'paid', 'pending', 'remaining', 'tax_reb', 'gross_local', 'gross_usd',
               'sale_tax_amount', 'gross_plus_tax', 'tax_rebate_amt', 'net_after_rebate', 'final_price']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE vendor_tracker SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [row_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/vendortracker/<int:row_id>', methods=['DELETE'])
def delete_vendortracker(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM vendor_tracker WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/vendortracker/clear', methods=['DELETE'])
def clear_vendortracker():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    conn.execute('DELETE FROM vendor_tracker')
    conn.execute('DELETE FROM invoice_log')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


def sync_tracker_paid(conn, vendor, ep):
    """Recalculate paid/pending/remaining from invoices and update tracker row."""
    if not vendor or ep is None:
        return
    tracker = conn.execute(
        'SELECT id, tot_award FROM vendor_tracker WHERE UPPER(vendor)=UPPER(?) AND ep=?',
        (vendor, ep)
    ).fetchone()
    if not tracker:
        return
    paid_sum = conn.execute(
        'SELECT COALESCE(SUM(amount),0) FROM invoice_log WHERE UPPER(vendor)=UPPER(?) AND episode=? AND UPPER(status)="PAID"',
        (vendor, ep)
    ).fetchone()[0]
    pending_sum = conn.execute(
        'SELECT COALESCE(SUM(amount),0) FROM invoice_log WHERE UPPER(vendor)=UPPER(?) AND episode=? AND UPPER(status) IN ("PENDING","APPROVED")',
        (vendor, ep)
    ).fetchone()[0]
    tot_award = tracker['tot_award'] or 0
    remaining = tot_award - paid_sum
    conn.execute(
        'UPDATE vendor_tracker SET paid=?, pending=?, remaining=? WHERE id=?',
        (paid_sum, pending_sum, remaining, tracker['id'])
    )


@app.route('/api/invoicelog', methods=['GET', 'POST'])
def invoicelog_collection():
    conn = get_db()
    if not conn: return jsonify([]) if request.method == 'GET' else jsonify({'error': 'No project'}), 400
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM invoice_log ORDER BY episode, id').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    # POST — create new row
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO invoice_log
        (vendor, episode, inv_num, inv_date, amount, status, approve_date, notes)
        VALUES (?,?,?,?,?,?,?,?)''',
        (d.get('vendor',''), d.get('episode'), d.get('inv_num',''),
         d.get('inv_date',''), d.get('amount', 0), d.get('status',''),
         d.get('approve_date',''), d.get('notes','')))
    new_id = c.lastrowid
    sync_tracker_paid(conn, d.get('vendor',''), d.get('episode'))
    conn.commit()
    conn.close()
    return jsonify({'id': new_id})


@app.route('/api/invoicelog/<int:row_id>', methods=['PUT'])
def update_invoicelog(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    # fetch current row so we can sync old vendor/ep if they change
    old = conn.execute('SELECT vendor, episode FROM invoice_log WHERE id=?', (row_id,)).fetchone()
    d = request.json
    allowed = ['vendor', 'episode', 'inv_num', 'inv_date', 'amount', 'status', 'approve_date', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE invoice_log SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [row_id])
    # sync tracker for old vendor/ep and new vendor/ep (handles renames)
    new_vendor  = updates.get('vendor',  old['vendor']  if old else None)
    new_episode = updates.get('episode', old['episode'] if old else None)
    if old:
        sync_tracker_paid(conn, old['vendor'], old['episode'])
    if new_vendor != (old['vendor'] if old else None) or new_episode != (old['episode'] if old else None):
        sync_tracker_paid(conn, new_vendor, new_episode)
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/invoicelog/<int:row_id>', methods=['DELETE'])
def delete_invoicelog(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    old = conn.execute('SELECT vendor, episode FROM invoice_log WHERE id=?', (row_id,)).fetchone()
    conn.execute('DELETE FROM invoice_log WHERE id=?', (row_id,))
    if old:
        sync_tracker_paid(conn, old['vendor'], old['episode'])
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/vendortracker/import', methods=['POST'])
def import_vendortracker():
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    f = request.files.get('file')
    if not f: return jsonify({'error': 'No file'}), 400
    if not f.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Use .xlsx files'}), 400

    mode = request.form.get('mode', 'replace')
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(f.read()), data_only=True)

    tracker_inserted = 0
    invoice_inserted = 0

    # ── VENDORINVTRACK sheet ────────────────────────────────────────────
    if 'VENDORINVTRACK' in wb.sheetnames:
        ws = wb['VENDORINVTRACK']
        rows = list(ws.iter_rows(values_only=True))
        # Find the TRACKING section header row (contains 'VENDOR' and 'EP' and 'PAID')
        track_row = None
        for i, row in enumerate(rows):
            vals = [str(v).strip().upper() if v else '' for v in row]
            if 'VENDOR' in vals and 'PAID' in vals and 'PENDING' in vals:
                track_row = i
                break

        if track_row is not None:
            headers = [str(v).strip() if v else '' for v in rows[track_row]]
            # Build hmap with FIRST occurrence wins (handles duplicate VENDOR/REG)
            hmap = {}
            for i, h in enumerate(headers):
                hu = h.upper()
                if hu and hu not in hmap:
                    hmap[hu] = i
            # Find second VENDOR column for right (tax) section
            vendor_indices = [i for i, h in enumerate(headers) if h.strip().upper() == 'VENDOR']
            right_offset = vendor_indices[1] if len(vendor_indices) > 1 else None

            if mode == 'replace':
                conn.execute('DELETE FROM vendor_tracker')

            for row in rows[track_row + 1:]:
                if all(v is None for v in row): continue
                v_idx = hmap.get('VENDOR', 1)
                vendor = row[v_idx] if v_idx < len(row) else None
                if not vendor or str(vendor).strip() == '': continue
                vendor = str(vendor).strip()

                reg_idx = hmap.get('REG', 2)
                ep_idx  = hmap.get('EP', 3)
                ep_val  = row[ep_idx] if ep_idx < len(row) else None
                try:    ep_int = int(ep_val) if ep_val is not None else None
                except: ep_int = None

                def gv(key, default=None):
                    idx = hmap.get(key.upper())
                    return row[idx] if idx is not None and idx < len(row) else default

                def gv_right(offset, default=None):
                    if right_offset is None: return default
                    idx = right_offset + offset
                    return row[idx] if idx < len(row) else default

                tot_key = next((k for k in hmap if 'TOT' in k and 'AWARD' in k), None)
                rem_key = next((k for k in hmap if 'REMAIN' in k), None)

                conn.execute('''INSERT INTO vendor_tracker
                    (vendor, region, ep, asset_award, award_ep, tot_award,
                     paid, pending, remaining,
                     tax_reb, gross_local, gross_usd, sale_tax_amount,
                     gross_plus_tax, tax_rebate_amt, net_after_rebate, final_price)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (vendor,
                     str(row[reg_idx]).strip() if reg_idx < len(row) and row[reg_idx] else '',
                     ep_int,
                     _sfloat(gv('ASSET_AWARD')),
                     _sfloat(gv('AWARD_EP')),
                     _sfloat(gv(tot_key) if tot_key else None),
                     _sfloat(gv('PAID')) or 0,
                     _sfloat(gv('PENDING')) or 0,
                     _sfloat(gv(rem_key) if rem_key else None),
                     _sfloat(gv_right(2)),   # TAX_REB
                     _sfloat(gv_right(3)),   # GROSS(local currency)
                     _sfloat(gv_right(4)),   # GROSS(usd)
                     _sfloat(gv_right(5)),   # SALE TAX amount
                     _sfloat(gv_right(6)),   # Gross+salestax
                     _sfloat(gv_right(7)),   # Tax Rebate
                     _sfloat(gv_right(8)),   # NET(after tax rebate)
                     _sfloat(gv_right(10)),  # Final Price
                    ))
                tracker_inserted += 1

    # ── INVOICELOG sheet ───────────────────────────────────────────────
    if 'INVOICELOG' in wb.sheetnames:
        ws2 = wb['INVOICELOG']
        rows2 = list(ws2.iter_rows(values_only=True))
        # Find header row with VENDOR, INV#, AMOUNT
        hdr_row = None
        for i, row in enumerate(rows2):
            vals = [str(v).strip().upper() if v else '' for v in row]
            if 'VENDOR' in vals and 'AMOUNT' in vals:
                hdr_row = i
                break

        if hdr_row is not None:
            headers2 = [str(v).strip().upper() if v else '' for v in rows2[hdr_row]]
            h2map = {h: i for i, h in enumerate(headers2) if h}

            if mode == 'replace':
                conn.execute('DELETE FROM invoice_log')

            def g2(key, row):
                idx = h2map.get(key)
                return row[idx] if idx is not None and idx < len(row) else None

            def fmt_date(v):
                if v is None: return None
                if hasattr(v, 'strftime'): return v.strftime('%Y-%m-%d')
                return str(v).strip()

            for row in rows2[hdr_row + 1:]:
                if all(v is None for v in row): continue
                vendor = g2('VENDOR', row)
                if not vendor or str(vendor).strip() == '': continue
                conn.execute('''INSERT INTO invoice_log
                    (vendor, episode, inv_num, inv_date, amount, status, approve_date, notes)
                    VALUES (?,?,?,?,?,?,?,?)''',
                    (str(vendor).strip(),
                     int(g2('EPISODE', row)) if g2('EPISODE', row) is not None else None,
                     str(g2('INV#', row) or '').strip(),
                     fmt_date(g2('INV_DATE', row)),
                     _sfloat(g2('AMOUNT', row)) or 0,
                     str(g2('STATUS', row) or '').strip(),
                     fmt_date(g2('APPROVE DATE', row)),
                     str(g2('NOTES', row) or '').strip()))
                invoice_inserted += 1

    conn.commit()
    conn.close()
    return jsonify({'tracker_inserted': tracker_inserted, 'invoice_inserted': invoice_inserted})


# ---------------------------------------------------------------------------
# API – Import Excel
# ---------------------------------------------------------------------------

COL_MAP = {
    'ep':'ep','id':'shot_num','shot_num':'shot_num','shot #':'shot_num','#':'shot_num',
    'sc':'scene_code','scene_code':'scene_code','scene #':'scene_code',
    's_code':'s_code','shot code':'s_code',
    'loc':'location','location':'location',
    'ext/int':'ext_int','ext_int':'ext_int','int/ext':'ext_int',
    'pg':'pg','page':'pg','img':'img','image':'img',
    'asset':'asset','assets':'asset',
    'script description':'script_desc','script_desc':'script_desc','script desc':'script_desc',
    'vfx description':'vfx_desc','vfx_desc':'vfx_desc','vfx desc':'vfx_desc',
    'type':'shot_type','shot_type':'shot_type',
    'omit':'omit',
    'overall shot history  showrunner/director/ep/pd notes \nfor internal purpose only':'history_notes',
    'overall shot history  showrunner/director/ep/pd notes \nfor internal purpose only ':'history_notes',
    'history':'history_notes','history_notes':'history_notes','shot history':'history_notes',
    'director notes':'history_notes',
    'shot(est)':'shot_est','shot est':'shot_est','shot_est':'shot_est','shots':'shot_est',
    'cost(est)':'cost_est','cost est':'cost_est','cost_est':'cost_est','cost':'cost_est',
    'budget(est)':'budget_est','budget est':'budget_est','budget_est':'budget_est','budget':'budget_est',
    'award(vendor)':'award_vendor','award vendor':'award_vendor','award_vendor':'award_vendor','vendor':'award_vendor',
    'edit_count':'edit_count','edit count':'edit_count','edit #':'edit_count','edit_#':'edit_count',
    'budget(awardcost)':'budget_award_cost','budget award cost':'budget_award_cost',
    'efc':'efc',
    'variance':None,
    'notes':'notes',
}

DB_FIELDS = ['shot_num','scene_code','s_code','location','ext_int','pg','img',
             'asset','script_desc','vfx_desc','shot_type','omit','history_notes',
             'shot_est','cost_est','budget_est','award_vendor','edit_count',
             'budget_award_cost','efc','notes']


def _parse_rows_from_excel(file_bytes, ep, sheet_hint=None):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    target = None
    if sheet_hint and sheet_hint in wb.sheetnames:
        target = wb[sheet_hint]
    if not target:
        ep_str = str(ep)
        for name in wb.sheetnames:
            if ep_str in name:
                target = wb[name]
                break
    if not target:
        target = wb.active

    header_row_idx = None
    headers = []
    for i, row in enumerate(target.iter_rows(values_only=True), 1):
        if len([c for c in row if c is not None]) >= 4:
            headers = [str(c).strip().lower() if c is not None else '' for c in row]
            header_row_idx = i
            break
    if header_row_idx is None:
        return [], wb.sheetnames

    col_to_field = {}
    for idx, h in enumerate(headers):
        field = COL_MAP.get(h)
        if field:
            col_to_field[idx] = field

    rows_out = []
    for row in target.iter_rows(min_row=header_row_idx + 1, values_only=True):
        if all(c is None for c in row):
            continue
        rec = {'ep': int(ep)}
        for idx, field in col_to_field.items():
            if field == 'ep':
                continue
            val = row[idx] if idx < len(row) else None
            if val is not None:
                if field == 'omit':
                    rec[field] = 1 if str(val).strip().lower() in ('true','1','yes','x','omit') else 0
                elif field in ('shot_est', 'edit_count'):
                    try: rec[field] = int(float(val))
                    except: rec[field] = 0
                elif field in ('cost_est', 'budget_est', 'budget_award_cost', 'efc'):
                    try: rec[field] = float(val)
                    except: rec[field] = 0.0
                else:
                    rec[field] = str(val).strip() if not isinstance(val, str) else val.strip()
            else:
                rec.setdefault(field, None)
        if any(rec.get(f) for f in ('shot_num','scene_code','vfx_desc','script_desc','cost_est')):
            rows_out.append(rec)
    return rows_out, wb.sheetnames


@app.route('/api/import/preview/<int:ep>', methods=['POST'])
def import_preview(ep):
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file'}), 400
    fname = f.filename.lower()
    file_bytes = f.read()
    if fname.endswith('.xlsx') or fname.endswith('.xls'):
        sheet = request.form.get('sheet', '')
        rows, sheets = _parse_rows_from_excel(file_bytes, ep, sheet or None)
        return jsonify({'rows': rows, 'sheets': sheets, 'count': len(rows)})
    return jsonify({'error': 'Use .xlsx files'}), 400


@app.route('/api/import/commit/<int:ep>', methods=['POST'])
def import_commit(ep):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    rows = d.get('rows', [])
    mode = d.get('mode', 'append')
    if not rows:
        return jsonify({'error': 'No rows'}), 400
    if mode == 'replace':
        conn.execute('DELETE FROM shots WHERE ep=?', (ep,))
    inserted = 0
    for rec in rows:
        rec['ep'] = ep
        fields = [f for f in DB_FIELDS if f in rec]
        fields_ep = ['ep'] + fields
        placeholders = ','.join('?' for _ in fields_ep)
        values = [rec.get(f) for f in fields_ep]
        conn.execute(f"INSERT INTO shots ({','.join(fields_ep)}) VALUES ({placeholders})", values)
        inserted += 1
    conn.commit()
    conn.close()
    return jsonify({'inserted': inserted, 'mode': mode})


# ---------------------------------------------------------------------------

def migrate_db_schema():
    """Add any missing columns/tables to existing project databases."""
    conn = get_projects_db()
    projects = conn.execute('SELECT db_path FROM projects').fetchall()
    conn.close()
    for proj in projects:
        try:
            pconn = sqlite3.connect(proj['db_path'])
            cols = [r[1] for r in pconn.execute('PRAGMA table_info(sequences)').fetchall()]
            if 'auto_sync' not in cols:
                pconn.execute('ALTER TABLE sequences ADD COLUMN auto_sync INTEGER DEFAULT 0')
                pconn.commit()
            # Add bid_compare table if missing
            tables = [r[0] for r in pconn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if 'assets' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, orig_id INTEGER, ep INTEGER,
                    scene_code TEXT, turnover TEXT, asset_name TEXT, description TEXT,
                    reference TEXT, asset_type TEXT, repeat_asset INTEGER DEFAULT 0,
                    hero_id INTEGER DEFAULT 0, omit INTEGER DEFAULT 0, ref TEXT,
                    notes TEXT, lidar INTEGER DEFAULT 0, photogrammetry INTEGER DEFAULT 0,
                    est_budget REAL DEFAULT 0, actual_spend REAL DEFAULT 0,
                    award_vendor TEXT, vendor_bids TEXT
                )''')
                pconn.commit()
            if 'bid_compare' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS bid_compare (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    orig_id     INTEGER,
                    ep          INTEGER,
                    sc          TEXT,
                    setting     TEXT,
                    novfx       INTEGER DEFAULT 0,
                    scount      INTEGER DEFAULT 0,
                    edit_count  INTEGER DEFAULT 0,
                    vfxtype     TEXT,
                    version     INTEGER DEFAULT 1,
                    award       TEXT,
                    lockbudget  REAL DEFAULT 0,
                    efc         REAL DEFAULT 0,
                    vendor_bids TEXT
                )''')
                pconn.commit()
            if 'vendor_tracker' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS vendor_tracker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor TEXT, region TEXT, ep INTEGER,
                    asset_award REAL, award_ep REAL, tot_award REAL,
                    paid REAL DEFAULT 0, pending REAL DEFAULT 0, remaining REAL,
                    tax_reb REAL, gross_local REAL, gross_usd REAL,
                    sale_tax_amount REAL, gross_plus_tax REAL,
                    tax_rebate_amt REAL, net_after_rebate REAL, final_price REAL
                )''')
                pconn.commit()
            if 'invoice_log' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS invoice_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor TEXT, episode INTEGER, inv_num TEXT,
                    inv_date TEXT, amount REAL DEFAULT 0,
                    status TEXT, approve_date TEXT, notes TEXT
                )''')
                pconn.commit()
            if 'budget_scenario' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS budget_scenario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, scenario_type TEXT DEFAULT 'Conservative',
                    ep INTEGER DEFAULT 101, tax_pct REAL DEFAULT 0,
                    eligible_pct REAL DEFAULT 0, net_cost REAL DEFAULT 0, notes TEXT DEFAULT ''
                )''')
                pconn.commit()
            if 'ep_forecast' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS ep_forecast (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL UNIQUE,
                    contingency REAL DEFAULT 0.2, budget REAL DEFAULT 0,
                    award REAL DEFAULT 0, eligible REAL DEFAULT 0,
                    global_rebate_pct REAL DEFAULT 0, global_pct REAL DEFAULT 0,
                    notes TEXT DEFAULT ''
                )''')
                # seed EP rows 101-108
                for _ep in range(101, 109):
                    pconn.execute('INSERT OR IGNORE INTO ep_forecast (ep) VALUES (?)', (_ep,))
                pconn.commit()
            if 'vendor_forecast' not in tables:
                pconn.execute('''CREATE TABLE IF NOT EXISTS vendor_forecast (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT DEFAULT '',
                    ep INTEGER DEFAULT 101, gross_local REAL DEFAULT 0,
                    gross_usd REAL DEFAULT 0, region TEXT DEFAULT '',
                    eligible_pct REAL DEFAULT 0, rebate_pct REAL DEFAULT 0,
                    notes TEXT DEFAULT ''
                )''')
                pconn.commit()
            # Add region_mix columns if missing
            epf_cols = [r[1] for r in pconn.execute('PRAGMA table_info(ep_forecast)').fetchall()]
            if 'region_mix' not in epf_cols:
                pconn.execute("ALTER TABLE ep_forecast ADD COLUMN region_mix TEXT DEFAULT '[]'")
                pconn.commit()
            sc_cols = [r[1] for r in pconn.execute('PRAGMA table_info(budget_scenario)').fetchall()]
            if 'region_mix' not in sc_cols:
                pconn.execute("ALTER TABLE budget_scenario ADD COLUMN region_mix TEXT DEFAULT '[]'")
                pconn.commit()
            pconn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Budget Scenario & Forecast
# ---------------------------------------------------------------------------

@app.route('/scenario')
def scenario():
    redir = require_project()
    if redir: return redir
    return render_template('scenario.html')


@app.route('/api/budget_scenario', methods=['GET', 'POST'])
def budget_scenario_collection():
    conn = get_db()
    if not conn: return jsonify([]) if request.method == 'GET' else jsonify({'error': 'No project'}), 400
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM budget_scenario ORDER BY id').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO budget_scenario (scenario_type, ep, tax_pct, eligible_pct, net_cost, notes, region_mix)
                 VALUES (?,?,?,?,?,?,?)''',
              (d.get('scenario_type','Conservative'), d.get('ep', 101),
               d.get('tax_pct', 0), d.get('eligible_pct', 0),
               d.get('net_cost', 0), d.get('notes', ''), d.get('region_mix', '[]')))
    new_id = c.lastrowid
    conn.commit(); conn.close()
    return jsonify({'id': new_id})


@app.route('/api/budget_scenario/<int:row_id>', methods=['PUT', 'DELETE'])
def budget_scenario_row(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    if request.method == 'DELETE':
        conn.execute('DELETE FROM budget_scenario WHERE id=?', (row_id,))
        conn.commit(); conn.close()
        return jsonify({'status': 'ok'})
    d = request.json
    allowed = ['scenario_type', 'ep', 'tax_pct', 'eligible_pct', 'net_cost', 'notes', 'region_mix']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE budget_scenario SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [row_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/ep_forecast', methods=['GET'])
def ep_forecast_collection():
    conn = get_db()
    if not conn: return jsonify([])
    rows = conn.execute('SELECT * FROM ep_forecast ORDER BY ep').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/ep_forecast/<int:row_id>', methods=['PUT'])
def update_ep_forecast(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    d = request.json
    allowed = ['contingency', 'budget', 'award', 'eligible', 'region_mix', 'global_pct', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE ep_forecast SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [row_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/api/vendor_forecast', methods=['GET', 'POST'])
def vendor_forecast_collection():
    conn = get_db()
    if not conn: return jsonify([]) if request.method == 'GET' else jsonify({'error': 'No project'}), 400
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM vendor_forecast ORDER BY ep, vendor').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json
    c = conn.cursor()
    c.execute('''INSERT INTO vendor_forecast (vendor, ep, gross_local, gross_usd, region, eligible_pct, rebate_pct, notes)
                 VALUES (?,?,?,?,?,?,?,?)''',
              (d.get('vendor',''), d.get('ep', 101), d.get('gross_local', 0), d.get('gross_usd', 0),
               d.get('region',''), d.get('eligible_pct', 0), d.get('rebate_pct', 0), d.get('notes','')))
    new_id = c.lastrowid
    conn.commit(); conn.close()
    return jsonify({'id': new_id})


@app.route('/api/vendor_forecast/<int:row_id>', methods=['PUT', 'DELETE'])
def vendor_forecast_row(row_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'No project'}), 400
    if request.method == 'DELETE':
        conn.execute('DELETE FROM vendor_forecast WHERE id=?', (row_id,))
        conn.commit(); conn.close()
        return jsonify({'status': 'ok'})
    d = request.json
    allowed = ['vendor', 'ep', 'gross_local', 'gross_usd', 'region', 'eligible_pct', 'rebate_pct', 'notes']
    updates = {k: d[k] for k in allowed if k in d}
    if updates:
        sql = 'UPDATE vendor_forecast SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn.execute(sql, list(updates.values()) + [row_id])
        conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


def migrate_legacy_db():
    """Register vfx_system.db as a project if it exists and isn't registered yet."""
    legacy_path = os.path.join(BASE_DIR, 'vfx_system.db')
    if not os.path.exists(legacy_path):
        return
    conn = get_projects_db()
    already = conn.execute(
        "SELECT id FROM projects WHERE db_filename='vfx_system.db'"
    ).fetchone()
    if not already:
        conn.execute('''INSERT INTO projects
            (name, season, db_filename, db_path, ep_start, ep_end, description, last_opened)
            VALUES (?,?,?,?,?,?,?,?)''',
            ('SIDEWINDER', 'S1', 'vfx_system.db', legacy_path, 101, 108,
             'Migrated legacy project', datetime.now().isoformat()))
        conn.commit()
    conn.close()


if __name__ == '__main__':
    init_projects_db()
    migrate_legacy_db()
    migrate_db_schema()
    print('\n  VFX Budget System  >>  http://localhost:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
