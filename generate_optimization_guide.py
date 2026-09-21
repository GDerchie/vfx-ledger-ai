"""
VFX Budget System v04 — Optimization & Future Development Guide
Run: python generate_optimization_guide.py
Output: VFX_Budget_System_Optimization_Guide.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

W, H = A4
OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_Optimization_Guide.pdf')

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG     = colors.HexColor('#0d0e18')
C_PANEL  = colors.HexColor('#12152a')
C_BORDER = colors.HexColor('#2e3050')
C_GOLD   = colors.HexColor('#f0b429')
C_BLUE   = colors.HexColor('#4a9cf0')
C_GREEN  = colors.HexColor('#52c46a')
C_RED    = colors.HexColor('#e05252')
C_ORANGE = colors.HexColor('#e08232')
C_MUTED  = colors.HexColor('#7880a0')
C_TEXT   = colors.HexColor('#d0d8f0')
C_ACCENT = colors.HexColor('#1e2240')
C_DARK   = colors.HexColor('#080a14')
C_PURPLE = colors.HexColor('#9b59b6')
C_TEAL   = colors.HexColor('#1abc9c')

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def P(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)
    return {
        'cover_title':  P('ct',  fontSize=30, leading=36, textColor=C_TEAL,
                           fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6),
        'cover_sub':    P('cs',  fontSize=13, leading=18, textColor=C_MUTED,
                           fontName='Helvetica', alignment=TA_CENTER, spaceAfter=4),
        'cover_tag':    P('ctg', fontSize=10, leading=14, textColor=C_BLUE,
                           fontName='Helvetica-Bold', alignment=TA_CENTER),
        'toc_entry':    P('te',  fontSize=11, leading=16, textColor=C_TEXT,
                           fontName='Helvetica', leftIndent=8, spaceAfter=2),
        'toc_sub':      P('ts',  fontSize=9.5, leading=14, textColor=C_MUTED,
                           fontName='Helvetica', leftIndent=22, spaceAfter=1),
        'ch_num':       P('cn',  fontSize=9, leading=12, textColor=C_TEAL,
                           fontName='Helvetica-Bold', spaceAfter=0),
        'ch_title':     P('ctt', fontSize=20, leading=24, textColor=C_TEAL,
                           fontName='Helvetica-Bold', spaceAfter=4),
        'ch_sub':       P('csb', fontSize=11, leading=16, textColor=C_MUTED,
                           fontName='Helvetica', spaceAfter=8),
        'section':      P('sec', fontSize=13, leading=17, textColor=C_BLUE,
                           fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=4),
        'body':         P('bod', fontSize=10, leading=15, textColor=C_TEXT,
                           fontName='Helvetica', spaceAfter=6),
        'bullet':       P('bul', fontSize=10, leading=14, textColor=C_TEXT,
                           fontName='Helvetica', leftIndent=14, spaceAfter=3,
                           bulletText='*', bulletIndent=4),
        'sub_b':        P('sb',  fontSize=9.5, leading=13, textColor=C_MUTED,
                           fontName='Helvetica', leftIndent=28, spaceAfter=2,
                           bulletText='-', bulletIndent=18),
        'tip':          P('tip', fontSize=9.5, leading=14, textColor=C_GREEN,
                           fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4),
        'warn':         P('wrn', fontSize=9.5, leading=14, textColor=C_ORANGE,
                           fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4),
        'code':         P('cod', fontSize=8.5, leading=13, textColor=C_TEAL,
                           fontName='Courier', leftIndent=14, spaceAfter=4,
                           backColor=C_ACCENT),
        'label':        P('lbl', fontSize=8, leading=11, textColor=C_MUTED,
                           fontName='Helvetica-Bold', spaceAfter=2),
        'caption':      P('cap', fontSize=8.5, leading=12, textColor=C_MUTED,
                           fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4),
        'arch':         P('arc', fontSize=8.5, leading=13, textColor=C_GREEN,
                           fontName='Courier', leftIndent=8, spaceAfter=1),
        'tier_title':   P('tt',  fontSize=11, leading=15, textColor=C_GOLD,
                           fontName='Helvetica-Bold', spaceAfter=2),
        'impact_high':  P('ih',  fontSize=9, leading=12, textColor=C_GREEN,
                           fontName='Helvetica-Bold', spaceAfter=0),
        'impact_med':   P('im',  fontSize=9, leading=12, textColor=C_GOLD,
                           fontName='Helvetica-Bold', spaceAfter=0),
        'impact_low':   P('il',  fontSize=9, leading=12, textColor=C_MUTED,
                           fontName='Helvetica-Bold', spaceAfter=0),
    }

S = make_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(n=6):    return Spacer(1, n)
def hr(c=C_BORDER, t=0.5): return HRFlowable(width='100%', thickness=t, color=c, spaceAfter=5, spaceBefore=3)
def body(t):    return Paragraph(t, S['body'])
def section(t): return Paragraph(t, S['section'])
def bullet(t):  return Paragraph(t, S['bullet'])
def sub_b(t):   return Paragraph(t, S['sub_b'])
def tip(t):     return Paragraph(f'TIP  {t}', S['tip'])
def warn(t):    return Paragraph(f'NOTE  {t}', S['warn'])
def code(t):    return Paragraph(t, S['code'])
def arch(t):    return Paragraph(t, S['arch'])

def chapter_header(num, title, subtitle=''):
    items = [
        Paragraph(f'CHAPTER {num}', S['ch_num']),
        Paragraph(title, S['ch_title']),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, S['ch_sub']))
    items.append(hr(C_TEAL, 1))
    items.append(sp(4))
    return items

def info_table(rows, col_widths=None):
    data = [[Paragraph(f'<b>{r[0]}</b>', S['label']),
             Paragraph(str(r[1]), S['body'])] for r in rows]
    w = col_widths or [48*mm, 112*mm]
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

def col_table(headers, rows, col_widths=None):
    n = len(headers)
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = [[Paragraph(str(c), S['body']) for c in r] for r in rows]
    data = [head_row] + body_rows
    w = col_widths or [(160/n)*mm]*n
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_PANEL),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [C_ACCENT, C_BG]),
        ('GRID',          (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR',     (0,0),(-1,0), C_GOLD),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

def arch_box(lines, border_color=None):
    bc = border_color or C_TEAL
    data = [[Paragraph(line, S['arch'])] for line in lines]
    t = Table(data, colWidths=[160*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_DARK),
        ('BOX',           (0,0),(-1,-1), 0.8, bc),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

def opt_card(num, title, tier_color, impact, effort, risk, summary, details, code_snippet=None):
    """Render a single optimization card"""
    impact_colors = {'HIGH': '#52c46a', 'MEDIUM': '#f0b429', 'LOW': '#7880a0'}
    effort_colors = {'Low': '#52c46a', 'Medium': '#f0b429', 'High': '#e05252', '1 day': '#52c46a', '2 days': '#f0b429', '3 days': '#e08232', '1 hour': '#52c46a', '30 min': '#52c46a'}
    risk_colors   = {'None': '#52c46a', 'Low': '#52c46a', 'Medium': '#f0b429', 'High': '#e05252'}

    ic = impact_colors.get(impact, '#d0d8f0')
    ec = effort_colors.get(effort, '#d0d8f0')
    rc = risk_colors.get(risk, '#d0d8f0')

    header = Table([[
        Paragraph(f'<font color="{tier_color.hexval()}"><b>#{num}</b></font>', S['body']),
        Paragraph(f'<b>{title}</b>', S['body']),
        Paragraph(f'<font color="{ic}">IMPACT: {impact}</font>', S['label']),
        Paragraph(f'<font color="{ec}">EFFORT: {effort}</font>', S['label']),
        Paragraph(f'<font color="{rc}">RISK: {risk}</font>', S['label']),
    ]], colWidths=[12*mm, 68*mm, 30*mm, 26*mm, 24*mm])
    header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_PANEL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 4),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('BOX',           (0,0),(-1,-1), 0.6, tier_color),
    ]))

    body_rows = [[Paragraph(summary, S['body'])]]
    for d in details:
        body_rows.append([Paragraph(f'   {d}', S['sub_b'])])
    if code_snippet:
        body_rows.append([Paragraph(code_snippet, S['code'])])

    body_t = Table(body_rows, colWidths=[160*mm])
    body_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_ACCENT),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
        ('BOX',           (0,0),(-1,-1), 0.6, tier_color),
        ('LINEABOVE',     (0,0),(-1,0), 0, C_BORDER),
    ]))

    return [KeepTogether([header, body_t]), sp(8)]

# ── Page callbacks ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H - 12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_TEAL)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H - 7*mm, 'VFX BUDGET SYSTEM v04  --  OPTIMIZATION & FUTURE DEVELOPMENT GUIDE')
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawRightString(W - 15*mm, H - 7*mm, 'INTERNAL USE ONLY')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 3.5*mm, 'VFX Budget System -- Development Roadmap')
    canvas.drawRightString(W - 15*mm, 3.5*mm, f'Page {doc.page}')
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C_TEAL)
    canvas.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BG)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(W/2, H - 11*mm, 'VFX BUDGET SYSTEM  --  OPTIMIZATION & FUTURE DEVELOPMENT GUIDE')
    canvas.setFillColor(colors.HexColor('#051a14'))
    canvas.rect(0, 0, 4*mm, H, fill=1, stroke=0)
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_TEAL)
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawCentredString(W/2, 5*mm, 'INTERNAL USE ONLY  --  Development Reference Document')
    canvas.restoreState()

# ── Content ────────────────────────────────────────────────────────────────────

def cover():
    e = []
    e.append(sp(55))
    e.append(Paragraph('OPTIMIZATION &amp; FUTURE', S['cover_title']))
    e.append(Paragraph('DEVELOPMENT GUIDE', S['cover_title']))
    e.append(sp(4))
    e.append(Paragraph('VFX Budget System v04', S['cover_sub']))
    e.append(sp(2))
    e.append(Paragraph('Technical Roadmap & Implementation Reference', S['cover_tag']))
    e.append(sp(20))
    e.append(hr(C_TEAL, 1.5))
    e.append(sp(10))
    for k, v in [
        ('OPTIMIZATIONS',  '17 items across 5 tiers'),
        ('SCOPE',          'Performance, Code Quality, UX, Data Integrity, New Features'),
        ('PRIORITY ORDER', 'Ranked by impact vs effort'),
        ('STATUS',         'Planned -- Not Yet Implemented'),
    ]:
        e.append(Paragraph(
            f'<font color="#1abc9c"><b>{k}&nbsp;&nbsp;</b></font>'
            f'<font color="#7880a0">{v}</font>',
            S['cover_sub']))
        e.append(sp(2))
    e.append(sp(30))
    e.append(Paragraph('v04 -- March 2026', S['cover_tag']))
    e.append(PageBreak())
    return e

def toc():
    e = []
    e.append(Paragraph('TABLE OF CONTENTS', S['ch_title']))
    e.append(hr(C_TEAL, 1))
    e.append(sp(6))
    chapters = [
        ('1', 'Optimization Overview',      ['Impact matrix', 'Priority order', 'Effort vs impact chart']),
        ('2', 'Tier 1 — Performance',       ['API caching', 'Lazy-load nav', 'Tabulator virtual DOM', 'DB connection pool']),
        ('3', 'Tier 2 — Code Quality',      ['Split app.py', 'Shared JS utilities', 'Blueprint architecture']),
        ('4', 'Tier 3 — UX & Workflow',     ['Unsaved changes warning', 'Keyboard shortcuts', 'Bulk row operations', 'Auto-save indicator']),
        ('5', 'Tier 4 — Data Integrity',    ['Input validation', 'Duplicate shot detection', 'Orphaned asset detection']),
        ('6', 'Tier 5 — New Features',      ['Change history', 'Season dashboard', 'Email/Slack alerts', 'Per-EP PDF one-pager']),
        ('7', 'Implementation Roadmap',     ['Week-by-week plan', 'Dependencies', 'What stays unchanged']),
        ('8', 'Future Version — v05',       ['Proposed feature set', 'Architecture upgrades', 'AI enhancements']),
    ]
    for num, title, subs in chapters:
        e.append(Paragraph(
            f'<font color="#1abc9c"><b>{num}.</b></font>  <b>{title}</b>',
            S['toc_entry']))
        for s in subs:
            e.append(Paragraph(f'> {s}', S['toc_sub']))
        e.append(sp(3))
    e.append(PageBreak())
    return e

def ch1():
    e = []
    e += chapter_header('1', 'Optimization Overview', 'Impact matrix, priority order, and scope')

    e.append(section('The 17 Optimizations at a Glance'))
    e += col_table(
        ['#', 'Optimization', 'Tier', 'Impact', 'Effort', 'Risk'],
        [
            ['1',  'API response caching',           'Performance',      'HIGH',   'Medium', 'Low'],
            ['2',  'Lazy-load episode nav',           'Performance',      'MEDIUM', 'Low',    'None'],
            ['3',  'Tabulator virtual DOM',           'Performance',      'HIGH',   'Low',    'None'],
            ['4',  'DB connection pool',              'Performance',      'MEDIUM', 'Medium', 'Low'],
            ['5',  'Split app.py into blueprints',   'Code Quality',     'MEDIUM', 'High',   'Medium'],
            ['6',  'Shared JS utils file',           'Code Quality',     'LOW',    'Low',    'None'],
            ['7',  'Blueprint architecture',         'Code Quality',     'MEDIUM', 'High',   'Medium'],
            ['8',  'Unsaved changes warning',        'UX',               'HIGH',   'Low',    'None'],
            ['9',  'Keyboard shortcuts',             'UX',               'MEDIUM', 'Low',    'None'],
            ['10', 'Bulk row operations',            'UX',               'HIGH',   'Medium', 'Low'],
            ['11', 'Auto-save indicator',            'UX',               'HIGH',   'Low',    'None'],
            ['12', 'Input validation layer',         'Data Integrity',   'HIGH',   'Medium', 'Low'],
            ['13', 'Duplicate shot detection',       'Data Integrity',   'MEDIUM', 'Low',    'None'],
            ['14', 'Orphaned asset detection',       'Data Integrity',   'LOW',    'Low',    'None'],
            ['15', 'Change history per shot',        'New Feature',      'HIGH',   'Medium', 'Low'],
            ['16', 'Season progress dashboard',      'New Feature',      'HIGH',   'High',   'Low'],
            ['17', 'Email / Slack alerts',           'New Feature',      'MEDIUM', 'Medium', 'Low'],
        ],
        col_widths=[9*mm, 62*mm, 28*mm, 20*mm, 22*mm, 19*mm]
    )

    e.append(section('Quick-Win Matrix'))
    e.append(body('Items that deliver the most visible improvement for the least effort:'))
    e += arch_box([
        'START HERE (High Impact, Low Effort):',
        '  #3  Tabulator virtual DOM   -- 30 min, zero backend change, 5x table speed',
        '  #8  Unsaved changes warning -- 1 hour, prevents data loss',
        '  #11 Auto-save indicator     -- 1 hour, users see save status',
        '  #13 Duplicate shot detect   -- 2 hours, catches common data entry errors',
        '',
        'DO NEXT (High Impact, Medium Effort):',
        '  #1  API caching             -- 1 day, distribution page 3x faster',
        '  #10 Bulk row operations     -- 2 days, saves time on large episodes',
        '  #12 Input validation        -- 2 days, prevents bad data entering DB',
        '  #15 Change history          -- 2 days, audit trail for financial edits',
        '',
        'PLAN LATER (High Value, High Effort):',
        '  #5  Split app.py            -- 3 days, major maintainability improvement',
        '  #16 Season dashboard        -- 1 week, new feature for producers',
    ])

    e.append(section('Current System State (v04 Baseline)'))
    e += info_table([
        ('app.py',        '~1600 lines, 106 routes, single file'),
        ('Templates',     '11 HTML files, some shared logic duplicated'),
        ('Database',      'SQLite, one connection per request, no caching'),
        ('JS',            'Tabulator 6.2.1, Bootstrap 5.3, per-page scripts'),
        ('AI',            'Ollama SSE streaming, 4 task types'),
        ('No. of pages',  '10 (Distribution, EP x8, Assets, Notes, Bid Compare, Vendor Tracker, Invoice Log, Scenario, Settings)'),
    ])

    e.append(PageBreak())
    return e

def ch2():
    e = []
    e += chapter_header('2', 'Tier 1 — Performance', 'Making the system faster for all users')

    e += opt_card(
        num='1', title='API Response Caching',
        tier_color=C_TEAL, impact='HIGH', effort='Medium', risk='Low',
        summary='The Distribution page calls /api/distribution on every load, which queries all '
                'episodes simultaneously. With 8 episodes and combined shot+asset totals, this is '
                'the heaviest query in the system. Cache the response for 30 seconds.',
        details=[
            'Use Flask-Caching with SimpleCache (in-memory, no Redis needed)',
            'Invalidate cache when any shot or asset is saved (PUT/POST triggers cache.clear)',
            'Apply same pattern to /api/vendor_confidence (changes rarely)',
            'Expected improvement: Distribution page load 3x to 5x faster',
        ],
        code_snippet='pip install flask-caching\n'
                     'from flask_caching import Cache\n'
                     'cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})\n'
                     '@app.route("/api/distribution")\n'
                     '@cache.cached(timeout=30)\n'
                     'def distribution(): ...'
    )

    e += opt_card(
        num='2', title='Lazy-Load Episode Navigation Dropdown',
        tier_color=C_TEAL, impact='MEDIUM', effort='Low', risk='None',
        summary='The Episodes dropdown in the navbar is generated server-side on every page load '
                'using a Jinja loop. With 20+ episodes this adds render overhead. Load it once '
                'and cache in sessionStorage.',
        details=[
            'Fetch /api/episodes list once via JavaScript on first nav interaction',
            'Store in sessionStorage -- persists across page navigation in same tab',
            'Dropdown renders from JS, not Jinja -- removes server-side templating cost',
            'Benefit scales with episode count: 8 EPs minimal, 20+ EPs noticeable',
        ],
        code_snippet="// In base.html\nconst eps = JSON.parse(sessionStorage.getItem('eps')\n"
                     "  || await fetch('/api/episodes').then(r=>r.json()));\nsessionStorage.setItem('eps', JSON.stringify(eps));"
    )

    e += opt_card(
        num='3', title='Tabulator Virtual DOM Rendering',
        tier_color=C_TEAL, impact='HIGH', effort='Low', risk='None',
        summary='Tabulator renders all rows into the DOM by default. On episode pages with 200+ shots, '
                'this creates thousands of DOM nodes and slows scrolling. Virtual rendering only '
                'renders visible rows -- the rest are rendered on scroll.',
        details=[
            'Add two options to every Tabulator initialisation call',
            'renderVertical: "virtual" -- only renders rows visible in the viewport',
            'renderVerticalBuffer: 600 -- pre-renders 600px above/below for smooth scrolling',
            '500-row table renders as fast as a 50-row table',
            'Zero backend change -- pure frontend config addition',
        ],
        code_snippet='// Add to ALL Tabulator({...}) initialisations:\nrenderVertical: "virtual",\nrenderVerticalBuffer: 600,'
    )

    e += opt_card(
        num='4', title='Database Connection Pool',
        tier_color=C_TEAL, impact='MEDIUM', effort='Medium', risk='Low',
        summary='Currently every API request opens a new SQLite connection and closes it at the end. '
                'For high-frequency saves (typing in a cell triggers PUT) this creates overhead. '
                'Use a connection pool or persistent g-object connection.',
        details=[
            'Use Flask g object to hold connection per request (already partially done)',
            'Add teardown_appcontext to close connection cleanly after each request',
            'For PostgreSQL migration (future): use psycopg2.pool.ThreadedConnectionPool',
            'Estimated improvement: 15-25ms saved per API call on busy pages',
        ],
        code_snippet='from flask import g\ndef get_db():\n    if "db" not in g:\n        g.db = sqlite3.connect(DB_PATH)\n        g.db.row_factory = sqlite3.Row\n    return g.db\n\n@app.teardown_appcontext\ndef close_db(e=None):\n    db = g.pop("db", None)\n    if db: db.close()'
    )

    e.append(PageBreak())
    return e

def ch3():
    e = []
    e += chapter_header('3', 'Tier 2 — Code Quality', 'Maintainability and structure improvements')

    e += opt_card(
        num='5', title='Split app.py into Flask Blueprints',
        tier_color=C_BLUE, impact='MEDIUM', effort='High', risk='Medium',
        summary='app.py is currently ~1600 lines with 106 route functions. This makes it hard to '
                'navigate, debug, and onboard new developers. Split into Flask Blueprints by domain.',
        details=[
            'routes/shots.py     -- /api/shots/* (EP page shot CRUD)',
            'routes/assets.py    -- /api/assets/* (Assets page)',
            'routes/bidcompare.py -- /api/bidcompare/* (Bid Compare)',
            'routes/invoicelog.py -- /api/invoicelog/* + /api/vendor_registry/*',
            'routes/llm.py       -- /api/llm/stream + /api/llm/complete',
            'routes/export.py    -- /api/export/* (Excel/CSV downloads)',
            'routes/pages.py     -- all HTML page routes (/ep/<n>, /assets, /notes, etc.)',
            'app.py becomes ~100 lines: factory, config, blueprint registration',
        ],
        code_snippet='# app.py after split:\nfrom routes.shots import shots_bp\nfrom routes.assets import assets_bp\napp.register_blueprint(shots_bp)\napp.register_blueprint(assets_bp)\n# ... etc'
    )

    e += opt_card(
        num='6', title='Shared JavaScript Utilities File',
        tier_color=C_BLUE, impact='LOW', effort='Low', risk='None',
        summary='Several functions are duplicated across templates: fmt(), saveCell(), '
                'badge renderers, date formatters. Move shared code to /static/utils.js.',
        details=[
            'fmt(v) -- currency formatter used in ep.html, bidcompare.html, vendortracker.html',
            'badge(text, cls) -- status badge renderer used in distribution.html, ep.html',
            'dateStr() -- consistent date formatting',
            'apiPut(url, data) -- standard PUT wrapper with error handling',
            'Reduces total template JS by ~200 lines, easier to fix bugs in one place',
        ],
        code_snippet='// /static/utils.js\nwindow.fmt = v => {\n  const n = parseFloat(v);\n  return isNaN(n)||n===0 ? "" : "$"+n.toLocaleString("en-US",{maximumFractionDigits:0});\n};\nwindow.apiPut = (url,data) => fetch(url,{method:"PUT",\n  headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});'
    )

    e += opt_card(
        num='7', title='Blueprint Architecture Overview',
        tier_color=C_BLUE, impact='MEDIUM', effort='High', risk='Medium',
        summary='The full proposed folder structure after the Blueprint refactor. '
                'This is the target architecture for v05.',
        details=[
            'app.py                  -- application factory, 80-100 lines',
            'config.py               -- all configuration constants',
            'db.py                   -- connection helpers, migrate_db_schema()',
            'routes/shots.py         -- shot CRUD + import/export',
            'routes/assets.py        -- asset CRUD + import/export',
            'routes/bidcompare.py    -- bid CRUD + Excel import + confidence',
            'routes/invoicelog.py    -- invoice + vendor registry + capacity',
            'routes/vendortracker.py -- vendor tracker CRUD',
            'routes/llm.py           -- SSE streaming + prompt builders',
            'routes/export.py        -- Excel/CSV/PDF generation',
            'routes/pages.py         -- HTML page rendering',
            'routes/api.py           -- search, distribution, settings',
        ]
    )

    e.append(PageBreak())
    return e

def ch4():
    e = []
    e += chapter_header('4', 'Tier 3 — UX & Workflow', 'Improvements that users will notice immediately')

    e += opt_card(
        num='8', title='Unsaved Changes Warning',
        tier_color=C_GOLD, impact='HIGH', effort='Low', risk='None',
        summary='If a user closes the browser tab or navigates away while a cell edit is in flight '
                '(network request pending), the change is silently lost. Add a beforeunload warning.',
        details=[
            'Track a global boolean: let pendingSave = false',
            'Set pendingSave = true when any cell edit begins (cellEditing Tabulator event)',
            'Set pendingSave = false when the PUT /api/* response returns',
            'window.addEventListener("beforeunload", e => { if (pendingSave) e.preventDefault(); })',
            'Browser shows "Leave site? Changes may not be saved" dialog',
        ],
        code_snippet='let pendingSave = false;\ntable.on("cellEditing", () => pendingSave = true);\n// In each cellEdited:\nawait apiPut(url, data);\npendingSave = false;\n\nwindow.addEventListener("beforeunload", e => {\n  if (pendingSave) e.preventDefault();\n});'
    )

    e += opt_card(
        num='9', title='Keyboard Shortcuts',
        tier_color=C_GOLD, impact='MEDIUM', effort='Low', risk='None',
        summary='Power users working on large episodes need fast keyboard navigation. '
                'Add context-aware shortcuts that work alongside the existing Ctrl+K search.',
        details=[
            'Ctrl+K      -- Global search (already implemented)',
            'Ctrl+N      -- Add new row (context-aware: shot on EP page, asset on Assets page)',
            'Ctrl+S      -- Force sync / refresh current table from DB',
            'Escape      -- Cancel current cell edit without saving',
            'Ctrl+E      -- Export current view to CSV',
            'Arrow keys  -- Navigate between cells in Tabulator (Tabulator built-in, just enable)',
        ],
        code_snippet="document.addEventListener('keydown', e => {\n  if (e.ctrlKey && e.key==='n') { e.preventDefault(); addRow(); }\n  if (e.ctrlKey && e.key==='s') { e.preventDefault(); loadData(); }\n  if (e.ctrlKey && e.key==='e') { e.preventDefault(); exportCSV(); }\n});"
    )

    e += opt_card(
        num='10', title='Bulk Row Operations',
        tier_color=C_GOLD, impact='HIGH', effort='Medium', risk='Low',
        summary='Currently every shot must be edited one cell at a time. On large episodes (50+ shots), '
                'changing status, vendor, or complexity for a group is tedious. '
                'Add checkbox selection + bulk action toolbar.',
        details=[
            'Add selectable: "highlight" to Tabulator config -- enables row checkboxes',
            'Floating toolbar appears when 2+ rows selected: "Set Status", "Set Vendor", "Set Complexity"',
            'Bulk PUT request sends array of IDs + new value to /api/shots/bulk',
            'Confirm dialog: "Update 12 shots to status: Delivered?"',
            'Also enables bulk delete (with strong confirmation)',
        ],
        code_snippet='// Tabulator config:\nselectable: true,\nselectableRangeMode: "click",\n// Toolbar:\ntable.on("rowSelectionChanged", rows => {\n  bulkBar.style.display = rows.length>1 ? "flex" : "none";\n  bulkCount.textContent = rows.length + " selected";\n});'
    )

    e += opt_card(
        num='11', title='Auto-Save Status Indicator',
        tier_color=C_GOLD, impact='HIGH', effort='Low', risk='None',
        summary='After editing a cell, users have no visual confirmation that the change saved. '
                'A subtle status badge near each table gives immediate feedback.',
        details=[
            'Small badge in top-right of each table panel: "Saved", "Saving...", "Error"',
            'Green "Saved" fades in on successful PUT, disappears after 2 seconds',
            'Yellow "Saving..." appears immediately when edit is submitted',
            'Red "Error" stays visible if the PUT fails, with retry option',
            'Zero backend change -- pure frontend UI addition',
        ],
        code_snippet="function showSaveStatus(el, state) {\n  const colors = {saving:'#f0b429', saved:'#52c46a', error:'#e05252'};\n  el.textContent = state.charAt(0).toUpperCase()+state.slice(1);\n  el.style.color = colors[state];\n  if (state==='saved') setTimeout(()=>el.textContent='', 2000);\n}"
    )

    e.append(PageBreak())
    return e

def ch5():
    e = []
    e += chapter_header('5', 'Tier 4 — Data Integrity', 'Preventing bad data from entering the system')

    e += opt_card(
        num='12', title='Input Validation Layer',
        tier_color=C_ORANGE, impact='HIGH', effort='Medium', risk='Low',
        summary='Cost fields (cost_est, efc) accept any string currently. A user who accidentally '
                'types "1.5M" instead of "1500000" silently stores a non-numeric value. '
                'Validate at both the frontend and the API layer.',
        details=[
            'Frontend: Tabulator validator on cost columns -- reject non-numeric on blur',
            'Backend: Sanitise all cost fields in PUT handlers before writing to DB',
            'Warn (not block) if EFC > EST x 2.0 -- likely a data entry error',
            'Warn if EFC is negative -- impossible in normal production scenarios',
            'Reject future dates in invoice_date and approve_date fields',
            'Reject duplicate invoice numbers from the same vendor',
        ],
        code_snippet='// Tabulator column validator:\n{ field:"cost_est", validator:["numeric", "min:0"] }\n\n# Backend (app.py):\ndef clean_cost(v):\n    try: return max(0, float(str(v).replace(",","").replace("$","")))\n    except: return 0.0'
    )

    e += opt_card(
        num='13', title='Duplicate Shot Detection',
        tier_color=C_ORANGE, impact='MEDIUM', effort='Low', risk='None',
        summary='If the same scene code is entered twice on an episode page, the table shows '
                'duplicate rows with no warning. This causes double-counting in distribution totals. '
                'Detect and highlight duplicates immediately.',
        details=[
            'On cell edit of the SC (scene code) field, check existing rows for same value',
            'Highlight duplicate rows in amber with a warning icon',
            'Show toast: "Scene 42A already exists in this episode"',
            'Also run on data load -- flag pre-existing duplicates in the database',
            'Backend: add UNIQUE constraint option to scene_code per episode (optional, strict mode)',
        ],
        code_snippet="table.on('cellEdited', cell => {\n  if (cell.getField() !== 'scene_code') return;\n  const val = cell.getValue();\n  const dups = table.getData().filter(r => r.scene_code===val);\n  if (dups.length > 1) showToast('Duplicate scene code: '+val, 'warning');\n});"
    )

    e += opt_card(
        num='14', title='Orphaned Asset Detection',
        tier_color=C_ORANGE, impact='LOW', effort='Low', risk='None',
        summary='Assets on the Assets page can be created and never linked to any shot. '
                'Over time these accumulate as ghost entries that inflate asset cost totals. '
                'Surface them visually so they can be reviewed.',
        details=[
            'On Assets page load, call /api/assets/orphaned -- returns assets with no shot links',
            'Show count in a warning banner: "3 assets are not linked to any shot"',
            'Highlight orphaned rows with a subtle amber left border',
            'Tooltip: "No shots link to this asset -- check ASSET column in episode pages"',
            'Add /api/assets/orphaned endpoint: LEFT JOIN shots on asset name, WHERE shot IS NULL',
        ],
        code_snippet="@app.route('/api/assets/orphaned')\ndef orphaned_assets():\n    rows = conn.execute('''\n        SELECT a.* FROM assets a\n        LEFT JOIN shots s ON UPPER(s.asset)=UPPER(a.asset_name)\n        WHERE s.id IS NULL AND a.omit=0\n    ''').fetchall()\n    return jsonify([dict(r) for r in rows])"
    )

    e.append(PageBreak())
    return e

def ch6():
    e = []
    e += chapter_header('6', 'Tier 5 — New Features', 'High-value additions for future versions')

    e += opt_card(
        num='15', title='Change History Per Shot / Asset',
        tier_color=C_PURPLE, impact='HIGH', effort='Medium', risk='Low',
        summary='Financial fields (cost_est, efc, award_vendor) change frequently during production. '
                'There is currently no record of what a value was before it changed. '
                'Add a change_log table that records every edit.',
        details=[
            'New table: change_log(id, table_name, row_id, field, old_value, new_value, user, timestamp)',
            'Populate from PUT handlers: log before-and-after for cost/efc/vendor/status fields',
            'UI: small clock icon on each row opens a "History" side panel',
            'History panel shows last 10 changes with timestamps and one-click rollback',
            'Doubles as an audit log (satisfies financial accountability requirements)',
        ],
        code_snippet="def log_change(table, row_id, field, old_val, new_val, user='system'):\n    conn.execute(\n        'INSERT INTO change_log VALUES (NULL,?,?,?,?,?,?,datetime(\"now\"))',\n        (table, row_id, field, str(old_val), str(new_val), user)\n    )\n    conn.commit()"
    )

    e += opt_card(
        num='16', title='Season Progress Dashboard',
        tier_color=C_PURPLE, impact='HIGH', effort='High', risk='Low',
        summary='Producers need a single-screen view of season health. Currently they must visit '
                'each episode page and the distribution page separately. '
                'A new dashboard page aggregates everything into visual charts.',
        details=[
            'New page: /dashboard -- accessible from navbar',
            'Section 1: Season burn chart -- EST vs EFC over time (using change_log data)',
            'Section 2: Shot delivery status donut per episode (Delivered / In Progress / Not Started)',
            'Section 3: Vendor workload bar chart -- shots per vendor across all EPs',
            'Section 4: Risk heatmap -- episode grid coloured by risk badge',
            'Section 5: Top 5 at-risk shots -- highest EFC overrun items',
            'Uses Chart.js (CDN) -- lightweight, no backend chart library needed',
        ],
        code_snippet='// Chart.js (add to base.html CDN):\n// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n\n// Example: donut per EP\nnew Chart(ctx, {\n  type: "doughnut",\n  data: { labels:["Delivered","In Progress","Not Started"],\n          datasets:[{data:[d,ip,ns]}] }\n});'
    )

    e += opt_card(
        num='17', title='Email / Slack Alerts',
        tier_color=C_PURPLE, impact='MEDIUM', effort='Medium', risk='Low',
        summary='Key events in production should trigger notifications without requiring someone '
                'to check the app. Auto-alerts for risk changes, invoice approvals, and budget overruns.',
        details=[
            'Trigger: risk badge changes from WATCH --> AT RISK or higher',
            'Trigger: invoice status set to Approved -- notify producer for payment',
            'Trigger: EFC exceeds EST by more than 20% on any episode',
            'Trigger: Shot count exceeds episode bid count (scope creep warning)',
            'Slack: POST to Webhook URL (no auth needed, just a URL in Settings)',
            'Email: SMTP via smtplib (Gmail App Password, or SendGrid for production)',
            'Settings page: configure Slack webhook URL + alert email addresses',
        ],
        code_snippet='# Slack alert (simplest implementation):\nimport requests\ndef slack_alert(msg):\n    webhook = app.config.get("SLACK_WEBHOOK")\n    if webhook:\n        requests.post(webhook, json={"text": msg}, timeout=3)'
    )

    e.append(sp(4))
    e.append(section('Bonus: Per-Episode PDF One-Pager'))
    e.append(body('Generate a clean, producer-facing PDF summary for any single episode. '
                   'Content: episode header, shot count, budget vs EFC, risk badge, '
                   'awarded vendors list, and top 5 heaviest shots. '
                   'Uses the same ReportLab approach as the Tutorial and Security PDFs. '
                   'Accessible from each EP page via an "Export PDF" button.'))
    e.append(tip('This PDF is designed to be sent to a studio executive or client without '
                  'exposing the full budget system. It shows summary numbers only.'))

    e.append(PageBreak())
    return e

def ch7():
    e = []
    e += chapter_header('7', 'Implementation Roadmap', 'Phased plan with dependencies and timeline')

    e.append(section('Week-by-Week Plan'))
    e += col_table(
        ['Phase', 'Items', 'Effort', 'Code Risk', 'Visible to Users'],
        [
            ['Week 1\nQuick Wins',    '#3 Virtual DOM\n#8 Unsaved Warning\n#11 Auto-save Indicator\n#6 Shared JS utils',    '2 days total', 'None',   'YES -- immediate'],
            ['Week 2\nUX Polish',     '#9 Keyboard Shortcuts\n#13 Duplicate Shot Detect\n#2 Lazy-load Nav',                 '2 days total', 'None',   'YES'],
            ['Week 3\nData Safety',   '#12 Input Validation\n#14 Orphaned Assets\n#4 DB Connection Pool',                   '3 days total', 'Low',    'Partial'],
            ['Week 4\nPerformance',   '#1 API Caching\n#10 Bulk Row Operations',                                            '3 days total', 'Low',    'YES -- speed'],
            ['Month 2\nNew Features', '#15 Change History\n#17 Email/Slack Alerts',                                         '1 week',       'Low',    'YES'],
            ['Month 3\nArchitecture', '#5 Split app.py Blueprints\n#7 Blueprint refactor complete',                         '1 week',       'Medium', 'No (internal)'],
            ['Month 4\nv05 Features', '#16 Season Dashboard\nPer-EP PDF one-pager',                                         '2 weeks',      'Low',    'YES -- new pages'],
        ],
        col_widths=[22*mm, 70*mm, 22*mm, 20*mm, 26*mm]
    )

    e.append(section('Dependencies'))
    e.append(body('Some optimizations depend on others being completed first:'))
    e += arch_box([
        '#15 Change History  requires  #4 DB Connection Pool  (clean conn handling)',
        '#16 Dashboard       requires  #15 Change History     (burn chart data source)',
        '#5  Blueprint split requires  #4 DB Connection Pool  (move get_db() to db.py first)',
        '#17 Slack Alerts    requires  #12 Input Validation   (avoid alerting on bad data)',
        '',
        'All other items are independent and can be done in any order.',
    ])

    e.append(section('What Stays Unchanged Throughout'))
    e.append(body('These parts of the system are NOT touched in any optimization phase:'))
    e.append(bullet('All 11 HTML templates (structure and layout unchanged)'))
    e.append(bullet('All Tabulator column definitions and cell formatters'))
    e.append(bullet('All API endpoint URLs and response formats'))
    e.append(bullet('All LLM / AI streaming features'))
    e.append(bullet('All Excel import and export logic'))
    e.append(bullet('Delivery Risk Score calculation'))
    e.append(bullet('Vendor Confidence Score calculation'))
    e.append(bullet('Invoice Log Vendor Registry and Capacity Tracker'))
    e.append(bullet('All cross-template data connections (/api/vendors/all etc.)'))

    e.append(PageBreak())
    return e

def ch8():
    e = []
    e += chapter_header('8', 'Future Version — v05', 'Proposed scope for the next major version')

    e.append(section('v05 Goals'))
    e.append(body('Version 05 should represent a fully production-hardened system. '
                   'All optimizations from this guide are complete, plus significant new features '
                   'aimed at making the system the single source of truth for a full season.'))

    e.append(section('Proposed v05 Feature Set'))
    e += col_table(
        ['Category', 'Feature', 'Description'],
        [
            ['Architecture',  'Blueprint refactor',       'app.py split into modular routes/ structure'],
            ['Architecture',  'PostgreSQL',               'Full migration from SQLite for multi-user production'],
            ['Architecture',  'Google OAuth login',       'Studio Google accounts as authentication'],
            ['Architecture',  'Tailscale VPN',            'App invisible to public internet'],
            ['Performance',   'API caching',              'All list endpoints cached 30s'],
            ['Performance',   'Virtual DOM tables',       'All Tabulator instances virtualised'],
            ['UX',            'Season Dashboard',         'New /dashboard page with charts and heatmap'],
            ['UX',            'Bulk row operations',      'Multi-select and bulk edit on all tables'],
            ['UX',            'Per-EP PDF export',        'One-pager PDF per episode for execs'],
            ['Data',          'Change history',           'Full audit trail for all financial edits'],
            ['Data',          'Input validation',         'Numeric gates, duplicate detection, orphan alerts'],
            ['Alerts',        'Slack / email alerts',     'Risk escalation and invoice approval notifications'],
            ['AI',            'Smarter prompts',          'AI sees change history for better context'],
            ['AI',            'Budget anomaly detection', 'AI flags statistically unusual EFC movements'],
            ['Google Drive',  'Drive Picker import',      'Import Excel directly from Drive in all pages'],
            ['Google Drive',  'DB backup to Drive',       'Automatic nightly DB backup to Drive folder'],
        ],
        col_widths=[28*mm, 45*mm, 87*mm]
    )

    e.append(section('AI Enhancement Roadmap'))
    e.append(body('The current AI system (Ollama SSE streaming, 4 task types) is a strong foundation. '
                   'v05 can extend it significantly:'))
    e += col_table(
        ['Task', 'Input', 'Output'],
        [
            ['Budget Anomaly',    'EFC history, change log',               'Alert if EFC moved >15% in <24hrs'],
            ['Vendor Comparison', 'All vendor bids + confidence scores',   'Narrative recommendation: which vendor to award'],
            ['Risk Narrative',    'Risk score, shot breakdown, timeline',  'Full risk memo with mitigation suggestions'],
            ['Season Forecast',   'All EPs EST, EFC, delivery status',     'Season completion forecast with confidence interval'],
            ['Note Clustering',   'All open VFX notes',                    'Group by theme, flag blockers, suggest resolutions'],
        ],
        col_widths=[35*mm, 55*mm, 70*mm]
    )

    e.append(section('Estimated v05 Timeline'))
    e += info_table([
        ('Weeks 1-4',   'All 17 optimizations from this guide (Tier 1-4)'),
        ('Month 2',     'Change history, alerts, bulk operations (Tier 5 new features)'),
        ('Month 3',     'Blueprint refactor, PostgreSQL migration'),
        ('Month 4',     'Google OAuth, Tailscale, security hardening'),
        ('Month 5',     'Season Dashboard, per-EP PDF, AI enhancements'),
        ('Month 6',     'Google Drive integration, testing, QA, v05 release'),
    ])

    e.append(sp(10))
    e.append(hr(C_TEAL, 1))
    e.append(sp(6))
    e.append(Paragraph('End of Optimization &amp; Future Development Guide  --  VFX Budget System v04', S['cover_sub']))
    e.append(Paragraph('Reference document -- update as items are completed', S['caption']))

    return e

# ── Build ──────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=18*mm,
    )
    story = []
    story += cover()
    story += toc()
    story += ch1()
    story += ch2()
    story += ch3()
    story += ch4()
    story += ch5()
    story += ch6()
    story += ch7()
    story += ch8()

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    print(f'PDF generated: {OUT}')

if __name__ == '__main__':
    build()
