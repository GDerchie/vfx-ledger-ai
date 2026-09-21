"""routes/projects.py — Project management Blueprint."""
import os
import secrets
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import core

bp = Blueprint('projects', __name__)


@bp.route('/')
def home():
    if session.get('project_db') and os.path.exists(session['project_db']):
        return redirect(url_for('episodes.distribution'))
    conn = core.get_projects_db()
    proj = conn.execute(
        'SELECT * FROM projects WHERE last_opened IS NOT NULL ORDER BY last_opened DESC LIMIT 1'
    ).fetchone()
    conn.close()
    if proj and os.path.exists(proj['db_path']):
        return redirect(url_for('projects.open_project', project_id=proj['id']))
    return render_template('home.html')


@bp.route('/projects')
def project_list():
    return render_template('home.html')


@bp.route('/api/projects', methods=['GET'])
def list_projects():
    conn = core.get_projects_db()
    rows = conn.execute(
        'SELECT * FROM projects ORDER BY last_opened DESC NULLS LAST, created_at DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/projects', methods=['POST'])
def create_project():
    d = request.json
    name     = d.get('name', '').strip().upper()
    season   = d.get('season', 'S1').strip().upper()
    ep_start = int(d.get('ep_start', 101))
    ep_end   = int(d.get('ep_end', 108))
    desc     = d.get('description', '')
    if not name:
        return jsonify({'error': 'Project name required'}), 400
    db_filename = f"{name}_{season}.vfxdb"
    db_path     = os.path.join(core.PROJECTS_DIR, db_filename)
    if os.path.exists(db_path):
        base = db_filename.replace('.vfxdb', '')
        i = 2
        while os.path.exists(os.path.join(core.PROJECTS_DIR, f"{base}_v{i}.vfxdb")):
            i += 1
        db_filename = f"{base}_v{i}.vfxdb"
        db_path     = os.path.join(core.PROJECTS_DIR, db_filename)
    core.init_project_db(db_path, ep_start, ep_end)
    conn = core.get_projects_db()
    c = conn.cursor()
    c.execute('''INSERT INTO projects
        (name, season, db_filename, db_path, ep_start, ep_end, description)
        VALUES (?,?,?,?,?,?,?)''',
        (name, season, db_filename, db_path, ep_start, ep_end, desc))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': new_id, 'db_filename': db_filename})


@bp.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    d = request.json
    allowed = ['name', 'season', 'description']
    updates = {k: d[k] for k in allowed if k in d}
    if 'name' in updates:
        updates['name'] = updates['name'].strip().upper()
    if updates:
        sql = 'UPDATE projects SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?'
        conn = core.get_projects_db()
        conn.execute(sql, list(updates.values()) + [project_id])
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})


@bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = core.get_projects_db()
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


@bp.route('/projects/<int:project_id>/open')
def open_project(project_id):
    conn = core.get_projects_db()
    proj = conn.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
    if not proj:
        conn.close()
        return redirect(url_for('projects.home'))
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
    return redirect(url_for('episodes.distribution'))


@bp.route('/projects/close')
def close_project():
    session.clear()
    return redirect(url_for('projects.home'))


# ── Multi-project compare ─────────────────────────────────────────────────────

@bp.route('/api/projects/compare', methods=['GET'])
def compare_projects():
    """
    Compare season-level KPIs across all projects.
    Returns list of projects with: shots, est, efc, variance, vendor_count, risk.
    Optional ?ids=1,2,3 to limit to specific project IDs.
    """
    ids_param = request.args.get('ids', '')
    id_filter = [int(i) for i in ids_param.split(',') if i.strip().isdigit()] if ids_param else []

    pconn = core.get_projects_db()
    q     = 'SELECT * FROM projects ORDER BY name, season'
    projs = pconn.execute(q).fetchall()
    pconn.close()

    results = []
    for proj in projs:
        if id_filter and proj['id'] not in id_filter:
            continue
        if not os.path.exists(proj['db_path']):
            results.append({'id': proj['id'], 'name': proj['name'], 'season': proj['season'],
                            'error': 'db not found'})
            continue
        try:
            import sqlite3
            conn = sqlite3.connect(proj['db_path'])
            conn.row_factory = sqlite3.Row
            agg = conn.execute('''
                SELECT COUNT(CASE WHEN omit=0 THEN 1 END) as shots,
                       COUNT(DISTINCT CASE WHEN omit=0 AND award_vendor IS NOT NULL
                             AND award_vendor!='' THEN award_vendor END) as vendors,
                       SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) as est,
                       SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) as efc
                FROM shots
            ''').fetchone()
            aa = conn.execute('''
                SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) as ae,
                       SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) as af
                FROM assets
            ''').fetchone()
            pending = conn.execute(
                "SELECT COALESCE(SUM(amount),0) as p FROM invoice_log "
                "WHERE UPPER(status) IN ('PENDING','APPROVED')"
            ).fetchone()
            conn.close()

            est = (agg['est'] or 0) + (aa['ae'] or 0 if aa else 0)
            efc = (agg['efc'] or 0) + (aa['af'] or 0 if aa else 0)
            results.append({
                'id':            proj['id'],
                'name':          proj['name'],
                'season':        proj['season'],
                'shots':         agg['shots']   or 0,
                'vendors':       agg['vendors'] or 0,
                'est':           est,
                'efc':           efc,
                'variance':      efc - est,
                'variance_pct':  round((efc / est - 1) * 100, 1) if est else 0,
                'pending_invoices': pending['p'] if pending else 0,
                'ep_start':      proj['ep_start'],
                'ep_end':        proj['ep_end'],
                'last_opened':   proj['last_opened'],
            })
        except Exception as e:
            results.append({'id': proj['id'], 'name': proj['name'],
                            'season': proj['season'], 'error': str(e)})

    return jsonify(results)


# ── Slack digest ──────────────────────────────────────────────────────────────

@bp.route('/api/slack/digest', methods=['POST'])
def slack_digest():
    """
    Build and optionally send the weekly Slack budget digest for the active project.
    POST body: { "send": true/false }  — default send=false (preview only)
    """
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    from services.slack import build_digest, send_digest
    d       = request.json or {}
    do_send = d.get('send', False)

    proj_name = session.get('project_name', 'Unknown')
    season    = session.get('project_season', '')

    if do_send:
        msg = send_digest(conn, proj_name, season)
        conn.close()
        return jsonify({'status': 'sent', 'message': msg})
    else:
        msg = build_digest(conn, proj_name, season)
        conn.close()
        return jsonify({'status': 'preview', 'message': msg})


# ── API token auth ────────────────────────────────────────────────────────────

@bp.route('/api/auth/token', methods=['POST'])
def generate_token():
    """
    Generate a long-lived API token for headless access.
    POST body: { "password": "..." }
    Returns { "token": "vfx_…" }
    The token is stored (hashed) in auth_config.json and accepted by the auth middleware.
    """
    d        = request.json or {}
    password = d.get('password', '')
    if not core._check_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    token     = 'vfx_' + secrets.token_hex(24)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    cfg = core._load_auth_config()
    tokens = cfg.get('api_tokens', [])
    tokens.append({'hash': token_hash, 'created': datetime.now().isoformat()})
    cfg['api_tokens'] = tokens[-20:]   # keep last 20 tokens
    core._save_auth_config(cfg)

    return jsonify({'token': token, 'note': 'Send as Authorization: Bearer <token>'})
