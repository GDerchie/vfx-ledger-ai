#!/usr/bin/env bash
# VFX Budget System — macOS / Linux launcher
# Usage: ./START.sh [--port 5100] [--no-browser]

set -e

# ── Change to script directory ─────────────────────────────────────────────────
cd "$(dirname "$0")"

PORT=5100
OPEN_BROWSER=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)   PORT="$2"; shift 2 ;;
        --no-browser) OPEN_BROWSER=false; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Find Python 3 ──────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c "import sys; print(sys.version_info >= (3,9))" 2>/dev/null)
        if [[ "$version" == "True" ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo ""
    echo "  ERROR: Python 3.9 or later not found."
    echo "  Install from https://www.python.org or via Homebrew: brew install python"
    echo ""
    exit 1
fi

echo ""
echo "  VFX Budget System"
echo "  Python : $($PYTHON --version)"
echo "  Port   : $PORT"
echo ""

# ── Install / check dependencies ───────────────────────────────────────────────
if ! "$PYTHON" -c "import flask" &>/dev/null; then
    echo "  Installing dependencies from requirements.txt ..."
    "$PYTHON" -m pip install -r requirements.txt --quiet
fi

# ── Open browser (macOS: open, Linux: xdg-open) ───────────────────────────────
if [[ "$OPEN_BROWSER" == "true" ]]; then
    (
        sleep 1.5
        if [[ "$(uname)" == "Darwin" ]]; then
            open "http://localhost:$PORT"
        elif command -v xdg-open &>/dev/null; then
            xdg-open "http://localhost:$PORT"
        fi
    ) &
fi

echo "  Starting server  >>  http://localhost:$PORT"
echo "  Press Ctrl+C to stop."
echo ""

# ── Auto-repair broken db_paths (Windows paths won't exist on macOS) ──────────
"$PYTHON" - <<'PYEOF'
import sqlite3, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DB = os.path.join(BASE, 'projects.db')
if not os.path.exists(PROJECTS_DB):
    exit(0)

# Build a map of filename -> absolute local path for all .vfxdb files found
found = {}
for p in glob.glob(os.path.join(BASE, '**', '*.vfxdb'), recursive=True):
    found[os.path.basename(p)] = p

conn = sqlite3.connect(PROJECTS_DB)
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, name, db_filename, db_path FROM projects').fetchall()
fixed = 0
for r in rows:
    if not os.path.exists(r['db_path'] or ''):
        local = found.get(r['db_filename'])
        if local:
            conn.execute('UPDATE projects SET db_path=? WHERE id=?', (local, r['id']))
            print(f"  [path-repair] {r['name']}  →  {local}")
            fixed += 1
if fixed:
    conn.commit()
    print(f"  [path-repair] Fixed {fixed} project path(s).")
conn.close()
PYEOF

"$PYTHON" app.py --port "$PORT"
