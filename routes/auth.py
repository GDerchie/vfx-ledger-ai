"""routes/auth.py — Session authentication Blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session
import core

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if core.check_password(pw):
            session['authenticated'] = True
            next_url = request.args.get('next') or url_for('projects.project_list')
            return redirect(next_url)
        return render_template('login.html', error='Incorrect password.')
    return render_template('login.html', error=None)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/api/auth/config', methods=['GET'])
def auth_config_get():
    from flask import jsonify
    cfg = core._load_auth_config()
    return jsonify({'enabled': cfg.get('enabled', False)})


@bp.route('/api/auth/config', methods=['PUT'])
def auth_config_put():
    from flask import jsonify
    d = request.json or {}
    cfg = {'enabled': bool(d.get('enabled', False)),
           'password': d.get('password', '').strip()}
    core._save_auth_config(cfg)
    return jsonify({'status': 'ok'})
