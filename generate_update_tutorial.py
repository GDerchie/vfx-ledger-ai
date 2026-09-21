"""
VFX Budget System — UPDATE-SISTEM10 Feature Tutorial Generator
Run: python generate_update_tutorial.py
Output: VFX_Budget_System_Update_Tutorial.pdf

Covers all four improvement sprints:
  Week 1 — Delivery Risk Forecast Engine + Vendor Capacity Load
  Week 2 — LLM Cost Learning from Actuals
  Week 3 — Season Optimizer (new page)
  Week 4 — Invoice-to-Shot Linking + Vendor Performance Score
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

# ── Palette ───────────────────────────────────────────────────────────────────
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
C_PURPLE   = colors.HexColor('#9b59b6')

OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_Update_Tutorial.pdf')

W, H = A4

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def P(name, parent='Normal', **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    styles = {}

    styles['cover_title'] = P('cover_title',
        fontSize=30, leading=36, textColor=C_GOLD,
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

    styles['new'] = P('new',
        fontSize=9.5, leading=14, textColor=C_PURPLE,
        fontName='Helvetica-Bold', leftIndent=12, spaceAfter=4)

    styles['code'] = P('code',
        fontSize=8.5, leading=13, textColor=C_BLUE,
        fontName='Courier', leftIndent=14, spaceAfter=4,
        backColor=C_ACCENT)

    styles['label'] = P('label',
        fontSize=8, leading=11, textColor=C_MUTED,
        fontName='Helvetica-Bold', spaceAfter=2)

    styles['caption'] = P('caption',
        fontSize=8.5, leading=12, textColor=C_MUTED,
        fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=4)

    styles['week_badge'] = P('week_badge',
        fontSize=9, leading=12, textColor=C_BG,
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2)

    return styles


S = make_styles()

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    return Paragraph(f'TIP  {text}', S['tip'])

def warn(text):
    return Paragraph(f'NOTE  {text}', S['warn'])

def new_feature(text):
    return Paragraph(f'NEW  {text}', S['new'])

def label(text):
    return Paragraph(text, S['label'])

def code(text):
    return Paragraph(text, S['code'])

def chapter_header(num, title, subtitle='', week_label=None):
    items = [
        Paragraph(f'CHAPTER {num}', S['ch_num']),
        Paragraph(title, S['ch_title']),
    ]
    if week_label:
        # Colored sprint badge
        badge_data = [[Paragraph(week_label, S['week_badge'])]]
        t = Table(badge_data, colWidths=[50*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_GOLD),
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROUNDEDCORNERS', [3]),
        ]))
        items.append(sp(4))
        items.append(t)
        items.append(sp(4))
    if subtitle:
        items.append(Paragraph(subtitle, S['ch_sub']))
    items.append(hr(C_GOLD, 1))
    items.append(sp(4))
    return items

def info_table(rows, col_widths=None):
    data = [[Paragraph(f'<b>{r[0]}</b>', S['label']),
             Paragraph(str(r[1]), S['body'])] for r in rows]
    w = col_widths or [45*mm, 115*mm]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_ACCENT),
        ('GRID',       (0, 0), (-1, -1), 0.4, C_BORDER),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (0, 0), (0, -1), C_GOLD),
    ]))
    return [t, sp(8)]

def col_table(headers, rows, col_widths=None):
    head_row = [Paragraph(f'<b>{h}</b>', S['label']) for h in headers]
    body_rows = [[Paragraph(str(c), S['body']) for c in r] for r in rows]
    data = [head_row] + body_rows
    n = len(headers)
    w = col_widths or [(160 / n) * mm] * n
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PANEL),
        ('BACKGROUND', (0, 1), (-1, -1), C_ACCENT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_ACCENT, C_BG]),
        ('GRID',       (0, 0), (-1, -1), 0.4, C_BORDER),
        ('TEXTCOLOR',  (0, 0), (-1, 0), C_GOLD),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return [t, sp(8)]

def badge_row(items):
    cells = [Paragraph(
        f'<font color="{c}"><b>{t}</b></font>', S['body']
    ) for t, c in items]
    t = Table([cells], colWidths=[38 * mm] * len(items))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_ACCENT),
        ('GRID',       (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [t, sp(6)]

def sprint_summary_table(rows):
    """Sprint overview table: Sprint | Feature | Where"""
    return col_table(
        ['Sprint', 'Feature', 'Where to Find'],
        rows,
        col_widths=[22*mm, 70*mm, 68*mm]
    )

# ── Page callbacks ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, H - 12*mm, W, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(15*mm, H - 7*mm, 'VFX BUDGET SYSTEM — UPDATE TUTORIAL')
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W - 15*mm, H - 7*mm, 'UPDATE-SISTEM10  •  4 SPRINT FEATURES')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 3.5*mm, 'VFX Budget System — Internal Documentation')
    canvas.drawRightString(W - 15*mm, 3.5*mm, f'Page {doc.page}')
    canvas.restoreState()

def on_cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(C_GOLD)
    canvas.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BG)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(W / 2, H - 11*mm, 'VFX BUDGET SYSTEM  —  UPDATE TUTORIAL')
    canvas.setFillColor(C_PANEL)
    canvas.rect(0, 0, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawCentredString(W / 2, 5*mm, 'CONFIDENTIAL — INTERNAL USE ONLY')
    canvas.restoreState()

# ── Content builders ───────────────────────────────────────────────────────────

def cover_page():
    elems = []
    elems.append(sp(50))
    elems.append(Paragraph('VFX BUDGET SYSTEM', S['cover_title']))
    elems.append(sp(4))
    elems.append(Paragraph('Update Tutorial — New Features', S['cover_sub']))
    elems.append(sp(2))
    elems.append(Paragraph('UPDATE-SISTEM10', S['cover_version']))
    elems.append(sp(20))
    elems.append(hr(C_GOLD, 1.5))
    elems.append(sp(10))

    overview = [
        ['SPRINT 1', 'Delivery Risk Forecast Engine  +  Vendor Capacity Load'],
        ['SPRINT 2', 'LLM Cost Learning from Project Actuals'],
        ['SPRINT 3', 'Season Optimizer — new constraint-based assignment page'],
        ['SPRINT 4', 'Invoice-to-Shot Linking  +  Vendor Performance Score'],
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
        ('1', 'What\'s New — Overview',
         ['Sprint summary', 'Where each feature lives', 'Quick-start checklist']),
        ('2', 'Delivery Risk Forecast  (Sprint 1)',
         ['New risk formula (3-component)', 'Risk Forecast panel on Dashboard',
          'Predicted delay days', 'Sub-score breakdown table']),
        ('3', 'Vendor Capacity Load  (Sprint 1)',
         ['Capacity Tracker fields', 'Load panel on Vendor Tracker',
          'Utilization bars', 'API endpoint']),
        ('4', 'LLM Cost Learning from Actuals  (Sprint 2)',
         ['How actuals are gathered', 'PROJECT ACTUALS table in Episode pages',
          'How the AI uses actuals', 'API endpoint']),
        ('5', 'Season Optimizer  (Sprint 3)',
         ['Opening the Optimizer page', 'Optimizer Settings panel',
          'Running an optimization', 'Reading the results grid',
          'Overriding individual shots', 'Applying assignments']),
        ('6', 'Invoice-to-Shot Linking  (Sprint 4)',
         ['Tag Shots modal', 'Shots column in Invoice Log',
          'Managing links', 'API endpoints']),
        ('7', 'Vendor Performance Score  (Sprint 4)',
         ['Score components', 'Performance panel in Invoice Log',
          'Score labels', 'API endpoint']),
        ('8', 'Updated Data Flow & API Reference',
         ['New data connections map', 'New API endpoints', 'LLM task keys']),
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


def ch1_overview():
    elems = []
    elems += chapter_header('1', "What's New — Overview",
                             'Four improvement sprints added to the VFX Budget System')

    elems.append(body(
        'UPDATE-SISTEM10 adds four major feature groups to the base system. '
        'All features are backwards-compatible — existing projects, shots, and data are '
        'unaffected. The database schema auto-migrates on next launch.'
    ))

    elems.append(section('Sprint Summary'))
    elems += sprint_summary_table([
        ['Sprint 1', 'Delivery Risk Forecast Engine',     'Dashboard → DELIVERY RISK FORECAST'],
        ['Sprint 1', 'Vendor Capacity Load panel',        'Vendor Tracker → VENDOR CAPACITY & LOAD'],
        ['Sprint 2', 'LLM Cost Learning from Actuals',    'Episode Page → AI cost estimation modal'],
        ['Sprint 3', 'Season Optimizer',                  'Nav → OPTIMIZER (new page)'],
        ['Sprint 4', 'Invoice-to-Shot Linking',           'Invoice Log → SHOTS column / Tag Shots modal'],
        ['Sprint 4', 'Vendor Performance Score',          'Invoice Log → Section E'],
    ])

    elems.append(section('Quick-Start Checklist'))
    elems.append(body('Before using the new features, complete these one-time setup steps:'))
    elems.append(bullet(
        '<b>Capacity Tracker</b> — navigate to Invoice Log → Section D. '
        'Enter <b>Shots/Month</b> and <b>Efficiency %</b> for each active vendor. '
        'These values power Sprint 1 risk scoring and Sprint 3 optimizer.'
    ))
    elems.append(bullet(
        '<b>Shot data quality</b> — ensure Episode page shots have '
        '<b>SHOT TYPE</b>, <b>COMPLEXITY</b>, and <b>EFC</b> filled in. '
        'Sprint 2 actuals learning and Sprint 3 optimizer depend on these fields.'
    ))
    elems.append(bullet(
        '<b>Bid Compare populated</b> — Sprint 3 optimizer reads vendor bid data. '
        'Import at least one BIDCOMPARE Excel file to get vendor options per shot.'
    ))
    elems.append(bullet(
        '<b>Vendor Registry complete</b> — Sprint 4 performance scoring uses '
        'invoice data. Ensure vendors in the registry match vendor names in bids and tracker.'
    ))
    elems.append(tip(
        'All new panels are labelled with their section letter/name and appear at the '
        'bottom of their respective pages. Scroll down if you do not immediately see them.'
    ))

    elems.append(section('Schema Migration'))
    elems.append(body(
        'On first launch after updating, the system automatically runs two migrations:'
    ))
    elems.append(bullet(
        '<b>invoice_shot_links</b> table — junction table linking invoices to shots '
        '(invoice_id, shot_id). Created automatically; no data is modified.'
    ))
    elems.append(warn(
        'If you see a 500 error after updating, open a terminal, '
        'run <b>python app.py</b>, and check the console for migration messages. '
        'The migration is safe and non-destructive.'
    ))

    elems.append(PageBreak())
    return elems


def ch2_risk_forecast():
    elems = []
    elems += chapter_header('2', 'Delivery Risk Forecast',
                             'New 3-component risk engine with predicted delay days',
                             week_label='SPRINT 1')

    elems.append(body(
        'The risk scoring system has been upgraded from a 2-component formula to a '
        '3-component model. The new formula incorporates <b>vendor capacity utilization</b> '
        'alongside complexity and budget variance, giving a more realistic delivery risk picture.'
    ))

    elems.append(section('New Risk Formula'))
    elems.append(body('The updated formula for each episode:'))
    elems.append(code(
        'Risk Score = (Capacity Risk × 0.45)'
        '  +  (Complexity Risk × 0.30)'
        '  +  (Confidence Risk × 0.25)'
    ))
    elems.append(sp(4))
    elems += col_table(
        ['Component', 'Weight', 'How It Is Computed'],
        [
            ['Capacity Risk',    '45%',
             'Based on vendor utilization. Shots awarded to vendors whose load exceeds '
             'their effective capacity (shots/month × efficiency %) push this score up. '
             'Fully available vendors = 0.0; overloaded vendors = up to 1.0.'],
            ['Complexity Risk',  '30%',
             'Fraction of shots that are heavy types (CG, CREATURE, CROWD, FX, EXTENSION) '
             'OR tagged HIGH/HERO complexity. Same logic as the original formula.'],
            ['Confidence Risk',  '25%',
             'Average of (1 − confidence) across all awarded vendors in this episode. '
             'Vendors with HIGH confidence (≥0.70) contribute low risk; LOW confidence '
             'vendors (<0.40) contribute high risk.'],
        ],
        col_widths=[32*mm, 16*mm, 112*mm]
    )

    elems.append(section('Risk Status Badges'))
    elems += badge_row([
        ('SAFE',      '#52c46a'),
        ('WATCH',     '#f0b429'),
        ('AT RISK',   '#e08232'),
        ('HIGH RISK', '#e05252'),
    ])
    elems += info_table([
        ('SAFE',      'Score < 0.20 — delivery on track, capacity comfortable'),
        ('WATCH',     'Score 0.20–0.45 — monitor closely, minor pressure'),
        ('AT RISK',   'Score 0.45–0.70 — significant delivery concern'),
        ('HIGH RISK', 'Score ≥ 0.70 — immediate attention required'),
    ])

    elems.append(section('Predicted Delay Days'))
    elems.append(body(
        'Each episode now also shows a <b>predicted delay</b> value. '
        'This is a rough estimate computed as:'
    ))
    elems.append(code('Predicted Delay (days) = int(risk_score × 30)'))
    elems.append(body(
        'For example, a risk score of 0.60 predicts 18 days of potential schedule slippage. '
        'This is an indicator — not a guarantee. Use it alongside judgement and vendor conversations.'
    ))
    elems.append(warn(
        'Predicted delay is only meaningful when Capacity Tracker data is complete. '
        'If no capacity data exists for a vendor, that vendor contributes 0 to Capacity Risk, '
        'making the score optimistic.'
    ))

    elems.append(section('Dashboard — DELIVERY RISK FORECAST Section'))
    elems.append(body(
        'The Dashboard page now has a <b>DELIVERY RISK FORECAST</b> section below the '
        'existing distribution table. It contains:'
    ))
    elems.append(bullet(
        '<b>Episode Risk Cards</b> — one card per episode showing the risk badge, '
        'score percentage, and predicted delay days. Cards are colour-coded by status.'
    ))
    elems.append(bullet(
        '<b>Sub-score Breakdown Table</b> — a table listing each episode with columns '
        'for Capacity Risk, Complexity Risk, Confidence Risk, Overall Score, Status, '
        'and Predicted Delay. Use this to pinpoint which component is driving the risk.'
    ))
    elems.append(tip(
        'Click the <b>Refresh</b> button at the top of the Dashboard to recalculate '
        'all risk scores after updating shots, bids, or capacity data.'
    ))

    elems += info_table([
        ('API Endpoint', 'GET /api/risk_forecast'),
        ('Response',     'List of {ep, capacity_risk, complexity_risk, confidence_risk, '
                         'score, status, predicted_delay} objects'),
    ])

    elems.append(PageBreak())
    return elems


def ch3_capacity_load():
    elems = []
    elems += chapter_header('3', 'Vendor Capacity Load',
                             'Per-vendor utilization tracking and load visualisation',
                             week_label='SPRINT 1')

    elems.append(body(
        'The Vendor Capacity Load feature connects the Capacity Tracker data '
        '(set in Invoice Log → Section D) with actual awarded shot counts to show '
        'real-time utilization for every vendor.'
    ))

    elems.append(section('Capacity Tracker Fields (Invoice Log → Section D)'))
    elems.append(body(
        'These fields must be populated for load tracking to work. '
        'Navigate to <b>Invoice Log → Section D — Capacity Tracker</b>:'
    ))
    elems += col_table(
        ['Field', 'Description', 'Example'],
        [
            ['VENDOR',        'Vendor name (must match registry)',             'ILM'],
            ['SHOTS / MONTH', 'Estimated shot throughput per calendar month',  '25'],
            ['EFFICIENCY %',  'Realistic delivery factor (100% = full speed)', '90'],
            ['EFFECTIVE CAP', 'Auto-computed: Shots/Month × Efficiency %',    '22.5'],
        ],
        col_widths=[35*mm, 85*mm, 40*mm]
    )
    elems.append(tip(
        'Efficiency % should reflect real-world factors like holiday periods, '
        'handoff delays, and review cycles. 85–95% is typical for established vendors.'
    ))

    elems.append(section('Vendor Tracker — VENDOR CAPACITY & LOAD Panel'))
    elems.append(body(
        'The Vendor Tracker page now includes a <b>VENDOR CAPACITY & LOAD</b> panel '
        'below the main tracker table. For each vendor it shows:'
    ))
    elems += col_table(
        ['Field', 'Description'],
        [
            ['VENDOR',        'Vendor name'],
            ['ASSIGNED SHOTS','Total shots currently awarded to this vendor (from episodes)'],
            ['EFF. CAP',      'Effective capacity from Capacity Tracker (shots/month)'],
            ['UTILIZATION',   'Assigned Shots ÷ Effective Capacity — shown as a percentage bar'],
            ['STATUS',        'OK (green, <80%) / BUSY (yellow, 80–100%) / OVERLOADED (red, >100%)'],
        ],
        col_widths=[30*mm, 130*mm]
    )

    elems.append(section('Reading Utilization Bars'))
    elems.append(body(
        'Each vendor row in the panel shows a colour-coded progress bar:'
    ))
    elems += badge_row([
        ('OK (< 80%)',        '#52c46a'),
        ('BUSY (80–100%)',    '#f0b429'),
        ('OVERLOADED (>100%)', '#e05252'),
    ])
    elems.append(body(
        'An OVERLOADED vendor is a delivery risk signal. Consider redistributing shots '
        'via the Season Optimizer (Chapter 5) or renegotiating with the vendor.'
    ))
    elems.append(tip(
        'Vendors with no capacity data show UTILIZATION = N/A. '
        'Add their Shots/Month in the Capacity Tracker to enable tracking.'
    ))

    elems += info_table([
        ('API Endpoint', 'GET /api/vendor_loads'),
        ('Response',     'List of {vendor, assigned_shots, eff_cap, utilization, status} objects'),
    ])

    elems.append(PageBreak())
    return elems


def ch4_cost_learning():
    elems = []
    elems += chapter_header('4', 'LLM Cost Learning from Actuals',
                             'AI cost estimation anchored to your project\'s own historical data',
                             week_label='SPRINT 2')

    elems.append(body(
        'Previously the AI cost estimator generated figures from general knowledge only. '
        'The updated system now <b>injects your project\'s real EFC data</b> into every '
        'cost estimation prompt, anchoring AI suggestions to actual spend patterns '
        'from your own show.'
    ))

    elems.append(section('How Actuals Are Gathered'))
    elems.append(body(
        'When you click ✨ on a shot to generate a cost estimate, the system first calls '
        '<b>/api/cost_actuals</b> with the shot\'s type, complexity, and vendor. '
        'The engine queries historical EFC figures at three levels of specificity:'
    ))
    elems += col_table(
        ['Level', 'Query', 'Example'],
        [
            ['Specific',   'type + complexity + vendor match',
             'CG + HERO + ILM: $180K avg from 3 shots'],
            ['Partial',    'type + complexity match (any vendor)',
             'CG + HERO: $162K avg from 9 shots'],
            ['Broad',      'type match only (any complexity, any vendor)',
             'CG shots overall: $95K avg from 45 shots'],
        ],
        col_widths=[22*mm, 60*mm, 78*mm]
    )
    elems.append(body(
        'All three levels are returned and formatted as a context string that is injected '
        'into the LLM prompt before generation.'
    ))

    elems.append(section('PROJECT ACTUALS Table — Episode Page'))
    elems.append(body(
        'When the AI cost modal opens on an episode page, a <b>PROJECT ACTUALS</b> table '
        'now appears above the generated estimate. It shows the three actuals buckets '
        'retrieved from your project data so you can see exactly what context the AI used.'
    ))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['MATCH LEVEL',  'Specific / Partial / Broad — how closely the query matched'],
            ['SHOT TYPE',    'Type used in the query'],
            ['COMPLEXITY',   'Complexity tier used in the query'],
            ['VENDOR',       'Vendor used (or "Any" for partial/broad)'],
            ['AVG EFC',      'Average EFC across matched shots'],
            ['SAMPLES',      'Number of shots matched — more samples = higher confidence'],
        ],
        col_widths=[28*mm, 22*mm, 25*mm, 25*mm, 30*mm, 30*mm]
    )
    elems.append(tip(
        'The more shots you have with EFC filled in, the better the actuals data. '
        'Broad averages from 10+ shots are more reliable than a Specific average from 1 shot.'
    ))

    elems.append(section('How the AI Uses Actuals'))
    elems.append(body(
        'The cost_est LLM prompt now opens with an actuals context block, for example:'
    ))
    elems.append(code(
        'Project actuals for CG / HERO / ILM: avg EFC $180K (3 shots)\n'
        'Project actuals for CG / HERO (all vendors): avg EFC $162K (9 shots)\n'
        'Project actuals for CG (all): avg EFC $95K (45 shots)\n'
        'Use these figures as your primary anchor for cost estimation.'
    ))
    elems.append(body(
        'The AI is instructed to anchor its estimate to these project-specific figures '
        'rather than industry generalisations. If actuals data is thin (< 3 samples), '
        'the AI is instructed to widen its confidence range accordingly.'
    ))
    elems.append(warn(
        'Actuals are only as good as your EFC data. Shots with EFC = 0 or EFC = EST '
        '(never updated from estimate) will produce misleadingly low averages. '
        'Keep EFC values current throughout production.'
    ))

    elems += info_table([
        ('API Endpoint', 'GET /api/cost_actuals'),
        ('Query Params', '?shot_type=CG&complexity=HERO&vendor=ILM'),
        ('Response',     '{actuals: "formatted string", buckets: [{level, avg_efc, samples}, ...]}'),
    ])

    elems.append(PageBreak())
    return elems


def ch5_optimizer():
    elems = []
    elems += chapter_header('5', 'Season Optimizer',
                             'Constraint-based vendor assignment for the full season',
                             week_label='SPRINT 3')

    elems.append(body(
        'The Season Optimizer is a new page that proposes the <b>lowest-cost vendor '
        'assignment</b> for every shot in the season, subject to your constraints. '
        'It reads from Bid Compare data and applies confidence, vendor share, and '
        'preferred-vendor rules. <b>It does not write anything until you click Apply.</b>'
    ))

    elems.append(section('Opening the Optimizer'))
    elems.append(body(
        'Click <b>OPTIMIZER</b> in the navigation bar. '
        'The page has three panels:'
    ))
    elems.append(bullet('<b>Left panel</b> — Optimizer Settings'))
    elems.append(bullet('<b>Centre panel</b> — Results grid (appears after running)'))
    elems.append(bullet('<b>Right panel</b> — KPI bar + Vendor share summary'))
    elems.append(warn(
        'The Optimizer page requires Bid Compare data. '
        'If no bids have been imported for a shot, that shot will be labelled NO BID DATA '
        'and skipped in the optimization.'
    ))

    elems.append(section('Optimizer Settings Panel'))
    elems += col_table(
        ['Setting', 'Description', 'Default'],
        [
            ['EPISODE FILTER',
             'Run the optimizer on all episodes or a single selected episode.',
             'All Episodes'],
            ['MIN VENDOR CONFIDENCE',
             'Slider 0.0–1.0. Only vendors meeting this confidence threshold are '
             'eligible for assignment. Setting this higher focuses on proven vendors '
             'but may reduce options.',
             '0.50'],
            ['MAX VENDOR SHARE',
             'Slider 10–100%. Caps the fraction of total shots any single vendor '
             'can receive. Use this to spread workload and reduce concentration risk.',
             '100%'],
            ['PREFERRED VENDORS',
             'Optional checklist loaded from Bid Compare. When any preferred vendor '
             'is checked, the optimizer will assign that vendor wherever they have a '
             'valid bid — ignoring other vendors for those shots.',
             '(none)'],
        ],
        col_widths=[38*mm, 90*mm, 32*mm]
    )

    elems.append(section('Running an Optimization'))
    elems.append(body(
        'Click <b>RUN OPTIMIZER</b>. The system evaluates all shots and returns a '
        'proposed assignment within a second or two. A status message below the button '
        'shows the shot count processed.'
    ))
    elems.append(body('The optimizer algorithm per shot:'))
    elems.append(bullet(
        'Collect all vendors that have submitted a bid for this shot '
        '(from bid_compare table)'
    ))
    elems.append(bullet(
        'Filter to vendors meeting MIN VENDOR CONFIDENCE threshold '
        'and not exceeding MAX VENDOR SHARE'
    ))
    elems.append(bullet(
        'If PREFERRED VENDORS are set and one has a bid, assign that vendor'
    ))
    elems.append(bullet(
        'Otherwise, assign the vendor with the <b>lowest bid amount</b> '
        'that meets all constraints'
    ))
    elems.append(bullet(
        'If no vendor meets the constraints, the shot is marked UNCONSTRAINED '
        'and the cheapest available vendor is assigned regardless'
    ))

    elems.append(section('Reading the Results Grid'))
    elems += col_table(
        ['Column', 'Description'],
        [
            ['EP',              'Episode number'],
            ['SC',              'Scene code'],
            ['SETTING',         'Location / setting description from bid data'],
            ['VFX TYPE',        'VFX type from bid data'],
            ['PROPOSED VENDOR', 'Vendor the optimizer selected'],
            ['BID AMOUNT',      'That vendor\'s bid for this shot'],
            ['CONFIDENCE',      'Vendor confidence badge (HIGH / MED / LOW)'],
            ['LOCK $',          'Locked budget from bid data (if set)'],
            ['OVERRIDE',        'Dropdown to manually override the proposed vendor'],
        ],
        col_widths=[12*mm, 14*mm, 30*mm, 24*mm, 30*mm, 22*mm, 22*mm, 18*mm, 28*mm]
    )
    elems.append(body(
        'Rows with NO BID DATA are shown in muted text — they are excluded from the '
        'optimization and will not be applied.'
    ))

    elems.append(section('KPI Bar'))
    elems.append(body(
        'After running, the KPI bar at the top of the results section shows:'
    ))
    elems.append(bullet('<b>SHOTS ASSIGNED</b> — count of shots with a proposed vendor'))
    elems.append(bullet('<b>NO BID DATA</b> — count of shots the optimizer could not process'))
    elems.append(bullet('<b>TOTAL BID COST</b> — sum of all proposed bid amounts'))
    elems.append(bullet('<b>AVG CONFIDENCE</b> — average confidence score across proposed vendors'))

    elems.append(section('Vendor Share Summary'))
    elems.append(body(
        'Below the KPI bar, a <b>Vendor Share</b> table shows each proposed vendor, '
        'how many shots they are assigned, their share percentage, and total bid cost. '
        'Use this to sense-check workload distribution before applying.'
    ))

    elems.append(section('Overriding Individual Shots'))
    elems.append(body(
        'Any row in the results grid can be overridden. '
        'Click the <b>OVERRIDE</b> dropdown in that row and select a different vendor. '
        'The KPI bar and Vendor Summary update immediately to reflect your override.'
    ))
    elems.append(tip(
        'Overrides are only active for the current session. '
        'They are included when you click Apply Awards — but re-running '
        'the optimizer will reset all overrides to the algorithmic proposal.'
    ))

    elems.append(section('Applying Assignments'))
    elems.append(body(
        'When you are satisfied with the proposed (and optionally overridden) assignments, '
        'click <b>APPLY AWARDS</b>. This writes the <b>award_vendor</b> field on every '
        'matched shot in the episodes tables. Each change is logged in the audit trail.'
    ))
    elems.append(body(
        'The apply response shows: <b>Applied</b> (shots updated) and '
        '<b>Skipped</b> (shots not found or already matching).'
    ))
    elems.append(warn(
        'Apply Awards overwrites existing award_vendor values without confirmation. '
        'Review the results grid carefully before applying, especially if shots '
        'already have vendor awards that should be preserved.'
    ))

    elems.append(section('Typical Workflow'))
    elems += col_table(
        ['Step', 'Action'],
        [
            ['1', 'Ensure Bid Compare has up-to-date bids for the season'],
            ['2', 'Set Capacity Tracker entries so vendor load is accurate'],
            ['3', 'Open Optimizer, set Min Confidence and Max Vendor Share'],
            ['4', 'Optionally check Preferred Vendors'],
            ['5', 'Click RUN OPTIMIZER — review KPI bar and Vendor Summary'],
            ['6', 'Override any individual shots where the proposal is unsuitable'],
            ['7', 'Click APPLY AWARDS — vendor awards are written to episode pages'],
            ['8', 'Return to Dashboard and refresh to see updated risk scores'],
        ],
        col_widths=[12*mm, 148*mm]
    )

    elems.append(PageBreak())
    return elems


def ch6_invoice_shot_linking():
    elems = []
    elems += chapter_header('6', 'Invoice-to-Shot Linking',
                             'Tag specific shots against formal invoice documents',
                             week_label='SPRINT 4')

    elems.append(body(
        'Invoice-to-Shot Linking lets you associate a formal invoice with the '
        'specific VFX shots it covers. This creates a clear audit trail between '
        'financial documents and the creative deliverables they relate to.'
    ))

    elems.append(section('SHOTS Column in Invoice Log'))
    elems.append(body(
        'The Invoice Log table (Section B) now has a <b>SHOTS</b> column. '
        'Each invoice row shows:'
    ))
    elems.append(bullet(
        '<b>Camera icon</b> — click to open the Tag Shots modal for this invoice'
    ))
    elems.append(bullet(
        '<b>Count badge</b> — shows the number of shots currently linked '
        '(e.g. <b>12</b> in blue). Badge is grey (0) if no shots are linked.'
    ))

    elems.append(section('Tag Shots Modal'))
    elems.append(body(
        'Clicking the camera icon opens the <b>Tag Shots</b> modal. It shows a '
        'searchable, scrollable list of all VFX shots in the project. Each shot '
        'shows its episode, scene code, location, type, and complexity.'
    ))
    elems += col_table(
        ['Control', 'Function'],
        [
            ['Search box',          'Filter shots by episode, scene code, or location as you type'],
            ['Checkbox per shot',   'Tick to link this shot to the invoice; untick to unlink'],
            ['EP / SC columns',     'Help identify the correct shot quickly'],
            ['Save button',         'Writes all checked shots as links; removes any unchecked links'],
            ['Cancel button',       'Discards changes and closes the modal'],
        ],
        col_widths=[38*mm, 122*mm]
    )
    elems.append(body(
        'Saving replaces the full link set for this invoice — '
        'shots that were previously linked but are not checked will be removed. '
        'This is a bulk replace, not an additive operation.'
    ))
    elems.append(tip(
        'Use the EP filter in the search box (type "EP203" for example) to '
        'quickly narrow the shot list when an invoice covers a single episode.'
    ))

    elems.append(section('Managing Links'))
    elems.append(body('Links can be managed at any time:'))
    elems.append(bullet(
        'To <b>add shots</b>: open Tag Shots modal, check additional shots, Save'
    ))
    elems.append(bullet(
        'To <b>remove a shot</b>: open Tag Shots modal, uncheck the shot, Save'
    ))
    elems.append(bullet(
        'To <b>remove all links</b>: open Tag Shots modal, uncheck all, Save. '
        'The badge resets to 0.'
    ))
    elems.append(bullet(
        'To <b>delete an invoice</b> with links: links are cascade-deleted automatically'
    ))

    elems.append(section('API Endpoints'))
    elems += col_table(
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/invoicelog/<id>/shots', 'GET',    'List shot IDs linked to this invoice'],
            ['/api/invoicelog/<id>/shots', 'POST',   'Add a single shot link {shot_id}'],
            ['/api/invoicelog/<id>/shots', 'DELETE', 'Remove a single shot link {shot_id}'],
            ['/api/invoicelog/<id>/shots/bulk', 'POST',
             'Replace all shot links at once {shot_ids: [...]}'],
        ],
        col_widths=[58*mm, 18*mm, 84*mm]
    )
    elems.append(body(
        'The bulk endpoint is what the Tag Shots modal uses when you click Save. '
        'The individual GET/POST/DELETE endpoints are available for scripting or '
        'external integration.'
    ))

    elems.append(PageBreak())
    return elems


def ch7_vendor_performance():
    elems = []
    elems += chapter_header('7', 'Vendor Performance Score',
                             'Composite vendor quality metric from bid, invoice, and edit data',
                             week_label='SPRINT 4')

    elems.append(body(
        'The Vendor Performance Score gives each vendor a single composite quality rating '
        'derived from three data sources already in the system. '
        'It appears in <b>Invoice Log → Section E — VENDOR PERFORMANCE SCORE</b>.'
    ))

    elems.append(section('Score Components'))
    elems.append(body('The composite score is computed as:'))
    elems.append(code(
        'Performance Score = (Bid Confidence × 0.50)'
        '  +  (Invoice Accuracy × 0.30)'
        '  +  (Edit Efficiency × 0.20)'
    ))
    elems.append(sp(4))
    elems += col_table(
        ['Component', 'Weight', 'How It Is Computed'],
        [
            ['Bid Confidence',   '50%',
             'The existing vendor confidence score from Bid Compare — based on bid '
             'consistency and sample size. More samples + lower variance = higher score.'],
            ['Invoice Accuracy', '30%',
             'Ratio of approved/paid invoices to total invoices for this vendor. '
             'Vendors who submit clean invoices that are approved without dispute '
             'score higher. Formula: approved_count / max(total_count, 1)'],
            ['Edit Efficiency',  '20%',
             'Ratio of shots at DELIVERED or APPROVED status versus total shots '
             'awarded to this vendor. Vendors who consistently deliver and close out '
             'shots score higher. Formula: delivered_shots / max(awarded_shots, 1)'],
        ],
        col_widths=[32*mm, 16*mm, 112*mm]
    )

    elems.append(section('Performance Score Labels'))
    elems += badge_row([
        ('STRONG', '#52c46a'),
        ('MED',    '#f0b429'),
        ('WEAK',   '#e05252'),
    ])
    elems += info_table([
        ('STRONG', 'Score ≥ 0.65 — reliable vendor, strong track record'),
        ('MED',    'Score 0.40–0.65 — adequate performance, room to improve'),
        ('WEAK',   'Score < 0.40 — underperforming; investigate before awarding new shots'),
    ])

    elems.append(section('Performance Panel — Invoice Log Section E'))
    elems.append(body(
        'Scroll to the bottom of the Invoice Log page to find the '
        '<b>VENDOR PERFORMANCE SCORE</b> panel. For each vendor it shows:'
    ))
    elems.append(bullet('<b>Overall Score</b> — the composite 0.0–1.0 value'))
    elems.append(bullet('<b>Label</b> — STRONG / MED / WEAK badge'))
    elems.append(bullet(
        '<b>Component bars</b> — three horizontal progress bars for '
        'Bid Confidence, Invoice Accuracy, and Edit Efficiency, '
        'showing each sub-score individually'
    ))
    elems.append(tip(
        'Use performance scores when making vendor award decisions alongside bid amounts. '
        'A cheap bid from a WEAK vendor may cost more in rework than a higher bid '
        'from a STRONG vendor.'
    ))

    elems.append(section('Scores Update Automatically'))
    elems.append(body(
        'Performance scores re-compute each time the Invoice Log page loads. '
        'As you approve invoices, deliver shots, and import more bids, '
        'scores reflect the latest data without manual refresh.'
    ))

    elems += info_table([
        ('API Endpoint', 'GET /api/vendor_performance'),
        ('Response',     'List of {vendor, bid_confidence, invoice_accuracy, edit_efficiency, '
                         'score, label} objects'),
    ])

    elems.append(PageBreak())
    return elems


def ch8_data_flow():
    elems = []
    elems += chapter_header('8', 'Updated Data Flow & API Reference',
                             'New data connections and all new API endpoints')

    elems.append(section('Updated Data Connections Map'))
    elems += col_table(
        ['Source', 'Data Provided', 'Consumed By'],
        [
            ['Capacity Tracker',
             'shots_per_month, efficiency_pct per vendor',
             'Risk Forecast (capacity_risk), Vendor Load panel, Optimizer'],
            ['Bid Compare',
             'vendor bids per shot, bid amounts, confidence scores',
             'Optimizer (proposals), Distribution (confidence_risk), Perf Score (bid_confidence)'],
            ['Invoice Log',
             'approved/pending invoice counts per vendor',
             'Vendor Performance Score (invoice_accuracy)'],
            ['Episode shots',
             'award_vendor, status (DELIVERED/APPROVED), EFC history',
             'Optimizer (apply target), Perf Score (edit_efficiency), Cost Actuals (LLM anchor)'],
            ['invoice_shot_links',
             'invoice_id ↔ shot_id links',
             'Invoice Log SHOTS column badge'],
        ],
        col_widths=[35*mm, 65*mm, 60*mm]
    )

    elems.append(section('All New API Endpoints'))
    elems += col_table(
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/risk_forecast',          'GET',   'Per-EP 3-component risk scores'],
            ['/api/vendor_loads',           'GET',   'Vendor capacity utilization'],
            ['/api/cost_actuals',           'GET',   'Historical EFC actuals for LLM injection'],
            ['/api/optimizer/run',          'POST',  'Run optimizer; returns proposed assignments'],
            ['/api/optimizer/vendors',      'GET',   'Vendor list from bid_compare for checklist'],
            ['/api/optimizer/apply',        'POST',  'Write optimizer assignments to shots'],
            ['/api/invoicelog/<id>/shots',  'GET',   'Shot IDs linked to an invoice'],
            ['/api/invoicelog/<id>/shots',  'POST',  'Add a shot link to an invoice'],
            ['/api/invoicelog/<id>/shots',  'DELETE','Remove a shot link from an invoice'],
            ['/api/invoicelog/<id>/shots/bulk', 'POST', 'Bulk replace all shot links for an invoice'],
            ['/api/vendor_performance',     'GET',   'Vendor performance composite scores'],
        ],
        col_widths=[58*mm, 18*mm, 84*mm]
    )

    elems.append(section('New LLM Task Keys'))
    elems += col_table(
        ['Task Key', 'Trigger', 'New Context Added'],
        [
            ['cost_est', 'Episode ✨ cost button',
             'actuals_context — formatted string of project historical EFC buckets'],
        ],
        col_widths=[28*mm, 42*mm, 90*mm]
    )
    elems.append(body(
        'All other LLM task keys (ep_narrative, shot_desc, asset_desc, notes_summary) '
        'are unchanged from the base system.'
    ))

    elems.append(section('Modified Files Reference'))
    elems += col_table(
        ['File', 'What Changed'],
        [
            ['core.py',
             'Added: get_vendor_loads(), compute_ep_risk(), get_cost_actuals(), '
             'run_season_optimizer(), get_vendor_perf_scores(). '
             'DB migration: invoice_shot_links table.'],
            ['routes/optimizer.py',
             'New blueprint: /optimizer page, /api/optimizer/run, /vendors, /apply'],
            ['routes/vendors.py',
             'New endpoints: /api/vendor_loads, /api/vendor_performance, '
             'invoice_shot_links GET/POST/DELETE/bulk'],
            ['routes/dashboard.py',
             'New endpoint: /api/risk_forecast'],
            ['routes/settings_bp.py',
             'Added _enrich_context() + /api/cost_actuals endpoint'],
            ['llm.py',
             'Updated cost_est prompt to use actuals_context when provided'],
            ['templates/dashboard.html',
             'Added DELIVERY RISK FORECAST section (EP cards + sub-score table)'],
            ['templates/vendortracker.html',
             'Added VENDOR CAPACITY & LOAD panel'],
            ['templates/ep.html',
             'Added PROJECT ACTUALS table above AI cost estimate modal'],
            ['templates/optimizer.html',
             'New full page: settings panel, KPI bar, results grid, vendor summary'],
            ['templates/invoicelog.html',
             'Added SHOTS column with camera icon + count badge; Tag Shots modal; '
             'Section E Vendor Performance Score panel'],
            ['templates/base.html',
             'Added OPTIMIZER nav link'],
            ['app.py',
             'Registered optimizer blueprint'],
        ],
        col_widths=[48*mm, 112*mm]
    )

    elems.append(sp(10))
    elems.append(hr(C_GOLD, 1))
    elems.append(sp(6))
    elems.append(Paragraph(
        'End of Update Tutorial  —  VFX Budget System UPDATE-SISTEM10',
        S['cover_sub']
    ))
    elems.append(Paragraph(
        'All features are backwards-compatible. Existing project data is unaffected.',
        S['caption']
    ))

    return elems


# ── Main ───────────────────────────────────────────────────────────────────────
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
    story += ch1_overview()
    story += ch2_risk_forecast()
    story += ch3_capacity_load()
    story += ch4_cost_learning()
    story += ch5_optimizer()
    story += ch6_invoice_shot_linking()
    story += ch7_vendor_performance()
    story += ch8_data_flow()

    doc.build(
        story,
        onFirstPage=on_cover_page,
        onLaterPages=on_page,
    )
    print(f'\nPDF generated: {OUT}\n')


if __name__ == '__main__':
    build()
