#!/usr/bin/env python3
"""
VFX Budget System — cross-platform launcher
Works on Windows, macOS, and Linux.

Usage:
    python launch.py                  # start on port 5100
    python launch.py --port 5001      # use a custom port
    python launch.py --no-browser     # don't open browser automatically
    python launch.py --install        # install dependencies then exit
"""

import sys
import os
import subprocess
import time
import argparse
import platform

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Argument parsing ───────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='VFX Budget System launcher')
parser.add_argument('--port',       type=int, default=5100,  help='Port (default: 5100)')
parser.add_argument('--host',       default='0.0.0.0',       help='Host (default: 0.0.0.0)')
parser.add_argument('--no-browser', action='store_true',     help='Do not open browser')
parser.add_argument('--install',    action='store_true',     help='Install dependencies and exit')
args = parser.parse_args()

PYTHON = sys.executable
SYSTEM = platform.system()   # 'Windows', 'Darwin', 'Linux'

# ── Helpers ────────────────────────────────────────────────────────────────────
def run(*cmd, **kw):
    return subprocess.run(list(cmd), **kw)

def check_import(module):
    result = run(PYTHON, '-c', f'import {module}',
                 capture_output=True)
    return result.returncode == 0

def install_deps():
    req = os.path.join(HERE, 'requirements.txt')
    if not os.path.exists(req):
        print('  [WARN] requirements.txt not found — skipping install')
        return
    print('  Installing dependencies ...')
    run(PYTHON, '-m', 'pip', 'install', '-r', req, '--quiet', check=True)
    print('  Dependencies ready.')

def open_browser(port):
    url = f'http://localhost:{port}'
    time.sleep(1.5)
    if SYSTEM == 'Darwin':
        run('open', url)
    elif SYSTEM == 'Windows':
        os.startfile(url)   # type: ignore[attr-defined]
    else:
        # Linux — try common openers
        for opener in ('xdg-open', 'gnome-open', 'kde-open'):
            if run('which', opener, capture_output=True).returncode == 0:
                run(opener, url)
                break

# ── Version check ──────────────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    print(f'\n  ERROR: Python 3.9+ required. You have {platform.python_version()}.')
    print('  Download from https://www.python.org\n')
    sys.exit(1)

# ── Dependency install ─────────────────────────────────────────────────────────
print(f'\n  VFX Budget System')
print(f'  Platform : {SYSTEM} {platform.release()}')
print(f'  Python   : {platform.python_version()}  ({PYTHON})')
print(f'  Port     : {args.port}')
print()

if args.install:
    install_deps()
    sys.exit(0)

if not check_import('flask'):
    print('  Flask not found — installing dependencies ...')
    install_deps()
else:
    # Silently ensure all deps present without printing noise
    run(PYTHON, '-m', 'pip', 'install', '-r',
        os.path.join(HERE, 'requirements.txt'),
        '--quiet', '--disable-pip-version-check',
        capture_output=True)

# ── Open browser in background ─────────────────────────────────────────────────
if not args.no_browser:
    import threading
    t = threading.Thread(target=open_browser, args=(args.port,), daemon=True)
    t.start()

# ── Launch app ─────────────────────────────────────────────────────────────────
print(f'  Starting server  >>  http://localhost:{args.port}')
print('  Press Ctrl+C to stop.\n')

app_py = os.path.join(HERE, 'app.py')
os.chdir(HERE)
os.execv(PYTHON, [PYTHON, app_py, '--port', str(args.port), '--host', args.host])
