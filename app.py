"""
app.py — VFX Budget System entry point.
Creates the Flask app, wires shared state, registers all Blueprints.
"""
import os
from flask import Flask, g
import core

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('VFX_SECRET_KEY', 'vfx-budget-system-2026')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Optional: API response caching
try:
    from flask_caching import Cache as _Cache
    _real_cache = _Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
    core.cache = _real_cache
    import services.db as _sdb
    _sdb.cache = _real_cache
except ImportError:
    print('[WARNING] flask-caching not installed — caching disabled.')

# Initialize LLM result cache
import services.db as _sdb
import llm.cache as llm_cache
llm_cache.init_cache(_sdb.PROJECTS_DB)

# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------
@app.teardown_appcontext
def close_db(e=None):
    core.close_db_connections()

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------
from routes.auth        import bp as auth_bp
from routes.projects    import bp as projects_bp
from routes.episodes    import bp as episodes_bp
from routes.notes       import bp as notes_bp
from routes.assets      import bp as assets_bp
from routes.vendors     import bp as vendors_bp
from routes.settings_bp import bp as settings_bp
from routes.audit       import bp as audit_bp
from routes.dashboard   import bp as dashboard_bp
from routes.optimizer   import bp as optimizer_bp
from jobs.api           import bp as jobs_bp
from importers.api      import bp as importers_bp
from routes.reports     import bp as reports_bp
from routes.export      import bp as export_bp
from routes.game_theory import bp as game_theory_bp

app.register_blueprint(auth_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(episodes_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(vendors_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(optimizer_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(importers_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(export_bp)
app.register_blueprint(game_theory_bp)

# ---------------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------------
_PUBLIC_PATHS = {'/login', '/logout', '/static'}

@app.before_request
def require_auth():
    from flask import request, session, redirect, url_for
    path = request.path
    if any(path == p or path.startswith(p + '/') for p in _PUBLIC_PATHS):
        return None
    cfg = core._load_auth_config()
    if cfg.get('enabled') and cfg.get('password'):
        # Accept Bearer token for API/headless access
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
            if core.validate_api_token(token):
                return None   # token valid — allow through
        if not session.get('authenticated'):
            return redirect(url_for('auth.login', next=request.url))

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='VFX Budget System')
    parser.add_argument('--port', type=int, default=5100, help='Port (default: 5100)')
    parser.add_argument('--host', default='0.0.0.0', help='Host (default: 0.0.0.0)')
    args = parser.parse_args()

    core.init_projects_db()
    core.migrate_legacy_db()
    core.migrate_db_schema()
    core._init_slack(app)
    print(f'\n  VFX Budget System  >>  http://localhost:{args.port}\n')
    app.run(debug=False, host=args.host, port=args.port)
