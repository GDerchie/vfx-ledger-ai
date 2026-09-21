"""
services/db.py — DB connection helpers, constants, and cache stub.
"""
import sqlite3
import os
from flask import session, g, redirect, url_for

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DB  = os.path.join(BASE_DIR, 'projects.db')
PROJECTS_DIR = os.environ.get('VFX_PROJECTS_DIR', os.path.join(BASE_DIR, 'projects'))
os.makedirs(PROJECTS_DIR, exist_ok=True)

_MAX_COST = 10_000_000.0  # $10M hard ceiling per cost field

# ---------------------------------------------------------------------------
# Cache stub — replaced by app.py with the real flask-caching Cache object
# ---------------------------------------------------------------------------
class _NullCache:
    def cached(self, *a, **kw):
        def decorator(f): return f
        return decorator
    def clear(self): pass
    def get(self, key): return None
    def set(self, key, val, timeout=None): pass
    def delete(self, key): pass

cache = _NullCache()

# ---------------------------------------------------------------------------
# DB connection helpers
# ---------------------------------------------------------------------------
class _GConn:
    """Thin wrapper around sqlite3 connection — defers close() to teardown."""
    def __init__(self, conn):
        self._conn = conn
    def close(self): pass  # deferred
    def _real_close(self): self._conn.close()
    def __getattr__(self, name): return getattr(self._conn, name)


def get_projects_db():
    conn = sqlite3.connect(PROJECTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Return the active project DB connection (session-scoped, pooled via Flask g)."""
    db_path = session.get('project_db')
    if not db_path or not os.path.exists(db_path):
        return None
    g_key = 'db_' + db_path
    wrapped = getattr(g, g_key, None)
    if wrapped is None:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        wrapped = _GConn(conn)
        setattr(g, g_key, wrapped)
    return wrapped


def close_db_connections():
    """Called from app.teardown_appcontext."""
    for key in list(vars(g)):
        if key.startswith('db_'):
            wrapped = getattr(g, key, None)
            if wrapped:
                wrapped._real_close()


def get_episodes():
    return list(range(session.get('ep_start', 101), session.get('ep_end', 108) + 1))


def require_project():
    if not session.get('project_db') or not os.path.exists(session['project_db']):
        session.clear()
        return redirect(url_for('projects.project_list'))
    return None
