"""
VFX Budget System — macOS Quick-Start Guide Generator
Run: python generate_mac_guide.py
Output: VFX_Budget_System_macOS_Guide.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_macOS_Guide.pdf')
W, H = A4

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG     = colors.HexColor('#0d0e18')
C_PANEL  = colors.HexColor('#12152a')
C_BORDER = colors.HexColor('#2e3050')
C_GOLD   = colors.HexColor('#f0b429')
C_BLUE   = colors.HexColor('#4a9cf0')
C_GREEN  = colors.HexColor('#52c46a')
C_ORANGE = colors.HexColor('#e08232')
C_MUTED  = colors.HexColor('#7880a0')
C_TEXT   = colors.HexColor('#d0d8f0')
C_ACCENT = colors.HexColor('#1e2240')
C_DARK   = colors.HexColor('#1a1d35')
C_APPLE  = colors.HexColor('#555555')   # neutral grey for Apple references

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def P(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        'cover_title': P('cover_title',
            fontSize=30, leading=36, textColor=C_GOLD,
            fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6),
        'cover_sub': P('cover_sub',
            fontSize=12, leading=17, textColor=C_MUTED,
            fontName='Helvetica', alignment=TA_CENTER, spaceAfter=4),
        'cover_ver': P('cover_ver',
            fontSize=9, leading=13, textColor=C_BLUE,
            fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2),
        'ch_num': P('ch_num',
            fontSize=8, leading=11, textColor=C_GOLD,
            fontName='Helvetica-Bold', spaceAfter=0),
        'ch_title': P('ch_title',
            fontSize=18, leading=22, textColor=C_GOLD,
            fontName='Helvetica-Bold', spaceAfter=4),
        'section': P('section',
            fontSize=12, leading=16, textColor=C_BLUE,
            fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=4),
        'body': P('body',
            fontSize=10, leading=15, textColor=C_TEXT,
            fontName='Helvetica', spaceAfter=5),
        'bullet': P('bullet',
            fontSize=10, leading=14, textColor=C_TEXT,
            fontName='Helvetica', leftIndent=14, spaceAfter=3,
            bulletText='•', bulletIndent=4, bulletColor=C_GOLD),
        'step': P('step',
            fontSize=10, leading=14, textColor=C_TEXT,
            fontName='Helvetica', leftIndent=14, spaceAfter=4),
        'tip': P('tip',
            fontSize=9.5, leading=14, textColor=C_GREEN,
            fontName='Helvetica-Oblique', leftIndent=10, spaceAfter=4),
        'warn': P('warn',
            fontSize=9.5, leading=14, textColor=C_ORANGE,
            fontName='Helvetica-Oblique', leftIndent=10, spaceAfter=4),
        'code': P('code',
            fontSize=9, leading=14, textColor=C_BLUE,
            fontName='Courier', leftIndent=12, spaceAfter=4,
            backColor=C_ACCENT),
        'code_comment': P('code_comment',
            fontSize=9, leading=14, textColor=C_MUTED,
            fontName='Courier', leftIndent=12, spaceAfter=1,
            backColor=C_ACCENT),
        'label': P('label',
            fontSize=8, leading=11, textColor=C_MUTED,
            fontName='Helvetica-Bold', spaceAfter=2),
        'caption': P('caption',
            fontSize=8, leading=11, textColor=C_MUTED,
            fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4),
        'toc_entry': P('toc_entry',
            fontSize=10.5, leading=15, textColor=C_TEXT,
            fontName='Helvetica', leftIndent=6, spaceAfter=3),
        'toc_sub': P('toc_sub',
            fontSize=9, leading=13, textColor=C_MUTED,
            fontName='Helvetica', leftIndent=18, spaceAfter=1),
    }

S = make_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(pts=6):   return Spacer(1, pts)
def hr(c=C_BORDER, t=0.5): return HRFlowable(width='100%', thickness=t, color=c, spaceAfter=5, spaceBefore=3)
def body(txt):   return Paragraph(txt, S['body'])
def sec(txt):    return Paragraph(txt, S['section'])
def bul(txt):    return Paragraph(txt, S['bullet'])
def tip(txt):    return Paragraph(f'TIP  {txt}', S['tip'])
def warn(txt):   return Paragraph(f'NOTE  {txt}', S['warn'])
def code(txt):   return Paragraph(txt, S['code'])
def comment(txt): return Paragraph(f'# {txt}', S['code_comment'])

def step(num, title, detail=''):
    items = []
    label_text = f'<font color="#f0b429"><b>Step {num}</b></font>  <b>{title}</b>'
    items.append(Paragraph(label_text, S['step']))
    if detail:
        items.append(Paragraph(detail, S['body']))
    return items

def ch_header(num, title, subtitle=''):
    items = [
        Paragraph(f'SECTION {num}', S['ch_num']),
        Paragraph(title, S['ch_title']),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, S['cover_sub']))
    items.append(hr(C_GOLD, 1))
    items.append(sp(4))
    return items

def info_table(rows, widths=None):
    data = [[Paragraph(f'<b>{r[0]}</b>', S['label']),
             Paragraph(str(r[1]), S['body'])] for r in rows]
    w = widths or [42*mm, 118*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C_ACCENT),
        ('GRID',       (0,0),(-1,-1), 0.4, C_BORDER),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TEXTCOLOR',  (0,0),(0,-1), C_GOLD),
    ]))
    return [t, sp(8)]

def two_col_table(headers, rows, widths=None):
    n = len(headers)
    head = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    data = [head] + [[Paragraph(str(c), S['body']) for c in r] for r in rows]
    w = widths or [(160/n)*mm]*n
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), C_PANEL),
        ('BACKGROUND', (0,1),(-1,-1), C_ACCENT),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ACCENT, C_BG]),
        ('GRID',       (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR',  (0,0),(-1,0), C_GOLD),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

# ── Page callbacks ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H-12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H-7*mm, 'VFX BUDGET SYSTEM')
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W-15*mm, H-7*mm, 'macOS QUICK-START GUIDE')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 3.5*mm, 'VFX Budget System — Internal Documentation')
    canvas.drawRightString(W-15*mm, 3.5*mm, f'Page {doc.page}')
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.rect(0, H-18*mm, W, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BG)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(W/2, H-11*mm, 'VFX BUDGET SYSTEM  —  macOS QUICK-START GUIDE')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawCentredString(W/2, 5*mm, 'CONFIDENTIAL — INTERNAL USE ONLY')
    canvas.restoreState()

# ── Content ────────────────────────────────────────────────────────────────────

def cover():
    e = []
    e.append(sp(55))
    e.append(Paragraph('VFX BUDGET SYSTEM', S['cover_title']))
    e.append(sp(4))
    e.append(Paragraph('macOS Quick-Start Guide', S['cover_sub']))
    e.append(sp(2))
    e.append(Paragraph('For Apple Silicon & Intel Macs', S['cover_ver']))
    e.append(sp(22))
    e.append(hr(C_GOLD, 1.5))
    e.append(sp(10))
    for k, v in [
        ('COVERS',   'Installing Python · Running the app · Ollama AI setup'),
        ('LAUNCHER', 'START.sh  and  launch.py — both work on macOS'),
        ('TIME',     'You will be up and running in under 10 minutes'),
    ]:
        e.append(Paragraph(
            f'<font color="#f0b429"><b>{k}&nbsp;&nbsp;</b></font>'
            f'<font color="#7880a0">{v}</font>',
            S['cover_sub']))
        e.append(sp(3))
    e.append(sp(30))
    e.append(Paragraph('INTERNAL DOCUMENTATION', S['cover_ver']))
    e.append(PageBreak())
    return e


def toc():
    e = []
    e.append(Paragraph('CONTENTS', S['ch_title']))
    e.append(hr(C_GOLD, 1))
    e.append(sp(6))
    chapters = [
        ('1', 'Requirements',            ['macOS version', 'Python 3.9+', 'Optional: Ollama']),
        ('2', 'Installing Python',       ['Homebrew method (recommended)', 'python.org installer']),
        ('3', 'Getting the App Files',   ['Folder structure', 'Transferring from Windows']),
        ('4', 'Installing Dependencies', ['pip install', 'Virtual environment (optional)']),
        ('5', 'Running the App',         ['START.sh — double-click launcher',
                                          'launch.py — Python launcher',
                                          'Terminal commands']),
        ('6', 'Setting Up Ollama (AI)',  ['Install Ollama', 'Pull a model', 'Connect to the app']),
        ('7', 'Troubleshooting',         ['Port in use', 'Permission denied', 'Python not found',
                                          'Flask import error']),
    ]
    for num, title, subs in chapters:
        e.append(Paragraph(
            f'<font color="#f0b429"><b>{num}.</b></font>  <b>{title}</b>',
            S['toc_entry']))
        for s in subs:
            e.append(Paragraph(f'›  {s}', S['toc_sub']))
        e.append(sp(2))
    e.append(PageBreak())
    return e


def s1_requirements():
    e = []
    e += ch_header('1', 'Requirements', 'What you need before you start')

    e.append(body(
        'The VFX Budget System is a standard Python/Flask web app. '
        'It runs entirely on your local machine — no internet connection required '
        'for the core features. AI features need Ollama (free, local).'
    ))

    e.append(sec('System Requirements'))
    e += info_table([
        ('macOS',        '11 Big Sur or later (Intel and Apple Silicon both supported)'),
        ('Python',       '3.9 or later  —  Section 2 explains how to install it'),
        ('Browser',      'Safari, Chrome, or Firefox — any modern browser works'),
        ('Disk space',   '~100 MB for the app + dependencies; projects are small SQLite files'),
        ('RAM',          '4 GB minimum; 8 GB recommended if using Ollama AI'),
    ])

    e.append(sec('Optional — AI Features'))
    e.append(body(
        'The AI cost estimation, episode narratives, and shot description features '
        'require <b>Ollama</b> running locally. Ollama is free, runs entirely offline, '
        'and works on both Intel and Apple Silicon Macs. See Section 6.'
    ))
    e.append(tip(
        'Apple Silicon Macs (M1/M2/M3/M4) run Ollama models significantly faster '
        'than Intel Macs. A 7B model responds in 2–5 seconds on M-series chips.'
    ))

    e.append(PageBreak())
    return e


def s2_python():
    e = []
    e += ch_header('2', 'Installing Python', 'Two methods — Homebrew is recommended')

    e.append(body(
        'macOS includes a very old Python 2 in some versions. '
        'You need Python 3.9 or later. The easiest way is Homebrew.'
    ))

    e.append(sec('Method A — Homebrew (Recommended)'))
    e.append(body(
        'Homebrew is a free package manager for macOS. '
        'If you already have it, skip to step 2.'
    ))

    e += step('1', 'Install Homebrew',
        'Open Terminal (press Cmd+Space, type Terminal, press Enter). Paste:')
    e.append(code('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'))
    e.append(body('Follow the prompts. It may ask for your Mac password.'))

    e += step('2', 'Install Python 3')
    e.append(code('brew install python'))
    e.append(body('This installs the latest Python 3 and makes it available as <b>python3</b>.'))

    e += step('3', 'Verify the install')
    e.append(code('python3 --version'))
    e.append(body('You should see something like  <b>Python 3.12.x</b>.'))

    e.append(tip(
        'After installing via Homebrew, use <b>python3</b> and <b>pip3</b> in all '
        'terminal commands — not  python  or  pip  (those may still point to the old system Python).'
    ))

    e.append(sec('Method B — python.org Installer'))
    e.append(body(
        'Download the macOS installer from <b>python.org/downloads</b>. '
        'Run the .pkg file and follow the installer wizard. '
        'After installation, open a new Terminal and run:'
    ))
    e.append(code('python3 --version'))
    e.append(warn(
        'After a python.org install, you may need to run the '
        '"Install Certificates" script. Open Finder → Applications → Python 3.x '
        'and double-click  "Install Certificates.command".'
    ))

    e.append(PageBreak())
    return e


def s3_files():
    e = []
    e += ch_header('3', 'Getting the App Files', 'Folder layout and transferring from Windows')

    e.append(body(
        'The VFX Budget System folder is self-contained. '
        'Copy the entire  <b>UPDATE-SISTEM10</b>  folder to your Mac — '
        'anywhere you like (Desktop, Documents, or a shared drive all work).'
    ))

    e.append(sec('Folder Structure'))
    e += two_col_table(
        ['File / Folder', 'Purpose'],
        [
            ['app.py',                   'Main application entry point'],
            ['core.py',                  'Database + business logic'],
            ['llm.py',                   'AI / LLM client'],
            ['llm_config.json',          'AI provider settings (Ollama / Claude / OpenAI)'],
            ['requirements.txt',         'Python package list'],
            ['START.sh',                 'macOS / Linux shell launcher  ← use this on Mac'],
            ['launch.py',                'Cross-platform Python launcher'],
            ['START.bat',                'Windows-only — ignore on Mac'],
            ['routes/',                  'Flask blueprint modules'],
            ['templates/',               'HTML page templates'],
            ['static/',                  'CSS, JavaScript files'],
            ['projects/',                'Your project .vfxdb files live here'],
            ['projects.db',              'Project registry (auto-created)'],
        ],
        widths=[48*mm, 112*mm]
    )

    e.append(sec('Transferring from Windows'))
    e.append(body('Options to copy the folder to your Mac:'))
    e.append(bul('<b>AirDrop</b> — drag the folder onto AirDrop in Finder'))
    e.append(bul('<b>USB drive</b> — copy to a FAT32 or ExFAT drive, plug into Mac'))
    e.append(bul('<b>OneDrive / iCloud Drive</b> — if the folder is in a shared cloud location, it syncs automatically'))
    e.append(bul('<b>Network share</b> — on the same network, use  Go → Connect to Server  in Finder'))
    e.append(tip(
        'If the folder is already on OneDrive and your Mac has the OneDrive app installed, '
        'the files are already there — just find the OneDrive folder in Finder.'
    ))

    e.append(PageBreak())
    return e


def s4_dependencies():
    e = []
    e += ch_header('4', 'Installing Dependencies', 'Install the required Python packages')

    e.append(body(
        'The app needs a few Python packages: Flask, openpyxl, requests, and reportlab. '
        'They are all listed in  <b>requirements.txt</b>. Install them once with a single command.'
    ))

    e.append(sec('Quick Install'))
    e += step('1', 'Open Terminal and navigate to the app folder')
    e.append(body('Replace the path with wherever you saved the folder:'))
    e.append(code('cd ~/Desktop/UPDATE-SISTEM10'))
    e.append(comment('or: cd ~/Documents/UPDATE-SISTEM10'))

    e += step('2', 'Install all dependencies')
    e.append(code('pip3 install -r requirements.txt'))
    e.append(body('You will see download progress for each package. This takes about 30 seconds.'))

    e += step('3', 'Verify Flask installed')
    e.append(code('python3 -c "import flask; print(flask.__version__)"'))
    e.append(body('Should print a version number like  <b>3.1.0</b>.'))

    e.append(sec('Optional — Virtual Environment'))
    e.append(body(
        'A virtual environment keeps the app\'s packages isolated from the rest of your system. '
        'This is optional but recommended if you work on multiple Python projects.'
    ))
    e.append(code('python3 -m venv venv'))
    e.append(code('source venv/bin/activate'))
    e.append(comment('Now install inside the virtual environment'))
    e.append(code('pip install -r requirements.txt'))
    e.append(body(
        'Each time you open a new Terminal to run the app, activate the venv first: '
        '<b>source venv/bin/activate</b>.'
    ))
    e.append(tip(
        'If you use the <b>launch.py</b> launcher (see Section 5), '
        'it automatically checks for Flask and installs dependencies if needed — '
        'so you can skip this section and just run launch.py directly.'
    ))

    e.append(PageBreak())
    return e


def s5_running():
    e = []
    e += ch_header('5', 'Running the App', 'Three ways to start — pick whichever you prefer')

    # ── Method A ──
    e.append(sec('Method A — START.sh  (Shell Script)'))
    e.append(body(
        '<b>START.sh</b> is the macOS equivalent of START.bat on Windows. '
        'It auto-detects Python, checks dependencies, opens your browser, '
        'and starts the server.'
    ))

    e += step('1', 'Make the script executable  (one-time setup only)')
    e.append(body('In Terminal, navigate to the app folder and run:'))
    e.append(code('chmod +x START.sh'))

    e += step('2', 'Run the script')
    e.append(code('./START.sh'))
    e.append(body(
        'The terminal shows  <b>Starting server >> http://localhost:5000</b>. '
        'Your browser opens automatically.'
    ))

    e += step('3', 'Stop the server')
    e.append(body('Press  <b>Ctrl+C</b>  in the Terminal window.'))

    e.append(body('Optional flags:'))
    e += two_col_table(
        ['Command', 'What it does'],
        [
            ['./START.sh --port 5001',       'Use port 5001 instead of 5000'],
            ['./START.sh --no-browser',       'Start server without opening browser'],
        ],
        widths=[70*mm, 90*mm]
    )

    # ── Method B ──
    e.append(sec('Method B — launch.py  (Python Launcher)'))
    e.append(body(
        '<b>launch.py</b> is a cross-platform launcher written in Python. '
        'It works on Windows, macOS, and Linux without any setup.'
    ))
    e.append(code('python3 launch.py'))
    e.append(body('Same optional flags as START.sh:'))
    e += two_col_table(
        ['Command', 'What it does'],
        [
            ['python3 launch.py --port 5001',      'Custom port'],
            ['python3 launch.py --no-browser',     'No auto-open'],
            ['python3 launch.py --install',        'Install deps only, then exit'],
        ],
        widths=[80*mm, 80*mm]
    )

    # ── Method C ──
    e.append(sec('Method C — Direct Terminal Command'))
    e.append(body(
        'If you prefer to run directly without a launcher:'
    ))
    e.append(code('cd ~/Desktop/UPDATE-SISTEM10'))
    e.append(code('python3 app.py'))
    e.append(body(
        'Then open your browser and go to  <b>http://localhost:5000</b>.'
    ))

    e.append(sec('First Launch'))
    e.append(body(
        'On the very first launch, the system creates the  <b>projects.db</b>  registry file. '
        'You will see the Projects home screen. Click  <b>New Project</b>  to create your first project.'
    ))
    e.append(tip(
        'Bookmark  <b>http://localhost:5000</b>  in your browser. '
        'The app must be running (Terminal open) for the bookmark to work.'
    ))

    e.append(PageBreak())
    return e


def s6_ollama():
    e = []
    e += ch_header('6', 'Setting Up Ollama  (AI Features)', 'Free local AI — no internet required after setup')

    e.append(body(
        'Ollama runs large language models locally on your Mac. '
        'The VFX Budget System uses it for shot descriptions, cost estimates, '
        'episode narratives, and notes summarisation. '
        'It is optional — all other features work without it.'
    ))

    e.append(sec('Install Ollama'))
    e += step('1', 'Download Ollama for macOS')
    e.append(body(
        'Go to  <b>ollama.com</b>  and click  Download for macOS. '
        'Open the .dmg and drag Ollama to Applications.'
    ))
    e += step('2', 'Launch Ollama')
    e.append(body(
        'Open Ollama from Applications. A small icon appears in your menu bar. '
        'Ollama runs in the background and listens on  <b>http://localhost:11434</b>.'
    ))

    e.append(sec('Pull a Model'))
    e.append(body(
        'You need to download at least one model. '
        'Open Terminal and run one of these:'
    ))
    e += two_col_table(
        ['Command', 'Model', 'Size', 'Best For'],
        [
            ['ollama pull qwen2.5:7b',   'Qwen 2.5 7B',   '~4.7 GB', 'Default — fast, accurate'],
            ['ollama pull llama3.2:3b',  'Llama 3.2 3B',  '~2.0 GB', 'Fastest, lower RAM'],
            ['ollama pull llama3.1:8b',  'Llama 3.1 8B',  '~4.9 GB', 'High quality'],
            ['ollama pull mistral:7b',   'Mistral 7B',    '~4.1 GB', 'Alternative option'],
        ],
        widths=[48*mm, 30*mm, 20*mm, 62*mm]
    )
    e.append(tip(
        'Apple Silicon Macs (M1/M2/M3/M4) run all models well. '
        'For Intel Macs with 8 GB RAM, use  <b>llama3.2:3b</b>  for the best experience.'
    ))

    e.append(sec('Connect to the VFX Budget System'))
    e += step('1', 'Open the app and go to Settings')
    e.append(body('Click  <b>SETTINGS</b>  in the top navigation bar.'))

    e += step('2', 'Set the LLM provider to Ollama')
    e += info_table([
        ('Provider',   'Ollama'),
        ('Ollama URL', 'http://localhost:11434  (default — no change needed)'),
        ('Model',      'Enter the model you pulled, e.g.  qwen2.5:7b'),
    ])

    e += step('3', 'Test the connection')
    e.append(body(
        'Click  <b>Save Settings</b>, then  <b>Test Connection</b>. '
        'A green check means Ollama is reachable and the model is loaded. '
        'You can now use all ✨ AI buttons in the app.'
    ))

    e.append(warn(
        'Ollama must be running (menu bar icon visible) whenever you want to use AI features. '
        'If you quit Ollama, re-open it from Applications before using the app.'
    ))

    e.append(PageBreak())
    return e


def s7_troubleshooting():
    e = []
    e += ch_header('7', 'Troubleshooting', 'Common issues and how to fix them')

    issues = [
        (
            '"Permission denied" when running START.sh',
            'The script is not yet marked as executable. Run once in Terminal:\n'
            'chmod +x START.sh\n'
            'Then try ./START.sh again.'
        ),
        (
            '"Port 5000 is already in use"',
            'Another process is using port 5000 (or a previous session is still running). '
            'Either stop the other process, or use a different port:\n'
            './START.sh --port 5001\n'
            'Then open http://localhost:5001 in your browser.'
        ),
        (
            '"python3: command not found"',
            'Python 3 is not installed or not in your PATH. '
            'Follow Section 2 to install Python via Homebrew. '
            'After installation, open a new Terminal window and try again.'
        ),
        (
            '"No module named flask" or import errors',
            'Dependencies are not installed. Navigate to the app folder and run:\n'
            'pip3 install -r requirements.txt\n'
            'Or use the launcher which installs automatically:\n'
            'python3 launch.py --install'
        ),
        (
            'Browser opens but shows "This site can\'t be reached"',
            'The server is still starting up. Wait 2–3 seconds and refresh the page. '
            'Check the Terminal window for error messages.'
        ),
        (
            'App starts but AI features show "Connection error"',
            'Ollama is not running. Open Ollama from Applications (menu bar icon should appear). '
            'Also confirm the model name in Settings matches what you pulled — '
            'run  ollama list  in Terminal to see installed models.'
        ),
        (
            'macOS Gatekeeper blocks START.sh or launch.py',
            'Right-click START.sh in Finder → Open → confirm in the dialog. '
            'You only need to do this once. Alternatively, run from Terminal where '
            'Gatekeeper does not apply.'
        ),
        (
            '"SSL: CERTIFICATE_VERIFY_FAILED" on python.org install',
            'Run the Install Certificates script:\n'
            'open /Applications/Python\\ 3.x/Install\\ Certificates.command\n'
            '(Replace 3.x with your Python version number.)'
        ),
    ]

    for title, detail in issues:
        detail_lines = detail.split('\n')
        e.append(KeepTogether([
            Paragraph(f'<font color="#f0b429"><b>▸</b></font>  <b>{title}</b>', S['step']),
            *[code(line) if not line.startswith(('The', 'Another', 'Python', 'Dep', 'Browser', 'Oll', 'Righ', 'Run the', 'Wait', 'Also', 'macOS'))
              and line.strip() else body(line)
              for line in detail_lines if line.strip()],
            sp(4),
        ]))

    e.append(sp(10))
    e.append(hr(C_GOLD, 1))
    e.append(sp(6))
    e.append(Paragraph(
        'VFX Budget System  —  macOS Quick-Start Guide',
        S['cover_sub']
    ))
    e.append(Paragraph(
        'Questions? Ask your system administrator.',
        S['caption']
    ))

    return e


# ── Build ──────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm,  bottomMargin=18*mm,
    )
    story = []
    story += cover()
    story += toc()
    story += s1_requirements()
    story += s2_python()
    story += s3_files()
    story += s4_dependencies()
    story += s5_running()
    story += s6_ollama()
    story += s7_troubleshooting()

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    print(f'\nPDF generated: {OUT}\n')

if __name__ == '__main__':
    build()
