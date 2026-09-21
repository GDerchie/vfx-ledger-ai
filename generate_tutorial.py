"""
VFX Budget System v04 — PDF Tutorial Generator
Run: python generate_tutorial.py
Output: VFX_Budget_System_Tutorial.pdf
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
from reportlab.platypus import Flowable
import os

# ── Palette ──────────────────────────────────────────────────────────────────
C_BG       = colors.HexColor('#0d0e18')
C_PANEL    = colors.HexColor('#12152a')
C_BORDER   = colors.HexColor('#2e3050')
C_GOLD     = colors.HexColor('#f0b429')
C_BLUE     = colors.HexColor('#4a9cf0')
C_GREEN    = colors.HexColor('#52c46a')
C_RED      = colors.HexColor('#e05252')
C_MUTED    = colors.HexColor('#7880a0')
C_TEXT     = colors.HexColor('#d0d8f0')
C_WHITE    = colors.HexColor('#ffffff')
C_DARK     = colors.HexColor('#1a1d35')
C_ORANGE   = colors.HexColor('#e08232')
C_ACCENT   = colors.HexColor('#1e2240')

OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_Tutorial.pdf')

W, H = A4

# ── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def P(name, parent='Normal', **kw):
        s = ParagraphStyle(name, parent=base[parent], **kw)
        return s

    styles = {}

    styles['cover_title'] = P('cover_title',
        fontSize=32, leading=38, textColor=C_GOLD,
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6)

    styles['cover_sub'] = P('cover_sub',
        fontSize=13, leading=18, textColor=C_MUTED,
        fontName='Helvetica', alignment=TA_CENTER, spaceAfter=4)

    styles['cover_version'] = P('cover_version',
        fontSize=10, leading=14, textColor=C_BLUE,
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)

    styles['toc_entry'] = P('toc_entry',
        fontSize=11, leading=16, textColor=C_TEXT,
        fontName='Helvetica', leftIndent=8, spaceAfter=2)

    styles['toc_sub'] = P('toc_sub',
        fontSize=9.5, leading=14, textColor=C_MUTED,
        fontName='Helvetica', leftIndent=20, spaceAfter=1)

    styles['ch_num'] = P('ch_num',
        fontSize=9, leading=12, textColor=C_GOLD,
        fontName='Helvetica-Bold', spaceAfter=0)

    styles['ch_title'] = P('ch_title',
        fontSize=20, leading=24, textColor=C_GOLD,
        fontName='Helvetica-Bold', spaceAfter=4)

    styles['ch_sub'] = P('ch_sub',
        fontSize=11, leading=16, textColor=C_MUTED,
        fontName='Helvetica', spaceAfter=8)

    styles['section'] = P('section',
        fontSize=13, leading=17, textColor=C_BLUE,
        fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=4)

    styles['body'] = P('body',
        fontSize=10, leading=15, textColor=C_TEXT,
        fontName='Helvetica', spaceAfter=6)

    styles['bullet'] = P('bullet',
        fontSize=10, leading=14, textColor=C_TEXT,
        fontName='Helvetica', leftIndent=14, spaceAfter=3,
        bulletText='•', bulletIndent=4, bulletFontSize=10,
        bulletColor=C_GOLD)

    styles['sub_bullet'] = P('sub_bullet',
        fontSize=9.5, leading=13, textColor=C_MUTED,
        fontName='Helvetica', leftIndent=28, spaceAfter=2,
        bulletText='–', bulletIndent=18)

    styles['tip'] = P('tip',
        fontSize=9.5, leading=14, textColor=C_GREEN,
        fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4)

    styles['warn'] = P('warn',
        fontSize=9.5, leading=14, textColor=C_ORANGE,
        fontName='Helvetica-Oblique', leftIndent=12, spaceAfter=4)

    styles['code'] = P('code',
        fontSize=8.5, leading=13, textColor=C_BLUE,
        fontName='Courier', leftIndent=14, spaceAfter=4,
        backColor=C_ACCENT)

    styles['label'] = P('label',
        fontSize=8, leading=11, textColor=C_MUTED,
        fontName='Helvetica-Bold', spaceAfter=2,
        textTransform='uppercase', letterSpacing=0.5)

    styles['caption'] = P('caption',
        fontSize=8.5, leading=12, textColor=C_MUTED,
        fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4)

    return styles

S = make_styles()

# ── Helpers ──────────────────────────────────────────────────────────────────
def sp(pts=6):
    return Spacer(1, pts)

def hr(clr=C_BORDER, thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness, color=clr, spaceAfter=6, spaceBefore=4)

def body(text):
    return Paragraph(text, S['body'])

def section(text):
    return Paragraph(text, S['section'])

def bullet(text):
    return Paragraph(text, S['bullet'])

def sub_bullet(text):
    return Paragraph(text, S['sub_bullet'])

def tip(text):
    return Paragraph(f'💡 {text}', S['tip'])

def warn(text):
    return Paragraph(f'⚠ {text}', S['warn'])

def label(text):
    return Paragraph(text, S['label'])

def code(text):
    return Paragraph(text, S['code'])

def chapter_header(num, title, subtitle=''):
    items = [
        Paragraph(f'CHAPTER {num}', S['ch_num']),
        Paragraph(title, S['ch_title']),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, S['ch_sub']))
    items.append(hr(C_GOLD, 1))
    items.append(sp(4))
    return items

def info_table(rows, col_widths=None):
    """rows = list of (label, value) tuples"""
    data = [[Paragraph(f'<b>{r[0]}</b>', S['label']),
             Paragraph(str(r[1]), S['body'])] for r in rows]
    w = col_widths or [45*mm, 115*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), C_ACCENT),
        ('GRID',       (0,0),(-1,-1), 0.4, C_BORDER),
        ('VALIGN',     (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TEXTCOLOR', (0,0),(0,-1), C_GOLD),
    ]))
    return [t, sp(8)]

def col_table(headers, rows, col_widths=None):
    """Generic column table"""
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = [[Paragraph(str(c), S['body']) for c in r] for r in rows]
    data = [head_row] + body_rows
    n = len(headers)
    w = col_widths or [(160/n)*mm]*n
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), C_PANEL),
        ('BACKGROUND', (0,1),(-1,-1), C_ACCENT),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_ACCENT, C_BG]),
        ('GRID',       (0,0),(-1,-1), 0.4, C_BORDER),
        ('TEXTCOLOR', (0,0),(-1,0), C_GOLD),
        ('VALIGN',    (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',(0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
    ]))
    return [t, sp(8)]

def badge_row(items):
    """Render a list of (text, color_hex) as colored badge table"""
    cells = [Paragraph(
        f'<font color="{c}"><b>{t}</b></font>', S['body']
    ) for t, c in items]
    t = Table([cells], colWidths=[38*mm]*len(items))
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), C_ACCENT),
        ('GRID',(0,0),(-1,-1), 0.5, C_BORDER),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    return [t, sp(6)]

# ── Page callbacks ────────────────────────────────────────────────────────────
_page_num = [0]

def on_page(canvas, doc):
    _page_num[0] = doc.page
    canvas.saveState()
    # top stripe
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H - 12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H - 7*mm, 'VFX BUDGET SYSTEM v04')
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W - 15*mm, H - 7*mm, 'PRODUCTION TUTORIAL')
    # bottom stripe
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 3.5*mm, 'VFX Budget System — Internal Documentation')
    canvas.drawRightString(W - 15*mm, 3.5*mm, f'Page {doc.page}')
    canvas.restoreState()

def on_cover_page(canvas, doc):
    canvas.saveState()
    # Full dark background
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Gold top bar
    canvas.setFillColor(C_GOLD)
    canvas.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BG)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(W/2, H - 11*mm, 'VFX BUDGET SYSTEM  —  PRODUCTION TUTORIAL')
    # Bottom bar
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawCentredString(W/2, 5*mm, 'CONFIDENTIAL — INTERNAL USE ONLY')
    canvas.restoreState()

# ── Content builders ──────────────────────────────────────────────────────────

def cover_page():
    elems = []
    elems.append(sp(50))
    elems.append(Paragraph('VFX BUDGET SYSTEM', S['cover_title']))
    elems.append(sp(4))
    elems.append(Paragraph('Complete Production Tutorial', S['cover_sub']))
    elems.append(sp(2))
    elems.append(Paragraph('Version 04', S['cover_version']))
    elems.append(sp(20))
    elems.append(hr(C_GOLD, 1.5))
    elems.append(sp(10))

    overview = [
        ['PAGES', '11 Chapters · 10 System Pages'],
        ['STACK', 'Flask · SQLite · Tabulator · Bootstrap 5'],
        ['AI',    'Ollama LLM Integration (streaming)'],
        ['SCOPE', 'Episodes · Shots · Assets · Bids · Invoices · Notes'],
    ]
    for k, v in overview:
        elems.append(Paragraph(
            f'<font color="#f0b429"><b>{k}&nbsp;&nbsp;</b></font>'
            f'<font color="#7880a0">{v}</font>',
            S['cover_sub']
        ))
        elems.append(sp(2))

    elems.append(sp(30))
    elems.append(Paragraph('INTERNAL DOCUMENTATION', S['cover_version']))
    elems.append(PageBreak())
    return elems

def toc():
    elems = []
    elems.append(Paragraph('TABLE OF CONTENTS', S['ch_title']))
    elems.append(hr(C_GOLD, 1))
    elems.append(sp(6))

    chapters = [
        ('1',  'Getting Started',           ['Installation & launch', 'Project setup', 'Navigation']),
        ('2',  'Distribution Page',         ['Summary cards', 'EFC table', 'Risk badges', 'Export']),
        ('3',  'Episode Pages (EP)',         ['Shot table', 'Inline editing', 'Complexity', 'Forecast calculator', 'AI tools']),
        ('4',  'Assets Page',               ['Asset log', 'AI description generator', 'Vendor award']),
        ('5',  'VFX Notes',                 ['Adding & resolving notes', 'Filters', 'AI summarize']),
        ('6',  'Bid Compare',               ['Importing Excel', 'Vendor confidence badges', 'Awarding shots']),
        ('7',  'Vendor Tracker',            ['Invoice rows', 'Paid vs pending', 'Sync to Invoice Log']),
        ('8',  'Invoice Log',               ['Vendor Registry', 'Invoice Log', 'Vendor Summary', 'Capacity Tracker']),
        ('9',  'Scenario Planner',          ['Budget scenarios', 'What-if modeling']),
        ('10', 'Settings',                  ['Project config', 'Episode range', 'LLM model']),
        ('11', 'Cross-Page Data Flow',      ['How pages share data', 'API endpoints overview']),
    ]

    for num, title, subs in chapters:
        elems.append(Paragraph(
            f'<font color="#f0b429"><b>{num}.</b></font>  <b>{title}</b>',
            S['toc_entry']
        ))
        for s in subs:
            elems.append(Paragraph(f'› {s}', S['toc_sub']))
        elems.append(sp(3))

    elems.append(PageBreak())
    return elems

def ch1_getting_started():
    elems = []
    elems += chapter_header('1', 'Getting Started', 'Installation, project setup, and navigation')

    elems.append(section('System Requirements'))
    elems += info_table([
        ('Python', '3.9 or later'),
        ('Packages', 'flask, openpyxl, requests (install via pip)'),
        ('Browser', 'Chrome or Edge recommended (Tabulator renders best)'),
        ('LLM (optional)', 'Ollama running locally on port 11434 for AI features'),
    ])

    elems.append(section('Launching the Application'))
    elems.append(body('Double-click <b>START.bat</b> inside the UPDATE-SISTEM04 folder. '
                       'A terminal window will open and Flask starts on <b>http://127.0.0.1:5000</b>.'))
    elems.append(code('START.bat  →  runs:  python app.py'))
    elems.append(tip('If port 5000 is already in use, edit START.bat and change the port number.'))

    elems.append(section('Creating a Project'))
    elems.append(body('On first launch you will see the <b>Projects</b> screen. Click <b>New Project</b> and fill in:'))
    elems += col_table(
        ['Field', 'Description', 'Example'],
        [
            ['Project Name',   'Show / film title',              'ANDOR S2'],
            ['Season',         'Season label (optional)',         'S2'],
            ['Episode Start',  'First episode number',           '201'],
            ['Episode End',    'Last episode number',            '208'],
        ],
        col_widths=[38*mm, 72*mm, 48*mm]
    )
    elems.append(body('Click <b>Open</b> next to an existing project to load it. '
                       'All data is stored per-project in a SQLite .db file inside the <b>projects/</b> folder.'))

    elems.append(section('Navigation Bar'))
    elems.append(body('The top navigation bar is always visible. Tabs from left to right:'))
    nav_items = [
        ('DISTRIBUTION', 'Season-wide EFC summary, risk view, export'),
        ('ASSETS',       'VFX asset master list with vendor awards'),
        ('EPISODES',     'Dropdown: jump to any episode shot table'),
        ('VFX NOTES',    'Production notes & action items'),
        ('BID COMPARE',  'Multi-vendor bid grid imported from Excel'),
        ('VENDOR TRACKER','Invoice rows, paid vs pending tracking'),
        ('INVOICE LOG',  'Registry, formal invoices, vendor summary'),
        ('SCENARIO',     'Budget scenario / what-if planner'),
        ('SETTINGS',     'Project config, episode range, LLM model'),
    ]
    for name, desc in nav_items:
        elems.append(Paragraph(
            f'<font color="#f0b429"><b>{name}</b></font>  — {desc}',
            S['bullet']
        ))
    elems.append(sp(6))

    elems.append(section('Global Search  (Ctrl + K)'))
    elems.append(body('Press <b>Ctrl+K</b> anywhere to open the search modal. '
                       'Type at least 2 characters to search across shots, assets, and notes simultaneously. '
                       'Click any result to jump to that page.'))

    elems.append(PageBreak())
    return elems

def ch2_distribution():
    elems = []
    elems += chapter_header('2', 'Distribution Page', 'Season-wide EFC summary, risk scores, and export')

    elems.append(body('The Distribution page is the <b>command centre</b> for the season. '
                       'It aggregates totals from all episode pages and assets automatically.'))

    elems.append(section('Summary Cards'))
    elems.append(body('Four stat cards appear at the top:'))
    elems += col_table(
        ['Card', 'What it Shows'],
        [
            ['Total Est. Shots',     'Number of VFX shots across all episodes'],
            ['Total EST Budget',     'Sum of cost estimates (shots + assets)'],
            ['Total EFC Budget',     'Sum of EFCs (Estimated Final Cost) — live spend forecast'],
            ['Total Variance',       'EST minus EFC; negative = over budget'],
        ],
        col_widths=[55*mm, 105*mm]
    )

    elems.append(section('EFC Summary Table — Per Episode'))
    elems.append(body('One row per episode. Columns:'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['EP',          'Episode number, links to that episode\'s shot page'],
            ['SHOTS',       'Count of non-omitted VFX shots'],
            ['EST (Shot)',   'Total cost estimate from shot rows'],
            ['EFC (Shot)',   'Total EFC from shot rows'],
            ['EST (Asset)',  'Total cost estimate from linked assets'],
            ['EFC (Asset)',  'Total EFC from linked assets'],
            ['COMBINED EST','Shot EST + Asset EST'],
            ['COMBINED EFC','Shot EFC + Asset EFC'],
            ['VARIANCE',    'Combined EST − Combined EFC'],
            ['RISK',        'Delivery risk badge (SAFE / WATCH / AT RISK / HIGH RISK)'],
            ['✨',           'Generate an AI producer narrative memo for this episode'],
        ],
        col_widths=[38*mm, 122*mm]
    )

    elems.append(section('Delivery Risk Score'))
    elems.append(body('Each episode receives a risk score computed as:'))
    elems.append(code('Risk = 0.55 × Complexity Risk  +  0.45 × Budget Variance Risk'))
    elems.append(body('<b>Complexity Risk</b> = fraction of shots that are heavy types '
                       '(CG, CREATURE, CROWD, FX, EXTENSION) or tagged HERO/HIGH complexity. '
                       '<b>Budget Variance Risk</b> = how far EFC exceeds EST, clamped 0–1.'))
    elems += badge_row([
        ('SAFE',      '#52c46a'),
        ('WATCH',     '#f0b429'),
        ('AT RISK',   '#e08232'),
        ('HIGH RISK', '#e05252'),
    ])
    elems.append(body('Thresholds: SAFE < 0.20 · WATCH < 0.45 · AT RISK < 0.70 · HIGH RISK ≥ 0.70'))

    elems.append(section('AI Episode Narrative  (✨ button)'))
    elems.append(body('Click the ✨ button in any episode row to generate a concise producer memo. '
                       'The AI receives shots count, budget figures, risk label, and variance, then '
                       'streams a narrative summary. Use <b>Copy</b> to paste into your production report.'))
    elems.append(tip('Requires Ollama running locally. Configure the model in Settings → LLM.'))

    elems.append(section('Export'))
    elems += info_table([
        ('Export CSV',   'Downloads the on-screen EFC table as a .csv file'),
        ('Export Excel', 'Downloads a formatted .xlsx with all episode data'),
        ('Refresh',      'Re-fetches all data from the database without reloading the page'),
    ])

    elems.append(PageBreak())
    return elems

def ch3_episode():
    elems = []
    elems += chapter_header('3', 'Episode Pages', 'Shot tracking, inline editing, complexity tiers, and AI')

    elems.append(body('Each episode has its own page accessible via the <b>EPISODES</b> dropdown. '
                       'This is where individual VFX shots are entered, edited, and tracked.'))

    elems.append(section('Shot Table'))
    elems.append(body('The table lists every VFX shot for the episode. All cells are inline-editable — '
                       'click any cell to edit. Changes are saved automatically to the database.'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['SC',         'Scene code (e.g. 12A)'],
            ['LOCATION',   'Set / location description'],
            ['D/N',        'Day or Night'],
            ['INT/EXT',    'Interior or Exterior'],
            ['SHOT TYPE',  'CG, COMP, FX, CREATURE, EXTENSION, PLATE, etc.'],
            ['COMPLEXITY', 'Low / Medium / High / Hero — color-coded tier'],
            ['VFX DESC',   'Short description of the VFX work'],
            ['ASSET',      'Linked asset name from the Assets page'],
            ['VENDOR',     'Awarded vendor'],
            ['COST EST',   'Initial cost estimate in project currency'],
            ['EFC',        'Estimated Final Cost (current spend forecast)'],
            ['STATUS',     'In Progress / Review / Approved / Delivered / Omit'],
            ['OMIT',       'Toggle to exclude shot from totals'],
            ['✨',          'AI shot description generator'],
        ],
        col_widths=[30*mm, 130*mm]
    )

    elems.append(section('Complexity Tiers'))
    elems.append(body('The COMPLEXITY column has four tiers used for budgeting and risk scoring:'))
    elems += badge_row([
        ('LOW',    '#52c46a'),
        ('MEDIUM', '#f0b429'),
        ('HIGH',   '#e08232'),
        ('HERO',   '#e05252'),
    ])
    elems.append(body('Hero shots are rare, highly complex VFX (full CG environments, creature performances, etc.) '
                       'and carry a 5× cost multiplier in the Forecast Calculator.'))

    elems.append(section('Adding and Deleting Shots'))
    elems += info_table([
        ('Add Shot',    'Click the green  + Add Shot  button. A new row appears at the bottom.'),
        ('Delete Shot', 'Click the red trash icon at the end of any row.'),
        ('Import Excel','Click  Import Excel  to bulk-upload shots from a formatted .xlsx file.'),
        ('Export Excel','Click  Export Excel  to download all shots for this episode.'),
    ])

    elems.append(section('Shot Complexity Forecast Calculator'))
    elems.append(body('The panel on the right side of the page calculates a budget forecast '
                       'based on shot count and complexity distribution. Enter:'))
    elems += col_table(
        ['Field', 'Default Multiplier', 'Description'],
        [
            ['Simple',  '1.0×', 'Baseline simple VFX shot'],
            ['Medium',  '2.0×', 'Intermediate VFX work'],
            ['Heavy',   '3.5×', 'Complex, multi-layer VFX'],
            ['Hero',    '5.0×', 'Flagship/hero VFX shots'],
        ],
        col_widths=[35*mm, 40*mm, 83*mm]
    )
    elems.append(body('Enter the expected % of shots in each tier and a base shot rate. '
                       'The calculator outputs a weighted total budget forecast.'))

    elems.append(section('AI Shot Description  (✨ button)'))
    elems.append(body('Click ✨ in any shot row to open the AI Description modal. '
                       'The AI reads the shot\'s location, type, and VFX description and generates '
                       'a polished one-line description suitable for vendor briefs. '
                       'Click <b>Accept</b> to save it directly to the VFX DESC field, or <b>Discard</b> to cancel.'))

    elems.append(PageBreak())
    return elems

def ch4_assets():
    elems = []
    elems += chapter_header('4', 'Assets Page', 'VFX asset master list and vendor awards')

    elems.append(body('The Assets page is the master list of all VFX assets for the season — '
                       'CG characters, environments, props, and rigs. Assets link to shots in episode pages '
                       'and roll up into the Distribution cost totals.'))

    elems.append(section('Asset Table Columns'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['EP',          'Episode the asset first appears in'],
            ['SC',          'Scene code'],
            ['ASSET NAME',  'Short identifier used to link from shot rows'],
            ['ASSET TYPE',  'Character / Environment / Prop / Rig / Plate / Other'],
            ['DESCRIPTION', 'Detailed asset description (can be AI-generated)'],
            ['VENDOR',      'Vendor awarded this asset'],
            ['COST EST',    'Estimated cost for this asset build'],
            ['EFC',         'Current spend forecast'],
            ['STATUS',      'Not Started / In Progress / Complete'],
            ['AWARD',       'Checkbox — mark asset as formally awarded to vendor'],
            ['✨',           'AI description generator'],
        ],
        col_widths=[30*mm, 130*mm]
    )

    elems.append(section('Adding Assets'))
    elems.append(body('Click <b>+ Add Asset</b> to insert a new row. '
                       'Fill in the asset name — this name must exactly match what you type in the '
                       '<b>ASSET</b> column of shot rows to link them together.'))
    elems.append(tip('Asset names are case-insensitive when linking. Use short, consistent names '
                      'like "CG_DRAGON" or "ENV_PALACE" for clarity.'))

    elems.append(section('AI Asset Description  (✨ button)'))
    elems.append(body('Click ✨ in any asset row to open the AI Description modal. '
                       'The AI uses the asset name, type, and existing description to generate '
                       'a detailed production-ready description. '
                       'Click <b>Accept & Save</b> to write it directly to the DESCRIPTION field.'))

    elems.append(section('Importing Assets from Excel'))
    elems.append(body('Click <b>Import Excel</b> to bulk-upload assets from a .xlsx file. '
                       'The file must have a header row with columns matching the field names above. '
                       'Choose <b>Append</b> to add to existing data or <b>Replace</b> to clear first.'))

    elems.append(PageBreak())
    return elems

def ch5_notes():
    elems = []
    elems += chapter_header('5', 'VFX Notes', 'Production notes, action items, and AI summarization')

    elems.append(body('The VFX Notes page is a shared log for production notes, VFX supervisor feedback, '
                       'client comments, and action items across all episodes.'))

    elems.append(section('Notes Table Columns'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['#',          'Auto-incrementing item number'],
            ['DATE',       'Date the note was entered'],
            ['EP',         'Episode the note relates to'],
            ['AUTHOR',     'Name of the person who added the note'],
            ['NOTE',       'Full note text — inline editable'],
            ['STATUS',     'Open / In Progress / Resolved'],
            ['PRIORITY',   'Low / Medium / High / Critical'],
        ],
        col_widths=[22*mm, 138*mm]
    )

    elems.append(section('Adding Notes'))
    elems.append(body('Click <b>+ Add Note</b> in the toolbar. A new row is inserted. '
                       'Type directly into the NOTE cell. All changes save automatically.'))

    elems.append(section('Filtering Notes'))
    elems += info_table([
        ('EP Filter',     'Show notes for a specific episode only'),
        ('Status Filter', 'Show only Open, In Progress, or Resolved notes'),
        ('Priority',      'Filter by priority level'),
    ])

    elems.append(section('Resolving Notes'))
    elems.append(body('Change the STATUS cell to <b>Resolved</b> to mark a note as complete. '
                       'Resolved notes are dimmed in the table and excluded from the AI summary.'))

    elems.append(section('AI Summarize  (✨ Summarize button)'))
    elems.append(body('Click <b>✨ Summarize</b> in the toolbar to generate an AI summary of all '
                       '<b>open and in-progress</b> notes. The AI groups them by theme and lists '
                       'key action items. Use this to prepare a concise briefing for producers or supervisors.'))
    elems.append(tip('Only non-resolved notes are included in the AI summary. Resolve completed items '
                      'to keep the summary focused on current issues.'))

    elems.append(PageBreak())
    return elems

def ch6_bidcompare():
    elems = []
    elems += chapter_header('6', 'Bid Compare', 'Multi-vendor bidding grid with confidence scoring')

    elems.append(body('The Bid Compare page is your vendor bid evaluation tool. '
                       'Import bids from Excel and compare quotes from multiple vendors side by side, '
                       'with AI-powered confidence scoring based on bid history.'))

    elems.append(section('Importing a BIDCOMPARE Excel File'))
    elems.append(body('Click <b>Import BIDCOMPARE Excel</b>. The Excel file must follow this column structure:'))
    elems += col_table(
        ['Column', 'Required?', 'Description'],
        [
            ['EP',         'Yes', 'Episode number'],
            ['SC',         'Yes', 'Scene code'],
            ['SETTING',    'No',  'Location / setting description'],
            ['VFX TYPE',   'No',  'Type of VFX work'],
            ['VER',        'No',  'Bid version number'],
            ['LOCK $',     'No',  'Locked budget amount'],
            ['EFC',        'No',  'Estimated final cost'],
            ['<VendorName>','Yes','One column per vendor; column header = vendor name'],
        ],
        col_widths=[32*mm, 22*mm, 106*mm]
    )
    elems.append(body('Import modes:'))
    elems.append(bullet('<b>Replace</b> — clears existing data for the selected EP first (or all EPs if none selected)'))
    elems.append(bullet('<b>Append</b> — adds new rows without deleting existing data'))

    elems.append(section('Reading the Bid Grid'))
    elems.append(body('Each vendor becomes a column. Bid amounts are shown per shot row. '
                       'An awarded bid is highlighted in <font color="#52c46a"><b>green</b></font>.'))
    elems.append(body('To award a shot to a vendor, click the <b>AWARD</b> cell and type the vendor name. '
                       'Multiple vendors can be awarded with comma separation: <b>ILM, DNEG</b>'))

    elems.append(section('Vendor Confidence Badges'))
    elems.append(body('Each vendor column header shows a confidence badge computed from bid history:'))
    elems += col_table(
        ['Badge', 'Score', 'Meaning'],
        [
            ['HIGH  (green)',  '≥ 0.70', 'Consistent bidding, reliable estimate history'],
            ['MED   (yellow)', '≥ 0.40', 'Some variability, moderate reliability'],
            ['LOW   (red)',    '< 0.40', 'High variance or very few data points'],
        ],
        col_widths=[38*mm, 25*mm, 97*mm]
    )
    elems.append(body('Formula: <b>Confidence = min(samples/30, 1.0) × max(0, 1 − CV)</b> '
                       'where CV is the coefficient of variation across the vendor\'s historical bids.'))
    elems.append(tip('The more bids you import over time, the more accurate confidence scores become.'))

    elems.append(section('Filters'))
    elems += info_table([
        ('EP Filter',       'Show bids for a single episode'),
        ('Version Filter',  'Show a specific bid version only'),
        ('Show No-VFX',     'Toggle to include or hide shots with no VFX'),
    ])

    elems.append(section('Summary Stats'))
    elems.append(body('The stats bar above the grid shows: Shots count · Lock Budget total · EFC total · Awarded count'))

    elems.append(PageBreak())
    return elems

def ch7_vendor_tracker():
    elems = []
    elems += chapter_header('7', 'Vendor Tracker', 'Invoice rows, paid vs pending, and vendor status')

    elems.append(body('The Vendor Tracker is a lightweight invoice tracking table — '
                       'one row per vendor per episode. It tracks contracted amounts, what has been paid, '
                       'and what remains pending.'))

    elems.append(section('Tracker Table Columns'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['EP',          'Episode number'],
            ['VENDOR',      'Vendor / VFX house name'],
            ['CONTRACT $',  'Agreed total contract value'],
            ['INVOICED $',  'Total invoiced to date'],
            ['PAID $',      'Amount paid so far'],
            ['PENDING $',   'Invoiced minus Paid (auto-calculated)'],
            ['STATUS',      'Active / On Hold / Complete / Cancelled'],
            ['NOTES',       'Free-text notes for this vendor-episode row'],
        ],
        col_widths=[30*mm, 130*mm]
    )

    elems.append(section('Adding Vendor Rows'))
    elems.append(body('Click <b>+ Add Row</b>. Select the vendor and episode, then fill in financial fields. '
                       'All cells are inline-editable and save on change.'))

    elems.append(section('Link to Invoice Log'))
    elems.append(body('The Vendor Tracker header contains an <b>Invoice Log</b> shortcut button. '
                       'Click it to jump directly to the Invoice Log page where formal invoices '
                       'with invoice numbers, dates, and approval workflow are managed.'))
    elems.append(tip('Keep Vendor Tracker for quick episode-level totals. '
                      'Use Invoice Log for formal document-level tracking.'))

    elems.append(section('Exporting'))
    elems.append(body('Click <b>Export CSV</b> or <b>Export Excel</b> to download the full tracker.'))

    elems.append(PageBreak())
    return elems

def ch8_invoice_log():
    elems = []
    elems += chapter_header('8', 'Invoice Log', 'Vendor registry, formal invoices, and financial summary')

    elems.append(body('The Invoice Log is the formal financial ledger of the system. '
                       'It has four sections: Vendor Registry, Invoice Log, Vendor Summary, and Capacity Tracker.'))

    elems.append(section('Section A — Vendor Registry'))
    elems.append(body('The registry holds master vendor information used across the system:'))
    elems += col_table(
        ['Field', 'Description'],
        [
            ['VENDOR',    'Vendor name — must be unique'],
            ['REGION',    'Geographic region (e.g. UK, US, CA, IN)'],
            ['FX RATE',   'Currency exchange rate (1.0 = same currency as project)'],
            ['TAX %',     'Applicable tax percentage for this vendor'],
            ['REBATE %',  'Any rebate or tax credit the vendor qualifies for'],
            ['CONTACT',   'Primary contact name or email'],
        ],
        col_widths=[28*mm, 132*mm]
    )
    elems.append(body('<b>Sync from System</b> button: automatically scans Vendor Tracker, Assets, '
                       'and Bid Compare and adds any vendor names found there into the registry. '
                       'Existing entries are not overwritten.'))

    elems.append(section('Section B — Invoice Log'))
    elems.append(body('One row per invoice document. Columns:'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['VENDOR',       'Must match a vendor in the Registry (dropdown)'],
            ['EP',           'Episode this invoice relates to'],
            ['INV #',        'Invoice number from the vendor'],
            ['DATE',         'Invoice date'],
            ['AMOUNT',       'Invoice amount in vendor\'s currency'],
            ['NET $',        'Auto-calculated: Amount × FX Rate + Tax − Rebate'],
            ['STATUS',       'Pending / Approved / Paid'],
            ['APPROVE DATE', 'Date the invoice was approved for payment'],
            ['NOTES',        'Any additional notes'],
        ],
        col_widths=[30*mm, 130*mm]
    )
    elems.append(body('Filters available: by Vendor · by Episode · by Status'))

    elems.append(section('Section C — Vendor Summary'))
    elems.append(body('A live rollup table showing per-vendor totals computed from the invoice log:'))
    elems.append(bullet('Total Invoiced'))
    elems.append(bullet('Total Paid'))
    elems.append(bullet('Pending / Approved (not yet paid)'))
    elems.append(bullet('Net after rebate'))
    elems.append(bullet('Confidence badge (sourced from Bid Compare history)'))

    elems.append(section('Section D — Capacity Tracker'))
    elems.append(body('Tracks each vendor\'s estimated delivery capacity:'))
    elems += col_table(
        ['Field', 'Description'],
        [
            ['VENDOR',           'Vendor name'],
            ['SHOTS / MONTH',    'Estimated shot output per month'],
            ['EFFICIENCY %',     'Adjustment factor (e.g. 95% = slight buffer)'],
            ['EFFECTIVE CAP',    'Shots/Month × Efficiency % — computed automatically'],
        ],
        col_widths=[35*mm, 40*mm, 85*mm]
    )
    elems.append(tip('Use Capacity Tracker to check if an awarded vendor can realistically '
                      'deliver their shot count within the schedule.'))

    elems.append(PageBreak())
    return elems

def ch9_scenario():
    elems = []
    elems += chapter_header('9', 'Scenario Planner', 'Budget scenarios and what-if modeling')

    elems.append(body('The Scenario Planner lets you model different budget outcomes by '
                       'adjusting assumptions without changing live shot data.'))

    elems.append(section('Creating a Scenario'))
    elems.append(body('Click <b>+ New Scenario</b> and give it a name (e.g. "Optimistic", "Worst Case"). '
                       'Each scenario stores:'))
    elems.append(bullet('A global cost multiplier (e.g. 1.15 = 15% contingency)'))
    elems.append(bullet('Per-episode overrides for EFC or shot count'))
    elems.append(bullet('Free-text notes describing the scenario assumptions'))

    elems.append(section('Comparing Scenarios'))
    elems.append(body('The scenario comparison table shows all scenarios side by side with '
                       'total EST, EFC, and variance for each. Use this for exec presentations '
                       'and budget approval decks.'))

    elems.append(section('Locking a Scenario'))
    elems.append(body('Click <b>Lock</b> on a scenario to mark it as the approved baseline. '
                       'Locked scenarios cannot be edited and appear with a lock icon. '
                       'The Distribution page LOCK $ column is sourced from the locked scenario.'))

    elems.append(PageBreak())
    return elems

def ch10_settings():
    elems = []
    elems += chapter_header('10', 'Settings', 'Project configuration and LLM setup')

    elems.append(section('Project Settings'))
    elems += info_table([
        ('Project Name',   'Display name shown in the navbar'),
        ('Season',         'Season label (e.g. S1, S2)'),
        ('Episode Start',  'First episode number — sets range for all dropdowns and tables'),
        ('Episode End',    'Last episode number'),
        ('Currency',       'Display currency symbol (cosmetic only, no conversion)'),
    ])

    elems.append(section('LLM / AI Settings'))
    elems += info_table([
        ('Ollama URL',   'Base URL of your local Ollama instance (default: http://localhost:11434)'),
        ('Model',        'Model name to use for generation (e.g. llama3, mistral, gemma2)'),
        ('Temperature',  'Controls creativity — 0.2 for factual, 0.8 for more creative output'),
        ('Max Tokens',   'Maximum length of AI-generated text'),
    ])
    elems.append(tip('Test your LLM connection with the  Test Connection  button after saving settings. '
                      'A green check means Ollama is reachable and the model is loaded.'))

    elems.append(section('Database'))
    elems.append(body('Each project stores its data in a separate SQLite database file in the '
                       '<b>projects/</b> directory. You can:'))
    elems.append(bullet('Back up a project by copying its .db file'))
    elems.append(bullet('Restore by placing the .db file back in projects/ and opening it'))
    elems.append(bullet('Delete a project from the Projects home screen'))
    elems.append(warn('Deleting a project is permanent. Always back up the .db file first.'))

    elems.append(PageBreak())
    return elems

def ch11_data_flow():
    elems = []
    elems += chapter_header('11', 'Cross-Page Data Flow', 'How pages share data and key API endpoints')

    elems.append(body('All pages share a single SQLite database per project. Data entered on one page '
                       'is immediately visible on other pages. Here is a map of key data flows:'))

    elems.append(section('Data Connections Map'))
    elems += col_table(
        ['Source Page', 'Data Provided', 'Consumed By'],
        [
            ['Episode Pages',    'Shot counts, COST EST, EFC, COMPLEXITY',   'Distribution (risk + totals)'],
            ['Assets Page',      'Asset EST, EFC, vendor awards',             'Distribution (asset totals)'],
            ['Bid Compare',      'Vendor bid history, awarded vendors',       'Invoice Log (confidence badges), Vendor Registry sync'],
            ['Vendor Tracker',   'Vendor names, paid/pending',                'Invoice Log (Sync from System)'],
            ['Vendor Registry',  'FX rate, tax %, rebate %',                 'Invoice Log (NET calculation)'],
            ['Invoice Log',      'Paid/pending totals per vendor',            'Vendor Summary section'],
        ],
        col_widths=[35*mm, 60*mm, 65*mm]
    )

    elems.append(section('Key API Endpoints'))
    elems += col_table(
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/distribution',        'GET',    'Per-EP EFC + risk scores'],
            ['/api/shots/<ep>',          'GET',    'All shots for an episode'],
            ['/api/shots/<id>',          'PUT',    'Update a single shot field'],
            ['/api/assets',              'GET/POST','List or create assets'],
            ['/api/assets/<id>',         'PUT/DEL','Update or delete an asset'],
            ['/api/bidcompare',          'GET',    'All bid rows (with novfx filter)'],
            ['/api/bidcompare/import',   'POST',   'Import Excel bid file'],
            ['/api/bidcompare/vendors',  'GET',    'Distinct vendor list from bids'],
            ['/api/vendor_confidence',   'GET',    'Confidence scores per vendor'],
            ['/api/vendors/all',         'GET',    'All vendors from all sources'],
            ['/api/vendor_registry',     'GET/POST','Registry CRUD'],
            ['/api/invoicelog',          'GET/POST','Invoice log CRUD'],
            ['/api/notes',               'GET/POST','Notes CRUD'],
            ['/api/search',              'GET',    'Cross-entity search (q= param)'],
            ['/api/llm/stream',          'POST',   'SSE streaming LLM endpoint'],
        ],
        col_widths=[55*mm, 20*mm, 85*mm]
    )

    elems.append(section('Vendor Sync Flow'))
    elems.append(body('The <b>Sync from System</b> button in Invoice Log → Vendor Registry calls '
                       '<b>/api/vendors/all</b>, which queries four sources and deduplicates by uppercase name:'))
    elems.append(bullet('vendor_tracker table  (vendor column)'))
    elems.append(bullet('assets table  (award_vendor column)'))
    elems.append(bullet('bid_compare table  (award column — splits comma-separated awards)'))
    elems.append(bullet('vendor_registry table  (already registered vendors)'))
    elems.append(body('Any new vendor found is automatically added to the registry with default values '
                       '(FX rate 1.0, tax 0%, rebate 0%). Edit registry rows to add region and financial details.'))

    elems.append(section('AI / LLM Flow'))
    elems.append(body('All AI features stream through a single endpoint: <b>/api/llm/stream</b>. '
                       'The frontend sends a JSON body with a <b>task</b> key and context data. '
                       'The server builds a prompt, calls Ollama, and streams the response back as '
                       'Server-Sent Events (SSE). The frontend renders tokens as they arrive.'))
    elems += col_table(
        ['Task Key', 'Used In', 'Context Sent'],
        [
            ['ep_narrative',  'Distribution ✨ button',    'EP, shots, EFC, EST, risk label'],
            ['shot_desc',     'Episode ✨ button',          'Scene code, location, shot type, current desc'],
            ['asset_desc',    'Assets ✨ button',           'Asset name, type, current description'],
            ['notes_summary', 'VFX Notes ✨ Summarize',    'All open/in-progress note texts'],
        ],
        col_widths=[35*mm, 45*mm, 80*mm]
    )

    elems.append(sp(10))
    elems.append(hr(C_GOLD, 1))
    elems.append(sp(6))
    elems.append(Paragraph(
        'End of Tutorial  —  VFX Budget System v04',
        S['cover_sub']
    ))
    elems.append(Paragraph(
        'For support or feature requests, contact your system administrator.',
        S['caption']
    ))

    return elems

# ── Main ──────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=20*mm,
        bottomMargin=18*mm,
    )

    story = []
    story += cover_page()
    story += toc()
    story += ch1_getting_started()
    story += ch2_distribution()
    story += ch3_episode()
    story += ch4_assets()
    story += ch5_notes()
    story += ch6_bidcompare()
    story += ch7_vendor_tracker()
    story += ch8_invoice_log()
    story += ch9_scenario()
    story += ch10_settings()
    story += ch11_data_flow()

    # First page uses cover callback (no header/footer)
    doc.build(
        story,
        onFirstPage=on_cover_page,
        onLaterPages=on_page,
    )
    print(f'\nPDF generated: {OUT}\n')

if __name__ == '__main__':
    build()
