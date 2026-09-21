"""
VFX Budget System — DB Connection Workflow Guide Generator
Run: python generate_db_workflow_guide.py
Output: VFX_Budget_System_DB_Workflow.pdf

Covers:
  - Two-database architecture (projects.db + per-project .vfxdb)
  - Full request lifecycle: Browser → Flask → Blueprint → core → SQLite
  - Connection pooling via Flask g + _GConn deferred-close wrapper
  - Session-scoped project selection
  - Schema: all 16 tables with column summaries
  - Key data flows (shots, invoices, optimizer, vendor performance)
  - Startup migration sequence
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

OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_DB_Workflow.pdf')
W, H = A4

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
C_DARK   = colors.HexColor('#0a0b14')
C_PURPLE = colors.HexColor('#9b59b6')
C_TEAL   = colors.HexColor('#1abc9c')

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def P(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)
    return {
        'cover_title': P('cover_title',
            fontSize=28, leading=34, textColor=C_GOLD,
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
        'tip': P('tip',
            fontSize=9.5, leading=14, textColor=C_GREEN,
            fontName='Helvetica-Oblique', leftIndent=10, spaceAfter=4),
        'warn': P('warn',
            fontSize=9.5, leading=14, textColor=C_ORANGE,
            fontName='Helvetica-Oblique', leftIndent=10, spaceAfter=4),
        'code': P('code',
            fontSize=8.5, leading=13, textColor=C_BLUE,
            fontName='Courier', leftIndent=12, spaceAfter=2,
            backColor=C_ACCENT),
        'code_comment': P('code_comment',
            fontSize=8.5, leading=13, textColor=C_MUTED,
            fontName='Courier', leftIndent=12, spaceAfter=2,
            backColor=C_ACCENT),
        'label': P('label',
            fontSize=8, leading=11, textColor=C_MUTED,
            fontName='Helvetica-Bold', spaceAfter=2),
        'flow_box': P('flow_box',
            fontSize=9.5, leading=13, textColor=C_BG,
            fontName='Helvetica-Bold', alignment=TA_CENTER),
        'flow_sub': P('flow_sub',
            fontSize=8, leading=11, textColor=C_ACCENT,
            fontName='Helvetica', alignment=TA_CENTER),
        'arrow': P('arrow',
            fontSize=14, leading=16, textColor=C_GOLD,
            fontName='Helvetica-Bold', alignment=TA_CENTER),
        'caption': P('caption',
            fontSize=8, leading=11, textColor=C_MUTED,
            fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4),
        'toc_entry': P('toc_entry',
            fontSize=10.5, leading=15, textColor=C_TEXT,
            fontName='Helvetica', leftIndent=6, spaceAfter=2),
        'toc_sub': P('toc_sub',
            fontSize=9, leading=13, textColor=C_MUTED,
            fontName='Helvetica', leftIndent=18, spaceAfter=1),
        'table_title': P('table_title',
            fontSize=9, leading=12, textColor=C_GOLD,
            fontName='Helvetica-Bold', spaceAfter=1),
    }

S = make_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(pts=6):    return Spacer(1, pts)
def hr(c=C_BORDER, t=0.5): return HRFlowable(width='100%', thickness=t, color=c, spaceAfter=5, spaceBefore=3)
def body(txt):    return Paragraph(txt, S['body'])
def sec(txt):     return Paragraph(txt, S['section'])
def bul(txt):     return Paragraph(txt, S['bullet'])
def tip(txt):     return Paragraph(f'TIP  {txt}', S['tip'])
def warn(txt):    return Paragraph(f'NOTE  {txt}', S['warn'])
def code(txt):    return Paragraph(txt, S['code'])
def comment(txt): return Paragraph(f'# {txt}', S['code_comment'])

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

def col_table(headers, rows, widths=None):
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

# ── Flow diagram helpers ───────────────────────────────────────────────────────
def flow_box(label, sublabel='', bg=C_BLUE):
    """Single coloured box for flow diagrams."""
    inner = [Paragraph(label, S['flow_box'])]
    if sublabel:
        inner.append(Paragraph(sublabel, S['flow_sub']))
    t = Table([[inner]], colWidths=[160*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), bg),
        ('TOPPADDING', (0,0),(-1,-1), 7),
        ('BOTTOMPADDING',(0,0),(-1,-1), 7),
        ('LEFTPADDING',(0,0),(-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('BOX',        (0,0),(-1,-1), 0.8, C_BORDER),
    ]))
    return t

def flow_arrow(label=''):
    txt = f'▼  {label}' if label else '▼'
    return Paragraph(txt, S['arrow'])

def flow_row(items, widths=None):
    """
    Row of coloured boxes side by side.
    items: list of (label, sublabel, bg_color)
    """
    n = len(items)
    w = widths or [(160/n)*mm]*n
    cells = []
    for label, sublabel, bg in items:
        inner = [Paragraph(label, S['flow_box'])]
        if sublabel:
            inner.append(Paragraph(sublabel, S['flow_sub']))
        cells.append(inner)
    t = Table([cells], colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (i,0),(i,0), items[i][2]) for i in range(n)
    ] + [
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
        ('BOX',           (0,0),(-1,-1), 0.8, C_BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.5, C_BORDER),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    return t

def numbered_flow(steps):
    """
    Vertical numbered flow.
    steps: list of (num_label, box_label, sublabel, bg)
    """
    items = []
    for i, (num_lbl, box_lbl, sublbl, bg) in enumerate(steps):
        num_cell = [Paragraph(f'<font color="#f0b429"><b>{num_lbl}</b></font>', S['body'])]
        box_inner = [Paragraph(box_lbl, S['flow_box'])]
        if sublbl:
            box_inner.append(Paragraph(sublbl, S['flow_sub']))
        row = Table([[num_cell, box_inner]], colWidths=[12*mm, 148*mm])
        row.setStyle(TableStyle([
            ('BACKGROUND', (1,0),(1,0), bg),
            ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0),(-1,-1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
            ('LEFTPADDING',(0,0),(-1,-1), 5),
            ('RIGHTPADDING',(0,0),(-1,-1), 5),
            ('BOX',        (1,0),(1,0), 0.6, C_BORDER),
        ]))
        items.append(row)
        if i < len(steps) - 1:
            items.append(Paragraph('      ▼', S['arrow']))
    return items

# ── Page callbacks ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H-12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H-7*mm, 'VFX BUDGET SYSTEM')
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W-15*mm, H-7*mm, 'DB CONNECTION WORKFLOW')
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
    canvas.drawCentredString(W/2, H-11*mm, 'VFX BUDGET SYSTEM  —  DB CONNECTION WORKFLOW')
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
    e.append(Paragraph('Database Connection Workflow', S['cover_sub']))
    e.append(sp(2))
    e.append(Paragraph('Architecture · Lifecycle · Schema · Data Flows', S['cover_ver']))
    e.append(sp(22))
    e.append(hr(C_GOLD, 1.5))
    e.append(sp(10))
    for k, v in [
        ('DATABASES',  'projects.db (registry)  +  per-project .vfxdb files'),
        ('POOLING',    'Flask g + _GConn deferred-close wrapper per request'),
        ('SCHEMA',     '16 tables: shots, assets, invoices, vendors, optimizer, audit'),
        ('FLOWS',      'Read · Write · Session · Migration · Teardown'),
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
        ('1', 'Two-Database Architecture',
         ['projects.db — the project registry', '.vfxdb — per-project data files',
          'File locations and naming']),
        ('2', 'Full Request Lifecycle',
         ['Browser → Flask router → Blueprint → core.get_db()',
          'Connection pooling via Flask g', '_GConn deferred-close wrapper',
          'Response → teardown → real close']),
        ('3', 'Session-Scoped Project Selection',
         ['How a project is "opened"', 'session[\'project_db\'] path',
          'require_project() guard', 'Switching projects']),
        ('4', 'Startup Sequence & Migrations',
         ['app.py startup order', 'init_projects_db()', 'migrate_legacy_db()',
          'migrate_db_schema() — adding new columns safely']),
        ('5', 'Database Schema — All 16 Tables',
         ['Core production tables', 'Financial tables',
          'Optimizer & performance tables', 'System tables']),
        ('6', 'Key Data Flows',
         ['Shot read/write flow', 'Invoice-to-shot linking flow',
          'Vendor performance score flow', 'Season optimizer flow',
          'Change log (audit) flow']),
        ('7', 'Connection Reference',
         ['get_db() vs get_projects_db()', 'PRAGMA settings',
          'Error handling patterns', 'Cache invalidation']),
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


def s1_architecture():
    e = []
    e += ch_header('1', 'Two-Database Architecture',
                   'projects.db holds the project list; each project has its own .vfxdb file')

    e.append(body(
        'The system uses two separate SQLite databases. This separation keeps the project '
        'registry lightweight and isolates all production data per show, making backup, '
        'archiving, and portability trivial — one .vfxdb file = one complete project.'
    ))

    e.append(sec('Database 1 — projects.db  (Registry)'))
    e += info_table([
        ('File',     'projects.db  (always at the app root)'),
        ('Purpose',  'Stores the list of all projects — name, season, file path, episode range'),
        ('Tables',   'projects  (1 table only)'),
        ('Accessed', 'On the Projects home page and whenever a project is opened or created'),
        ('Function', 'get_projects_db()  in core.py — opens a fresh connection each time'),
    ])
    e.append(code('PROJECTS_DB = os.path.join(BASE_DIR, "projects.db")'))
    e.append(code('def get_projects_db():'))
    e.append(code('    conn = sqlite3.connect(PROJECTS_DB)'))
    e.append(code('    conn.row_factory = sqlite3.Row'))
    e.append(code('    return conn'))
    e.append(sp(6))

    e.append(sec('Database 2 — ProjectName_S1.vfxdb  (Per-Project)'))
    e += info_table([
        ('File',     'projects/ANDOR_S2.vfxdb  (one file per project, in projects/ folder)'),
        ('Naming',   'Generated as  {NAME}_{SEASON}.vfxdb  when project is created'),
        ('Purpose',  'All production data: shots, assets, invoices, bids, notes, settings'),
        ('Tables',   '16 tables — see Section 5 for full schema'),
        ('Accessed','get_db()  in core.py — session-scoped, pooled via Flask g'),
        ('Override', 'Set VFX_PROJECTS_DIR environment variable to change the default folder'),
    ])

    e.append(sec('Visual Layout'))
    # Architecture diagram as a table
    diag_data = [
        [
            Paragraph('<b>APP ROOT</b>', S['label']),
            Paragraph('<b>projects/ FOLDER</b>', S['label']),
        ],
        [
            Paragraph(
                'app.py\ncore.py\nllm.py\nrequirements.txt\n\n'
                '<font color="#f0b429"><b>projects.db</b></font>\n(registry)',
                S['code']),
            Paragraph(
                '<font color="#4a9cf0">ANDOR_S2.vfxdb</font>\n'
                '<font color="#4a9cf0">SIDEWINDER_S1.vfxdb</font>\n'
                '<font color="#4a9cf0">DUNE_S3.vfxdb</font>\n'
                '  ...',
                S['code']),
        ],
    ]
    diag = Table(diag_data, colWidths=[75*mm, 85*mm])
    diag.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(0,0), C_PANEL),
        ('BACKGROUND', (1,0),(1,0), C_PANEL),
        ('BACKGROUND', (0,1),(0,1), C_ACCENT),
        ('BACKGROUND', (1,1),(1,1), C_DARK),
        ('GRID',       (0,0),(-1,-1), 0.6, C_BORDER),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING',(0,0),(-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('TEXTCOLOR',  (0,0),(-1,0), C_GOLD),
    ]))
    e.append(diag)
    e.append(sp(4))
    e.append(tip(
        'To back up a project, copy its .vfxdb file. '
        'To restore, place it back in the projects/ folder and reopen it from the home screen.'
    ))

    e.append(PageBreak())
    return e


def s2_request_lifecycle():
    e = []
    e += ch_header('2', 'Full Request Lifecycle',
                   'From browser click to SQLite row and back')

    e.append(body(
        'Every page load and API call follows this path. Understanding it explains '
        'why connections are safe under concurrent use and why they never leak.'
    ))

    e.append(sec('Complete Flow Diagram'))
    steps = [
        ('1', 'BROWSER',
         'User clicks a page or triggers an AJAX/fetch call',
         C_TEAL),
        ('2', 'FLASK ROUTER  (app.py)',
         'before_request: check auth → session valid? → allow or redirect to /login',
         C_PURPLE),
        ('3', 'BLUEPRINT ROUTE HANDLER  (routes/*.py)',
         'e.g. routes/episodes.py  @bp.route("/api/shots/<ep>")  →  calls core.get_db()',
         C_BLUE),
        ('4', 'core.get_db()',
         'Read session["project_db"] path → check Flask g for existing connection → '
         'open new sqlite3 connection if first call this request → return _GConn wrapper',
         C_GOLD),
        ('5', 'SQLITE EXECUTE  (projects/Name.vfxdb)',
         'conn.execute(SQL, params) → rows returned as sqlite3.Row dict-like objects',
         C_GREEN),
        ('6', 'BLUEPRINT RETURNS RESPONSE',
         'jsonify(rows) or render_template(html) → Flask sends HTTP response to browser',
         C_BLUE),
        ('7', 'TEARDOWN  (app.teardown_appcontext)',
         'close_db_connections() iterates g keys starting with "db_" → calls _real_close() '
         'on each _GConn wrapper → underlying sqlite3 connection is closed',
         C_ORANGE),
    ]
    e += numbered_flow(steps)
    e.append(sp(10))

    e.append(sec('Connection Pooling — Flask g'))
    e.append(body(
        'Flask\'s application context object <b>g</b> lives for exactly one request. '
        'The first call to <b>get_db()</b> within a request opens a connection and '
        'stores it on g under a key based on the DB file path. '
        'Every subsequent call within the same request returns the same connection object — '
        'no extra connections are opened.'
    ))
    e.append(code('g_key = "db_" + db_path'))
    e.append(code('wrapped = getattr(g, g_key, None)'))
    e.append(code('if wrapped is None:'))
    e.append(code('    conn = sqlite3.connect(db_path)'))
    e.append(code('    wrapped = _GConn(conn)'))
    e.append(code('    setattr(g, g_key, wrapped)'))
    e.append(code('return wrapped'))
    e.append(sp(6))

    e.append(sec('_GConn — Deferred-Close Wrapper'))
    e.append(body(
        'Blueprint code calls <b>conn.close()</b> as a safety habit in many route handlers. '
        'Without protection this would close the connection mid-request if another handler '
        'calls get_db() again. The <b>_GConn</b> wrapper silences <b>close()</b> — '
        'the actual close only happens during teardown via <b>_real_close()</b>.'
    ))
    e += col_table(
        ['Method', 'Behaviour'],
        [
            ['conn.close()',       'No-op — silently ignored during the request'],
            ['conn._real_close()', 'Closes the underlying sqlite3 connection — called by teardown only'],
            ['conn.<any other>',   '__getattr__ proxies all other calls directly to the real connection'],
        ],
        widths=[45*mm, 115*mm]
    )

    e.append(sec('PRAGMA Settings Applied on Every Connection'))
    e += col_table(
        ['PRAGMA', 'Value', 'Effect'],
        [
            ['journal_mode', 'WAL',
             'Write-Ahead Logging — allows concurrent reads during writes; '
             'better performance for the typical Flask read-heavy workload'],
            ['foreign_keys', 'ON',
             'Enforces referential integrity on FOREIGN KEY constraints '
             '(e.g. invoice_shot_links → shots and invoice_log)'],
        ],
        widths=[32*mm, 20*mm, 108*mm]
    )

    e.append(PageBreak())
    return e


def s3_session():
    e = []
    e += ch_header('3', 'Session-Scoped Project Selection',
                   'How the active project is tracked across requests')

    e.append(body(
        'Flask\'s signed cookie session stores which project the user has open. '
        'The key <b>session["project_db"]</b> holds the full filesystem path to '
        'the active .vfxdb file. Every call to <b>get_db()</b> reads this key.'
    ))

    e.append(sec('Opening a Project — Flow'))
    steps = [
        ('1', 'User clicks  Open  on a project card (home screen)',
         'Browser POSTs to  /api/projects/<id>/open',
         C_TEAL),
        ('2', 'routes/projects.py  open_project()',
         'Looks up db_path from projects.db for the given project id',
         C_BLUE),
        ('3', 'Writes to Flask session',
         'session["project_db"] = db_path\n'
         'session["ep_start"] = proj["ep_start"]\n'
         'session["ep_end"] = proj["ep_end"]',
         C_GOLD),
        ('4', 'Updates projects.db',
         'Sets last_opened = now() for the project row',
         C_PURPLE),
        ('5', 'Redirects to /distribution',
         'All subsequent requests use session["project_db"] to open the .vfxdb',
         C_GREEN),
    ]
    e += numbered_flow(steps)
    e.append(sp(8))

    e.append(sec('require_project() Guard'))
    e.append(body(
        'Every Blueprint route that needs project data calls '
        '<b>core.require_project()</b> at the top. '
        'If no project is selected or the .vfxdb file is missing, '
        'the session is cleared and the user is redirected to the home screen.'
    ))
    e.append(code('def require_project():'))
    e.append(code('    if not session.get("project_db") or \\'))
    e.append(code('       not os.path.exists(session["project_db"]):'))
    e.append(code('        session.clear()'))
    e.append(code('        return redirect(url_for("projects.project_list"))'))
    e.append(code('    return None'))
    e.append(sp(4))
    e.append(body('Route handlers call it like this:'))
    e.append(code('r = core.require_project()'))
    e.append(code('if r: return r     # redirect if no project'))
    e.append(code('conn = core.get_db()'))
    e.append(sp(6))

    e.append(sec('Switching Projects'))
    e.append(body(
        'Opening a different project simply overwrites <b>session["project_db"]</b> '
        'with the new file path. The next request\'s <b>get_db()</b> call opens a fresh '
        'connection to the new file. The previous connection is already closed by teardown.'
    ))

    e.append(sec('Session Data Stored'))
    e += col_table(
        ['Session Key', 'Type', 'Content'],
        [
            ['project_db',     'str',  'Full path to the active .vfxdb file'],
            ['ep_start',       'int',  'First episode number for this project (e.g. 201)'],
            ['ep_end',         'int',  'Last episode number (e.g. 208)'],
            ['authenticated',  'bool', 'True if password auth is enabled and user has logged in'],
        ],
        widths=[35*mm, 15*mm, 110*mm]
    )
    e.append(warn(
        'The session is a signed browser cookie — data is visible to the user '
        'but cannot be tampered with (signed with app.secret_key). '
        'Never store sensitive data (passwords, keys) in the session.'
    ))

    e.append(PageBreak())
    return e


def s4_startup():
    e = []
    e += ch_header('4', 'Startup Sequence & Migrations',
                   'What happens before the first request is served')

    e.append(body(
        'When you run <b>python app.py</b>, four functions execute in order '
        'before Flask starts accepting connections. These are safe to run on every '
        'launch — all use CREATE TABLE IF NOT EXISTS and ADD COLUMN IF NOT EXISTS patterns.'
    ))

    e.append(sec('Startup Order'))
    steps = [
        ('1', 'core.init_projects_db()',
         'CREATE TABLE IF NOT EXISTS projects — ensures registry table exists',
         C_BLUE),
        ('2', 'core.migrate_legacy_db()',
         'If vfx_system.db exists at app root (old single-DB layout), '
         'registers it as a project in projects.db with name "SIDEWINDER"',
         C_PURPLE),
        ('3', 'core.migrate_db_schema()',
         'Adds any new columns introduced by updates to all existing .vfxdb files. '
         'Creates new tables (e.g. invoice_shot_links) if missing.',
         C_GOLD),
        ('4', 'core._init_slack(app)',
         'Loads slack_config.json and sets app.config["SLACK_WEBHOOK"]',
         C_TEAL),
        ('5', 'app.run(host, port)',
         'Flask begins serving requests on http://0.0.0.0:5000',
         C_GREEN),
    ]
    e += numbered_flow(steps)
    e.append(sp(8))

    e.append(sec('migrate_db_schema() — How It Works'))
    e.append(body(
        'This function iterates every .vfxdb file in the projects/ folder '
        'and applies schema additions. It is additive-only — it never drops '
        'columns or tables, so existing data is always preserved.'
    ))
    e += col_table(
        ['Operation', 'Method', 'Safe to Re-run?'],
        [
            ['Add a new column to an existing table',
             'ALTER TABLE … ADD COLUMN … wrapped in try/except — '
             'silently ignored if column already exists',
             'Yes'],
            ['Create a new table',
             'CREATE TABLE IF NOT EXISTS',
             'Yes'],
            ['Backfill default values',
             'UPDATE … SET col = default WHERE col IS NULL',
             'Yes'],
        ],
        widths=[40*mm, 90*mm, 30*mm]
    )
    e.append(tip(
        'When adding a new feature that needs a new column or table, '
        'add the CREATE/ALTER statement to migrate_db_schema(). '
        'It will be applied to every existing project on next launch.'
    ))

    e.append(sec('init_project_db() — New Project Creation'))
    e.append(body(
        'When a user creates a new project, <b>init_project_db(db_path, ep_start, ep_end)</b> '
        'creates the .vfxdb file with all 16 tables and seeds ep_meta and ep_forecast rows '
        'for each episode in the range.'
    ))
    e.append(code('core.init_project_db(db_path, ep_start=201, ep_end=208)'))
    e.append(body(
        'This is called once at project creation time. All subsequent connections '
        'go through <b>get_db()</b> as normal.'
    ))

    e.append(PageBreak())
    return e


def s5_schema():
    e = []
    e += ch_header('5', 'Database Schema — All 16 Tables',
                   'Complete table inventory with primary columns and purpose')

    e.append(body(
        'Every project .vfxdb file contains the same 16 tables. '
        'The projects.db registry contains only 1 table (projects).'
    ))

    e.append(sec('Core Production Tables'))
    e += col_table(
        ['Table', 'Primary Key', 'Key Columns', 'Purpose'],
        [
            ['shots',
             'id',
             'ep, scene_code, shot_type, complexity, cost_est, efc, award_vendor, omit, status',
             'Every VFX shot. Central table — most pages read/write here.'],
            ['ep_meta',
             'ep',
             'script_v, edit_v, status, est_reduction',
             'Per-episode metadata (script version, edit version, status).'],
            ['assets',
             'id',
             'ep, asset_name, asset_type, description, award_vendor, est_budget, actual_spend',
             'VFX asset master list (CG chars, environments, props).'],
            ['vfx_notes',
             'id',
             'item_num, author, note_text, note_date, resolved',
             'Production notes and action items.'],
            ['sequences',
             'id',
             'ep, seq_name, location, est_shots, lbudget, efc, status',
             'Episode sequences for grouping shots.'],
        ],
        widths=[32*mm, 18*mm, 60*mm, 50*mm]
    )

    e.append(sec('Financial Tables'))
    e += col_table(
        ['Table', 'Primary Key', 'Key Columns', 'Purpose'],
        [
            ['bid_compare',
             'id',
             'ep, sc, vendor_bids (JSON), award, lockbudget, efc, version',
             'Multi-vendor bid grid. vendor_bids stored as JSON {vendor: amount}.'],
            ['vendor_tracker',
             'id',
             'vendor, ep, tot_award, paid, pending, remaining',
             'Lightweight per-vendor per-episode invoice tracking.'],
            ['invoice_log',
             'id',
             'vendor, episode, inv_num, inv_date, amount, status, approve_date',
             'Formal invoice ledger with approval workflow.'],
            ['vendor_registry',
             'id',
             'vendor (UNIQUE), region, fx_rate, tax_pct, rebate_pct, contact',
             'Master vendor list with financial rates.'],
            ['budget_scenario',
             'id',
             'scenario_type, ep, tax_pct, eligible_pct, net_cost',
             'Budget scenario / what-if modelling rows.'],
            ['ep_forecast',
             'ep',
             'contingency, budget, award, eligible, global_rebate_pct',
             'Per-episode budget forecast and rebate modelling.'],
            ['vendor_forecast',
             'id',
             'vendor, ep, gross_local, gross_usd, region, eligible_pct, rebate_pct',
             'Per-vendor per-episode financial forecast for rebate calculations.'],
            ['budget_history',
             'id',
             'ep, record_date, version_label, est_shots, est_budget, efc_budget',
             'Historical budget snapshots for trend analysis.'],
        ],
        widths=[32*mm, 18*mm, 60*mm, 50*mm]
    )

    e.append(sec('Optimizer & Link Tables (Sprint 3 & 4)'))
    e += col_table(
        ['Table', 'Primary Key', 'Key Columns', 'Purpose'],
        [
            ['vendor_capacity',
             'id',
             'vendor (UNIQUE), shots_per_month, efficiency_pct',
             'Vendor throughput data — drives capacity risk score and optimizer.'],
            ['invoice_shot_links',
             'id',
             'invoice_id, shot_id  (UNIQUE pair)',
             'Junction table linking invoice_log rows to shots rows.'],
            ['shot_asset_links',
             'id',
             'shot_id, asset_id  (UNIQUE pair)',
             'Junction table linking shots to assets.'],
        ],
        widths=[35*mm, 18*mm, 55*mm, 52*mm]
    )

    e.append(sec('System Tables'))
    e += col_table(
        ['Table', 'Primary Key', 'Key Columns', 'Purpose'],
        [
            ['change_log',
             'id',
             'table_name, row_id, field, old_value, new_value, user, timestamp',
             'Full audit trail. Written by log_change() on every field edit.'],
            ['project_settings',
             'key',
             'key (TEXT PK), value (TEXT)',
             'Per-project key-value settings store (currency, season label, etc.).'],
        ],
        widths=[35*mm, 18*mm, 60*mm, 47*mm]
    )

    e.append(sec('projects.db — Registry Table'))
    e += col_table(
        ['Column', 'Type', 'Description'],
        [
            ['id',           'INTEGER PK', 'Auto-increment'],
            ['name',         'TEXT',       'Project name (e.g. ANDOR)'],
            ['season',       'TEXT',       'Season label (e.g. S2)'],
            ['db_filename',  'TEXT',       'Filename only (e.g. ANDOR_S2.vfxdb)'],
            ['db_path',      'TEXT',       'Full filesystem path to the .vfxdb file'],
            ['ep_start',     'INTEGER',    'First episode number'],
            ['ep_end',       'INTEGER',    'Last episode number'],
            ['last_opened',  'TIMESTAMP',  'Updated each time the project is opened'],
            ['created_at',   'TIMESTAMP',  'When the project was created'],
        ],
        widths=[30*mm, 22*mm, 108*mm]
    )

    e.append(PageBreak())
    return e


def s6_data_flows():
    e = []
    e += ch_header('6', 'Key Data Flows',
                   'End-to-end traces for the most important operations')

    # ── Shot read flow ──
    e.append(sec('Flow A — Shot Read (Episode Page Load)'))
    steps = [
        ('1', 'Browser loads /ep/203',
         'GET request → routes/episodes.py  ep_page()',
         C_TEAL),
        ('2', 'require_project() + get_db()',
         'Session["project_db"] = "projects/ANDOR_S2.vfxdb" → connection opened/reused',
         C_BLUE),
        ('3', 'SQL: SELECT * FROM shots WHERE ep=203 AND omit=0',
         'Returns sqlite3.Row objects with all shot columns',
         C_GREEN),
        ('4', 'render_template("ep.html", shots=rows)',
         'Jinja2 renders HTML with shot data → response sent to browser',
         C_GOLD),
        ('5', 'Teardown',
         'close_db_connections() → _real_close() on the connection',
         C_ORANGE),
    ]
    e += numbered_flow(steps)
    e.append(sp(8))

    # ── Shot write flow ──
    e.append(sec('Flow B — Shot Write (Inline Cell Edit)'))
    steps = [
        ('1', 'User edits a cell in the shot table',
         'Tabulator fires PUT /api/shots/<shot_id>  with JSON body',
         C_TEAL),
        ('2', 'routes/episodes.py  update_shot()',
         'Calls clean_cost() to sanitise the value if it is a cost field',
         C_BLUE),
        ('3', 'log_change(table, row_id, field, old, new)',
         'Writes one row to change_log for audit trail',
         C_PURPLE),
        ('4', 'UPDATE shots SET <field>=? WHERE id=?',
         'Updates the .vfxdb shots table; conn.commit()',
         C_GREEN),
        ('5', 'cache.clear()',
         'Invalidates the distribution/risk cache so next load re-computes',
         C_GOLD),
        ('6', 'Return jsonify({ok: true})',
         'Tabulator receives success → cell value confirmed in UI',
         C_TEAL),
    ]
    e += numbered_flow(steps)
    e.append(sp(8))

    e.append(PageBreak())

    # ── Invoice-shot linking flow ──
    e.append(sec('Flow C — Invoice-to-Shot Linking (Tag Shots Modal Save)'))
    steps = [
        ('1', 'User opens Tag Shots modal for invoice #42',
         'GET /api/invoicelog/42/shots → returns currently linked shot_ids',
         C_TEAL),
        ('2', 'User checks/unchecks shots and clicks Save',
         'POST /api/invoicelog/42/shots/bulk  with {shot_ids: [12, 15, 23]}',
         C_BLUE),
        ('3', 'DELETE FROM invoice_shot_links WHERE invoice_id=42',
         'Removes all existing links for this invoice',
         C_RED),
        ('4', 'INSERT INTO invoice_shot_links (invoice_id, shot_id) VALUES (42, ?)',
         'Inserts one row per checked shot_id',
         C_GREEN),
        ('5', 'conn.commit() → return {linked: 3}',
         'SHOTS column badge in Invoice Log updates to show "3"',
         C_GOLD),
    ]
    e += numbered_flow(steps)
    e.append(sp(8))

    # ── Vendor performance flow ──
    e.append(sec('Flow D — Vendor Performance Score Computation'))
    e.append(body(
        'Scores are computed on-the-fly from three tables each time the Invoice Log page loads. '
        'No scores are stored — they are always fresh.'
    ))
    e += col_table(
        ['Component', 'Source Table', 'Query'],
        [
            ['Bid Confidence (50%)',
             'bid_compare',
             'vendor_bids JSON → compute CV across all bid amounts per vendor'],
            ['Invoice Accuracy (30%)',
             'invoice_log',
             'COUNT(status IN PAID/APPROVED) / COUNT(*) per vendor'],
            ['Edit Efficiency (20%)',
             'shots',
             'COUNT(status IN DELIVERED/APPROVED) / COUNT(award_vendor = vendor)'],
        ],
        widths=[38*mm, 28*mm, 94*mm]
    )
    e.append(body('Formula:'))
    e.append(code('score = (bid_confidence * 0.50)'))
    e.append(code('      + (invoice_accuracy * 0.30)'))
    e.append(code('      + (edit_efficiency  * 0.20)'))
    e.append(sp(8))

    # ── Change log flow ──
    e.append(sec('Flow E — Audit Trail (change_log)'))
    e.append(body(
        'Every field edit writes one row to the <b>change_log</b> table. '
        'This is called from route handlers via <b>core.log_change()</b>.'
    ))
    e.append(code('log_change("shots", shot_id, "efc", old_val, new_val)'))
    e += col_table(
        ['Column', 'Example Value', 'Meaning'],
        [
            ['table_name', 'shots',        'Which table was edited'],
            ['row_id',     '412',          'Primary key of the edited row'],
            ['field',      'efc',          'Column that changed'],
            ['old_value',  '95000.0',      'Value before the edit'],
            ['new_value',  '110000.0',     'Value after the edit'],
            ['user',       'system',       'Always "system" (single-user app)'],
            ['timestamp',  '2026-03-15 …', 'UTC timestamp auto-set by SQLite'],
        ],
        widths=[28*mm, 28*mm, 104*mm]
    )
    e.append(tip('Browse the full audit history in the app via  AUDIT  in the navigation bar.'))

    e.append(PageBreak())
    return e


def s7_reference():
    e = []
    e += ch_header('7', 'Connection Reference',
                   'Quick-reference for all DB connection patterns in the codebase')

    e.append(sec('get_db() vs get_projects_db()'))
    e += col_table(
        ['Function', 'Opens', 'When to Use', 'Closes'],
        [
            ['get_db()',
             'Session\'s active .vfxdb file',
             'All production data access (shots, assets, invoices, etc.)',
             'Automatically at teardown via close_db_connections()'],
            ['get_projects_db()',
             'projects.db (registry)',
             'Project listing, opening, creating, deleting projects',
             'Caller is responsible — always call conn.close() explicitly'],
        ],
        widths=[35*mm, 30*mm, 55*mm, 40*mm]
    )
    e.append(warn(
        'get_projects_db() returns a raw sqlite3 connection — not a _GConn wrapper. '
        'Always call conn.close() after use in route handlers that call get_projects_db().'
    ))

    e.append(sec('Standard Route Handler Pattern'))
    e.append(code('@bp.route("/api/example")'))
    e.append(code('def example():'))
    e.append(comment('  1. Guard — redirect if no project open'))
    e.append(code('    r = core.require_project()'))
    e.append(code('    if r: return r'))
    e.append(comment('  2. Get pooled project connection'))
    e.append(code('    conn = core.get_db()'))
    e.append(code('    if not conn: return jsonify({"error": "No project"}), 400'))
    e.append(comment('  3. Query'))
    e.append(code('    rows = conn.execute("SELECT …").fetchall()'))
    e.append(comment('  4. Return — do NOT call conn.close() here'))
    e.append(code('    return jsonify([dict(r) for r in rows])'))
    e.append(sp(4))
    e.append(tip(
        'Do not call conn.close() on the object returned by get_db(). '
        'The _GConn wrapper silences it, but it is cleaner to omit the call entirely. '
        'Teardown handles it.'
    ))

    e.append(sec('Cache Invalidation Pattern'))
    e.append(body(
        'After any write operation, call <b>core.cache.clear()</b> '
        'so the distribution page and risk forecast re-compute on the next load. '
        'This is wired to flask-caching when installed; falls back to a no-op otherwise.'
    ))
    e.append(code('conn.execute("UPDATE shots SET efc=? WHERE id=?", (val, sid))'))
    e.append(code('conn.commit()'))
    e.append(code('core.cache.clear()   # invalidate cached aggregates'))
    e.append(sp(6))

    e.append(sec('Error Handling Conventions'))
    e += col_table(
        ['Pattern', 'Where Used', 'Behaviour'],
        [
            ['if not conn: return 400',
             'API routes',
             'Returns {error: "No project"} JSON if session has no project open'],
            ['try/except around conn.execute',
             'log_change(), sync_tracker_paid()',
             'Silently catches DB errors so UI operations do not fail due to audit writes'],
            ['clean_cost(v)',
             'All cost/EFC field writes',
             'Strips $/ commas, clamps negatives to 0, rejects values over $10M'],
            ['_sfloat(v)',
             'Vendor financial calculations',
             'Returns None for error strings — allows NULL in aggregations'],
        ],
        widths=[40*mm, 38*mm, 82*mm]
    )

    e.append(sec('Environment Variable Overrides'))
    e += info_table([
        ('VFX_PROJECTS_DIR', 'Override the default projects/ folder path — useful for network shares'),
        ('VFX_PASSWORD',     'Set a password via environment variable instead of auth_config.json'),
    ])

    e.append(sp(10))
    e.append(hr(C_GOLD, 1))
    e.append(sp(6))
    e.append(Paragraph(
        'VFX Budget System  —  DB Connection Workflow',
        S['cover_sub']
    ))
    e.append(Paragraph(
        'core.py is the single source of truth for all database operations.',
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
    story += s1_architecture()
    story += s2_request_lifecycle()
    story += s3_session()
    story += s4_startup()
    story += s5_schema()
    story += s6_data_flows()
    story += s7_reference()

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    print(f'\nPDF generated: {OUT}\n')

if __name__ == '__main__':
    build()
