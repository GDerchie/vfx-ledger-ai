"""
VFX Budget System — UPDATE-SISTEM10 Feature Tutorial (Word .docx)
Run: python generate_update_tutorial_docx.py
Output: VFX_Budget_System_Update_Tutorial.docx

Covers all four improvement sprints:
  Sprint 1 — Delivery Risk Forecast Engine + Vendor Capacity Load
  Sprint 2 — LLM Cost Learning from Actuals
  Sprint 3 — Season Optimizer
  Sprint 4 — Invoice-to-Shot Linking + Vendor Performance Score
"""

import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = os.path.join(os.path.dirname(__file__), 'VFX_Budget_System_Update_Tutorial.docx')

# ── Colours ───────────────────────────────────────────────────────────────────
GOLD   = RGBColor(0xF0, 0xB4, 0x29)
BLUE   = RGBColor(0x4A, 0x9C, 0xF0)
GREEN  = RGBColor(0x52, 0xC4, 0x6A)
RED    = RGBColor(0xE0, 0x52, 0x52)
ORANGE = RGBColor(0xE0, 0x82, 0x32)
MUTED  = RGBColor(0x78, 0x80, 0xA0)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
DARK   = RGBColor(0x12, 0x15, 0x2A)
PURPLE = RGBColor(0x9B, 0x59, 0xB6)
BLACK  = RGBColor(0x00, 0x00, 0x00)
LIGHT_GREY = RGBColor(0xF2, 0xF2, 0xF2)
MID_GREY   = RGBColor(0xD9, 0xD9, 0xD9)

# ── Document setup ─────────────────────────────────────────────────────────────
def make_doc():
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin   = Cm(2.2)
        section.right_margin  = Cm(2.2)

    # Default paragraph style
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10)
    style.font.color.rgb = BLACK

    return doc

# ── Low-level XML helpers ──────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color: str):
    """Set table cell background shading."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_borders(cell, color='C8C8C8'):
    """Apply thin border to all sides of a cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)

def remove_paragraph_spacing(para):
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), '0')
    spacing.set(qn('w:after'), '0')
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')
    pPr.append(spacing)

# ── Text helpers ───────────────────────────────────────────────────────────────
def add_heading1(doc, text):
    """Chapter title — large gold bold."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = GOLD
    run.font.name = 'Calibri'
    return p

def add_heading2(doc, text):
    """Section heading — blue bold."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = BLUE
    run.font.name = 'Calibri'
    return p

def add_body(doc, text, bold_parts=None):
    """Normal body paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(5)
    # Simple approach: split on <b>...</b> markers
    import re
    parts = re.split(r'<b>(.*?)</b>', text)
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
        run.font.color.rgb = BLACK
        if i % 2 == 1:  # odd index = was inside <b>...</b>
            run.bold = True
    return p

def add_bullet(doc, text, level=0):
    """Bullet list item."""
    import re
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(2)
    parts = re.split(r'<b>(.*?)</b>', text)
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        run.font.size = Pt(10)
        run.font.name = 'Calibri'
        run.font.color.rgb = BLACK
        if i % 2 == 1:
            run.bold = True
    return p

def add_tip(doc, text):
    """Green tip callout."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(f'TIP   {text}')
    run.font.size = Pt(9.5)
    run.font.color.rgb = GREEN
    run.font.italic = True
    run.font.name = 'Calibri'
    return p

def add_warn(doc, text):
    """Orange note/warning callout."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(f'NOTE   {text}')
    run.font.size = Pt(9.5)
    run.font.color.rgb = ORANGE
    run.font.italic = True
    run.font.name = 'Calibri'
    return p

def add_code(doc, text):
    """Monospace code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.8)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    run.font.size = Pt(8.5)
    run.font.name = 'Courier New'
    run.font.color.rgb = BLUE
    return p

def add_sprint_badge(doc, label):
    """Coloured sprint badge as a single-cell table."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, 'F0B429')
    p = cell.paragraphs[0]
    remove_paragraph_spacing(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(label)
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = DARK
    run.font.name = 'Calibri'
    cell.width = Cm(5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_horizontal_rule(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'F0B429')
    pBdr.append(bottom)
    pPr.append(pBdr)

def page_break(doc):
    doc.add_page_break()

# ── Table helpers ──────────────────────────────────────────────────────────────
def _set_col_widths(table, widths_cm):
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                cell.width = Cm(widths_cm[i])

def add_info_table(doc, rows, col_widths_cm=None):
    """Two-column label/value table."""
    t = doc.add_table(rows=len(rows), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    widths = col_widths_cm or [4.5, 11.5]
    for i, (lbl, val) in enumerate(rows):
        c0, c1 = t.cell(i, 0), t.cell(i, 1)
        set_cell_bg(c0, 'EBF0FA')
        set_cell_bg(c1, 'F5F7FC')
        set_cell_borders(c0)
        set_cell_borders(c1)
        c0.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        c1.vertical_alignment = WD_ALIGN_VERTICAL.TOP

        p0 = c0.paragraphs[0]
        remove_paragraph_spacing(p0)
        r0 = p0.add_run(lbl.upper())
        r0.bold = True
        r0.font.size = Pt(8.5)
        r0.font.color.rgb = RGBColor(0x2E, 0x3A, 0x6E)
        r0.font.name = 'Calibri'

        p1 = c1.paragraphs[0]
        remove_paragraph_spacing(p1)
        r1 = p1.add_run(val)
        r1.font.size = Pt(9.5)
        r1.font.name = 'Calibri'
        r1.font.color.rgb = BLACK

    _set_col_widths(t, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_col_table(doc, headers, rows, col_widths_cm=None):
    """Multi-column data table with header row."""
    n = len(headers)
    t = doc.add_table(rows=1 + len(rows), cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    for j, h in enumerate(headers):
        cell = t.cell(0, j)
        set_cell_bg(cell, '2E3A6E')
        set_cell_borders(cell, 'FFFFFF')
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        p = cell.paragraphs[0]
        remove_paragraph_spacing(p)
        run = p.add_run(h.upper())
        run.bold = True
        run.font.size = Pt(8)
        run.font.color.rgb = GOLD
        run.font.name = 'Calibri'

    # Data rows
    for i, row in enumerate(rows):
        bg = 'EBF0FA' if i % 2 == 0 else 'F5F7FC'
        for j, val in enumerate(row):
            cell = t.cell(i + 1, j)
            set_cell_bg(cell, bg)
            set_cell_borders(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            p = cell.paragraphs[0]
            remove_paragraph_spacing(p)
            run = p.add_run(str(val))
            run.font.size = Pt(9)
            run.font.name = 'Calibri'
            run.font.color.rgb = BLACK

    total_width = sum(col_widths_cm) if col_widths_cm else 16.0
    widths = col_widths_cm or [total_width / n] * n
    _set_col_widths(t, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ── Cover page ─────────────────────────────────────────────────────────────────
def cover_page(doc):
    doc.add_paragraph().paragraph_format.space_after = Pt(40)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run('VFX BUDGET SYSTEM')
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = GOLD
    run.font.name = 'Calibri'

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(4)
    r2 = p2.add_run('Update Tutorial — New Features')
    r2.font.size = Pt(14)
    r2.font.color.rgb = MUTED
    r2.font.name = 'Calibri'

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_after = Pt(20)
    r3 = p3.add_run('UPDATE-SISTEM10')
    r3.bold = True
    r3.font.size = Pt(10)
    r3.font.color.rgb = BLUE
    r3.font.name = 'Calibri'

    add_horizontal_rule(doc)

    sprints = [
        ('SPRINT 1', 'Delivery Risk Forecast Engine  +  Vendor Capacity Load'),
        ('SPRINT 2', 'LLM Cost Learning from Project Actuals'),
        ('SPRINT 3', 'Season Optimizer — new constraint-based assignment page'),
        ('SPRINT 4', 'Invoice-to-Shot Linking  +  Vendor Performance Score'),
    ]
    for sprint, desc in sprints:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(f'{sprint}   ')
        r1.bold = True
        r1.font.color.rgb = GOLD
        r1.font.name = 'Calibri'
        r1.font.size = Pt(10)
        r2 = p.add_run(desc)
        r2.font.color.rgb = MUTED
        r2.font.name = 'Calibri'
        r2.font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(20)
    p_conf = doc.add_paragraph()
    p_conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rc = p_conf.add_run('CONFIDENTIAL — INTERNAL USE ONLY')
    rc.font.size = Pt(8)
    rc.font.color.rgb = MUTED
    rc.font.name = 'Calibri'

    page_break(doc)


# ── TOC ────────────────────────────────────────────────────────────────────────
def toc(doc):
    add_heading1(doc, 'Table of Contents')
    add_horizontal_rule(doc)

    chapters = [
        ("1.  What's New — Overview",
         ['Sprint summary', 'Where each feature lives', 'Quick-start checklist']),
        ('2.  Delivery Risk Forecast  (Sprint 1)',
         ['New 3-component risk formula', 'Risk Forecast panel on Dashboard',
          'Predicted delay days', 'Sub-score breakdown table']),
        ('3.  Vendor Capacity Load  (Sprint 1)',
         ['Capacity Tracker fields', 'Load panel on Vendor Tracker',
          'Utilization bars', 'API endpoint']),
        ('4.  LLM Cost Learning from Actuals  (Sprint 2)',
         ['How actuals are gathered', 'PROJECT ACTUALS table in Episode pages',
          'How the AI uses actuals', 'API endpoint']),
        ('5.  Season Optimizer  (Sprint 3)',
         ['Opening the Optimizer page', 'Optimizer Settings panel',
          'Running an optimization', 'Reading the results grid',
          'Overriding individual shots', 'Applying assignments']),
        ('6.  Invoice-to-Shot Linking  (Sprint 4)',
         ['Tag Shots modal', 'Shots column in Invoice Log',
          'Managing links', 'API endpoints']),
        ('7.  Vendor Performance Score  (Sprint 4)',
         ['Score components', 'Performance panel in Invoice Log',
          'Score labels', 'API endpoint']),
        ('8.  Updated Data Flow & API Reference',
         ['New data connections map', 'All new API endpoints', 'Modified files reference']),
    ]

    for ch_title, subs in chapters:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(1)
        r = p.add_run(ch_title)
        r.bold = True
        r.font.size = Pt(10.5)
        r.font.name = 'Calibri'
        r.font.color.rgb = BLACK
        for s in subs:
            ps = doc.add_paragraph()
            ps.paragraph_format.left_indent  = Cm(1.0)
            ps.paragraph_format.space_before = Pt(0)
            ps.paragraph_format.space_after  = Pt(1)
            rs = ps.add_run(f'›  {s}')
            rs.font.size = Pt(9)
            rs.font.name = 'Calibri'
            rs.font.color.rgb = MUTED

    page_break(doc)


# ── Chapter 1 ──────────────────────────────────────────────────────────────────
def ch1_overview(doc):
    add_heading1(doc, "Chapter 1 — What's New: Overview")
    add_horizontal_rule(doc)

    add_body(doc, (
        'UPDATE-SISTEM10 adds four major feature groups to the base VFX Budget System. '
        'All features are backwards-compatible — existing projects, shots, and data are '
        'unaffected. The database schema auto-migrates on next launch.'
    ))

    add_heading2(doc, 'Sprint Summary')
    add_col_table(doc,
        ['Sprint', 'Feature', 'Where to Find'],
        [
            ['Sprint 1', 'Delivery Risk Forecast Engine',  'Dashboard → DELIVERY RISK FORECAST'],
            ['Sprint 1', 'Vendor Capacity Load panel',     'Vendor Tracker → VENDOR CAPACITY & LOAD'],
            ['Sprint 2', 'LLM Cost Learning from Actuals', 'Episode Page → AI cost estimation modal'],
            ['Sprint 3', 'Season Optimizer',               'Nav → OPTIMIZER (new page)'],
            ['Sprint 4', 'Invoice-to-Shot Linking',        'Invoice Log → SHOTS column / Tag Shots modal'],
            ['Sprint 4', 'Vendor Performance Score',       'Invoice Log → Section E'],
        ],
        col_widths_cm=[2.2, 7.0, 7.2]
    )

    add_heading2(doc, 'Quick-Start Checklist')
    add_body(doc, 'Before using the new features, complete these one-time setup steps:')
    add_bullet(doc, (
        'Capacity Tracker — navigate to Invoice Log → Section D. '
        'Enter Shots/Month and Efficiency % for each active vendor. '
        'These values power Sprint 1 risk scoring and Sprint 3 optimizer.'
    ))
    add_bullet(doc, (
        'Shot data quality — ensure Episode page shots have SHOT TYPE, COMPLEXITY, '
        'and EFC filled in. Sprint 2 actuals learning and Sprint 3 optimizer depend on these fields.'
    ))
    add_bullet(doc, (
        'Bid Compare populated — Sprint 3 optimizer reads vendor bid data. '
        'Import at least one BIDCOMPARE Excel file to get vendor options per shot.'
    ))
    add_bullet(doc, (
        'Vendor Registry complete — Sprint 4 performance scoring uses invoice data. '
        'Ensure vendors in the registry match vendor names in bids and tracker.'
    ))
    add_tip(doc, (
        'All new panels are labelled with their section letter/name and appear at the '
        'bottom of their respective pages. Scroll down if you do not immediately see them.'
    ))

    add_heading2(doc, 'Schema Migration')
    add_body(doc, 'On first launch after updating, the system automatically runs two migrations:')
    add_bullet(doc, (
        'invoice_shot_links table — junction table linking invoices to shots '
        '(invoice_id, shot_id). Created automatically; no data is modified.'
    ))
    add_warn(doc, (
        'If you see a 500 error after updating, open a terminal, '
        'run  python app.py  and check the console for migration messages. '
        'The migration is safe and non-destructive.'
    ))

    page_break(doc)


# ── Chapter 2 ──────────────────────────────────────────────────────────────────
def ch2_risk_forecast(doc):
    add_heading1(doc, 'Chapter 2 — Delivery Risk Forecast')
    add_sprint_badge(doc, 'SPRINT 1')
    add_body(doc, 'New 3-component risk engine with predicted delivery delay days.')
    add_horizontal_rule(doc)

    add_body(doc, (
        'The risk scoring system has been upgraded from a 2-component formula to a '
        '3-component model. The new formula incorporates vendor capacity utilization '
        'alongside complexity and budget variance, giving a more realistic delivery risk picture.'
    ))

    add_heading2(doc, 'New Risk Formula')
    add_code(doc,
        'Risk Score = (Capacity Risk × 0.45)\n'
        '           + (Complexity Risk × 0.30)\n'
        '           + (Confidence Risk × 0.25)'
    )
    add_col_table(doc,
        ['Component', 'Weight', 'How It Is Computed'],
        [
            ['Capacity Risk', '45%',
             'Based on vendor utilization. Shots awarded to vendors whose load exceeds '
             'their effective capacity push this score up. '
             'Fully available vendors = 0.0; overloaded = up to 1.0.'],
            ['Complexity Risk', '30%',
             'Fraction of shots that are heavy types (CG, CREATURE, CROWD, FX, EXTENSION) '
             'OR tagged HIGH/HERO complexity.'],
            ['Confidence Risk', '25%',
             'Average of (1 - confidence) across all awarded vendors in the episode. '
             'HIGH confidence vendors contribute low risk; LOW confidence vendors contribute high risk.'],
        ],
        col_widths_cm=[3.2, 1.8, 11.4]
    )

    add_heading2(doc, 'Risk Status Badges')
    add_info_table(doc, [
        ('SAFE',      'Score < 0.20 — delivery on track, capacity comfortable'),
        ('WATCH',     'Score 0.20–0.45 — monitor closely, minor pressure'),
        ('AT RISK',   'Score 0.45–0.70 — significant delivery concern'),
        ('HIGH RISK', 'Score ≥ 0.70 — immediate attention required'),
    ])

    add_heading2(doc, 'Predicted Delay Days')
    add_body(doc, 'Each episode now shows a predicted delay estimate:')
    add_code(doc, 'Predicted Delay (days) = int(risk_score × 30)')
    add_body(doc, (
        'For example, a risk score of 0.60 predicts 18 days of potential schedule slippage. '
        'Use it as an indicator alongside judgement and vendor conversations.'
    ))
    add_warn(doc, (
        'Predicted delay is only meaningful when Capacity Tracker data is complete. '
        'If no capacity data exists for a vendor, that vendor contributes 0 to Capacity Risk, '
        'making the score optimistic.'
    ))

    add_heading2(doc, 'Dashboard — DELIVERY RISK FORECAST Section')
    add_body(doc, (
        'The Dashboard page now has a DELIVERY RISK FORECAST section below the existing '
        'distribution table. It contains:'
    ))
    add_bullet(doc, (
        'Episode Risk Cards — one card per episode showing the risk badge, '
        'score percentage, and predicted delay days.'
    ))
    add_bullet(doc, (
        'Sub-score Breakdown Table — lists each episode with columns for '
        'Capacity Risk, Complexity Risk, Confidence Risk, Overall Score, Status, and Predicted Delay.'
    ))
    add_tip(doc, (
        'Click the Refresh button at the top of the Dashboard to recalculate '
        'all risk scores after updating shots, bids, or capacity data.'
    ))
    add_info_table(doc, [
        ('API Endpoint', 'GET /api/risk_forecast'),
        ('Response',     'List of {ep, capacity_risk, complexity_risk, confidence_risk, score, status, predicted_delay}'),
    ])

    page_break(doc)


# ── Chapter 3 ──────────────────────────────────────────────────────────────────
def ch3_capacity_load(doc):
    add_heading1(doc, 'Chapter 3 — Vendor Capacity Load')
    add_sprint_badge(doc, 'SPRINT 1')
    add_body(doc, 'Per-vendor utilization tracking and load visualisation.')
    add_horizontal_rule(doc)

    add_body(doc, (
        'The Vendor Capacity Load feature connects the Capacity Tracker data '
        '(set in Invoice Log → Section D) with actual awarded shot counts to show '
        'real-time utilization for every vendor.'
    ))

    add_heading2(doc, 'Capacity Tracker Fields (Invoice Log → Section D)')
    add_col_table(doc,
        ['Field', 'Description', 'Example'],
        [
            ['VENDOR',        'Vendor name (must match registry)',             'ILM'],
            ['SHOTS / MONTH', 'Estimated shot throughput per calendar month',  '25'],
            ['EFFICIENCY %',  'Realistic delivery factor (100% = full speed)', '90'],
            ['EFFECTIVE CAP', 'Auto-computed: Shots/Month × Efficiency %',    '22.5'],
        ],
        col_widths_cm=[3.5, 8.5, 4.4]
    )
    add_tip(doc, 'Efficiency % should reflect real-world factors like holiday periods and review cycles. 85–95% is typical.')

    add_heading2(doc, 'Vendor Tracker — VENDOR CAPACITY & LOAD Panel')
    add_body(doc, (
        'The Vendor Tracker page now includes a VENDOR CAPACITY & LOAD panel '
        'below the main tracker table. For each vendor it shows:'
    ))
    add_col_table(doc,
        ['Field', 'Description'],
        [
            ['VENDOR',         'Vendor name'],
            ['ASSIGNED SHOTS', 'Total shots currently awarded to this vendor (from episodes)'],
            ['EFF. CAP',       'Effective capacity from Capacity Tracker (shots/month)'],
            ['UTILIZATION',    'Assigned Shots ÷ Effective Capacity — shown as a percentage bar'],
            ['STATUS',         'OK (green, <80%) / BUSY (yellow, 80–100%) / OVERLOADED (red, >100%)'],
        ],
        col_widths_cm=[3.5, 12.9]
    )

    add_heading2(doc, 'Utilization Status')
    add_info_table(doc, [
        ('OK (< 80%)',         'Vendor has comfortable capacity — safe to award more shots'),
        ('BUSY (80–100%)',     'Vendor is near capacity — monitor and communicate with them'),
        ('OVERLOADED (> 100%)', 'Vendor exceeds capacity — delivery risk; redistribute via Optimizer'),
    ])
    add_tip(doc, (
        'Vendors with no capacity data show UTILIZATION = N/A. '
        'Add their Shots/Month in the Capacity Tracker to enable tracking.'
    ))

    add_info_table(doc, [
        ('API Endpoint', 'GET /api/vendor_loads'),
        ('Response',     'List of {vendor, assigned_shots, eff_cap, utilization, status}'),
    ])

    page_break(doc)


# ── Chapter 4 ──────────────────────────────────────────────────────────────────
def ch4_cost_learning(doc):
    add_heading1(doc, 'Chapter 4 — LLM Cost Learning from Actuals')
    add_sprint_badge(doc, 'SPRINT 2')
    add_body(doc, "AI cost estimation anchored to your project's own historical EFC data.")
    add_horizontal_rule(doc)

    add_body(doc, (
        'Previously the AI cost estimator generated figures from general knowledge only. '
        'The updated system now injects your project\'s real EFC data into every '
        'cost estimation prompt, anchoring AI suggestions to actual spend patterns from your own show.'
    ))

    add_heading2(doc, 'How Actuals Are Gathered')
    add_body(doc, (
        'When you click ✨ on a shot to generate a cost estimate, the system calls '
        '/api/cost_actuals with the shot\'s type, complexity, and vendor. '
        'The engine queries historical EFC figures at three levels of specificity:'
    ))
    add_col_table(doc,
        ['Level', 'Query', 'Example'],
        [
            ['Specific', 'type + complexity + vendor match',      'CG + HERO + ILM: $180K avg from 3 shots'],
            ['Partial',  'type + complexity match (any vendor)',  'CG + HERO: $162K avg from 9 shots'],
            ['Broad',    'type match only (any complexity/vendor)', 'CG shots overall: $95K avg from 45 shots'],
        ],
        col_widths_cm=[2.2, 6.0, 8.2]
    )

    add_heading2(doc, 'PROJECT ACTUALS Table — Episode Page')
    add_body(doc, (
        'When the AI cost modal opens on an episode page, a PROJECT ACTUALS table '
        'now appears above the generated estimate, showing exactly what context the AI used.'
    ))
    add_col_table(doc,
        ['Column', 'Description'],
        [
            ['MATCH LEVEL', 'Specific / Partial / Broad — how closely the query matched'],
            ['SHOT TYPE',   'VFX type used in the query'],
            ['COMPLEXITY',  'Complexity tier used in the query'],
            ['VENDOR',      'Vendor used (or "Any" for partial/broad)'],
            ['AVG EFC',     'Average EFC across matched shots'],
            ['SAMPLES',     'Number of shots matched — more samples = higher confidence'],
        ],
        col_widths_cm=[2.8, 2.2, 2.5, 2.5, 3.0, 3.4]
    )
    add_tip(doc, (
        'The more shots you have with EFC filled in, the better the actuals data. '
        'Broad averages from 10+ shots are more reliable than a Specific average from 1 shot.'
    ))

    add_heading2(doc, 'How the AI Uses Actuals')
    add_body(doc, 'The cost_est LLM prompt now opens with an actuals context block, for example:')
    add_code(doc,
        'Project actuals for CG / HERO / ILM: avg EFC $180K (3 shots)\n'
        'Project actuals for CG / HERO (all vendors): avg EFC $162K (9 shots)\n'
        'Project actuals for CG (all): avg EFC $95K (45 shots)\n'
        'Use these figures as your primary anchor for cost estimation.'
    )
    add_warn(doc, (
        'Actuals are only as good as your EFC data. Shots with EFC = 0 or EFC = EST '
        '(never updated from the estimate) will produce misleadingly low averages. '
        'Keep EFC values current throughout production.'
    ))

    add_info_table(doc, [
        ('API Endpoint', 'GET /api/cost_actuals'),
        ('Query Params', '?shot_type=CG&complexity=HERO&vendor=ILM'),
        ('Response',     '{actuals: "formatted string", buckets: [{level, avg_efc, samples}, ...]}'),
    ])

    page_break(doc)


# ── Chapter 5 ──────────────────────────────────────────────────────────────────
def ch5_optimizer(doc):
    add_heading1(doc, 'Chapter 5 — Season Optimizer')
    add_sprint_badge(doc, 'SPRINT 3')
    add_body(doc, 'Constraint-based vendor assignment for the full season.')
    add_horizontal_rule(doc)

    add_body(doc, (
        'The Season Optimizer is a new page that proposes the lowest-cost vendor '
        'assignment for every shot in the season, subject to your constraints. '
        'It reads from Bid Compare data. It does not write anything until you click Apply.'
    ))

    add_heading2(doc, 'Opening the Optimizer')
    add_body(doc, 'Click OPTIMIZER in the navigation bar. The page has three areas:')
    add_bullet(doc, 'Left panel — Optimizer Settings')
    add_bullet(doc, 'Centre panel — Results grid (appears after running)')
    add_bullet(doc, 'Right panel — KPI bar + Vendor share summary')
    add_warn(doc, (
        'The Optimizer requires Bid Compare data. '
        'If no bids have been imported for a shot, that shot is labelled NO BID DATA and skipped.'
    ))

    add_heading2(doc, 'Optimizer Settings Panel')
    add_col_table(doc,
        ['Setting', 'Description', 'Default'],
        [
            ['EPISODE FILTER',
             'Run on all episodes or a single selected episode.',
             'All Episodes'],
            ['MIN VENDOR CONFIDENCE',
             'Slider 0.0–1.0. Only vendors meeting this confidence threshold are eligible.',
             '0.50'],
            ['MAX VENDOR SHARE',
             'Slider 10–100%. Caps the fraction of total shots any single vendor can receive.',
             '100%'],
            ['PREFERRED VENDORS',
             'Optional checklist. When set, only preferred vendors are selected if they bid the scene.',
             '(none)'],
        ],
        col_widths_cm=[3.8, 9.0, 3.6]
    )

    add_heading2(doc, 'Optimizer Algorithm (per shot)')
    add_bullet(doc, 'Collect all vendors that have submitted a bid for this shot')
    add_bullet(doc, 'Filter to vendors meeting MIN VENDOR CONFIDENCE and not exceeding MAX VENDOR SHARE')
    add_bullet(doc, 'If PREFERRED VENDORS are set and one has a bid, assign that vendor')
    add_bullet(doc, 'Otherwise, assign the vendor with the lowest bid amount meeting all constraints')
    add_bullet(doc, 'If no vendor meets constraints, mark UNCONSTRAINED and assign cheapest available')

    add_heading2(doc, 'Results Grid Columns')
    add_col_table(doc,
        ['Column', 'Description'],
        [
            ['EP',              'Episode number'],
            ['SC',              'Scene code'],
            ['SETTING',         'Location description from bid data'],
            ['VFX TYPE',        'VFX type from bid data'],
            ['PROPOSED VENDOR', 'Vendor the optimizer selected'],
            ['BID AMOUNT',      "That vendor's bid for this shot"],
            ['CONFIDENCE',      'Vendor confidence badge (HIGH / MED / LOW)'],
            ['LOCK $',          'Locked budget from bid data (if set)'],
            ['OVERRIDE',        'Dropdown to manually override the proposed vendor'],
        ],
        col_widths_cm=[1.4, 1.6, 3.2, 2.4, 3.2, 2.2, 2.2, 1.8, 2.4]
    )

    add_heading2(doc, 'KPI Bar')
    add_info_table(doc, [
        ('SHOTS ASSIGNED', 'Count of shots with a proposed vendor'),
        ('NO BID DATA',    'Count of shots the optimizer could not process'),
        ('TOTAL BID COST', 'Sum of all proposed bid amounts'),
        ('AVG CONFIDENCE', 'Average confidence score across proposed vendors'),
    ])

    add_heading2(doc, 'Overriding Individual Shots')
    add_body(doc, (
        'Click the OVERRIDE dropdown in any row to select a different vendor. '
        'The KPI bar and Vendor Summary update immediately.'
    ))
    add_tip(doc, (
        'Overrides are included when you click Apply Awards, but re-running the optimizer '
        'will reset all overrides to the algorithmic proposal.'
    ))

    add_heading2(doc, 'Applying Assignments')
    add_body(doc, (
        'Click APPLY AWARDS to write the award_vendor field on every matched shot. '
        'Each change is logged in the audit trail. '
        'The response shows: Applied (shots updated) and Skipped (not found or already matching).'
    ))
    add_warn(doc, (
        'Apply Awards overwrites existing award_vendor values without confirmation. '
        'Review the results grid carefully before applying.'
    ))

    add_heading2(doc, 'Typical Workflow')
    add_col_table(doc,
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
        col_widths_cm=[1.4, 15.0]
    )

    page_break(doc)


# ── Chapter 6 ──────────────────────────────────────────────────────────────────
def ch6_invoice_shot_linking(doc):
    add_heading1(doc, 'Chapter 6 — Invoice-to-Shot Linking')
    add_sprint_badge(doc, 'SPRINT 4')
    add_body(doc, 'Tag specific shots against formal invoice documents.')
    add_horizontal_rule(doc)

    add_body(doc, (
        'Invoice-to-Shot Linking lets you associate a formal invoice with the '
        'specific VFX shots it covers, creating a clear audit trail between '
        'financial documents and the creative deliverables they relate to.'
    ))

    add_heading2(doc, 'SHOTS Column in Invoice Log')
    add_body(doc, 'The Invoice Log table (Section B) now has a SHOTS column. Each invoice row shows:')
    add_bullet(doc, 'Camera icon — click to open the Tag Shots modal for this invoice')
    add_bullet(doc, 'Count badge — number of shots currently linked (grey = 0, blue = linked count)')

    add_heading2(doc, 'Tag Shots Modal')
    add_body(doc, (
        'Clicking the camera icon opens the Tag Shots modal — '
        'a searchable, scrollable list of all VFX shots in the project.'
    ))
    add_col_table(doc,
        ['Control', 'Function'],
        [
            ['Search box',        'Filter shots by episode, scene code, or location as you type'],
            ['Checkbox per shot', 'Tick to link this shot to the invoice; untick to unlink'],
            ['EP / SC columns',   'Help identify the correct shot quickly'],
            ['Save button',       'Writes all checked shots as links; removes any unchecked links'],
            ['Cancel button',     'Discards changes and closes the modal'],
        ],
        col_widths_cm=[3.8, 12.6]
    )
    add_body(doc, (
        'Saving replaces the full link set for this invoice — '
        'shots that were previously linked but are not checked will be removed. '
        'This is a bulk replace, not an additive operation.'
    ))
    add_tip(doc, (
        'Type "EP203" in the search box to quickly narrow the shot list '
        'when an invoice covers a single episode.'
    ))

    add_heading2(doc, 'Managing Links')
    add_bullet(doc, 'To add shots: open Tag Shots modal, check additional shots, Save')
    add_bullet(doc, 'To remove a shot: open Tag Shots modal, uncheck the shot, Save')
    add_bullet(doc, 'To remove all links: uncheck all, Save — badge resets to 0')
    add_bullet(doc, 'To delete an invoice with links: links are cascade-deleted automatically')

    add_heading2(doc, 'API Endpoints')
    add_col_table(doc,
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/invoicelog/<id>/shots',        'GET',    'List shot IDs linked to this invoice'],
            ['/api/invoicelog/<id>/shots',        'POST',   'Add a single shot link {shot_id}'],
            ['/api/invoicelog/<id>/shots',        'DELETE', 'Remove a single shot link {shot_id}'],
            ['/api/invoicelog/<id>/shots/bulk',   'POST',   'Replace all shot links {shot_ids: [...]}'],
        ],
        col_widths_cm=[6.0, 1.8, 8.6]
    )

    page_break(doc)


# ── Chapter 7 ──────────────────────────────────────────────────────────────────
def ch7_vendor_performance(doc):
    add_heading1(doc, 'Chapter 7 — Vendor Performance Score')
    add_sprint_badge(doc, 'SPRINT 4')
    add_body(doc, 'Composite vendor quality metric from bid, invoice, and edit data.')
    add_horizontal_rule(doc)

    add_body(doc, (
        'The Vendor Performance Score gives each vendor a single composite quality rating '
        'derived from three data sources already in the system. '
        'It appears in Invoice Log → Section E — VENDOR PERFORMANCE SCORE.'
    ))

    add_heading2(doc, 'Score Components')
    add_code(doc,
        'Performance Score = (Bid Confidence × 0.50)\n'
        '                  + (Invoice Accuracy × 0.30)\n'
        '                  + (Edit Efficiency  × 0.20)'
    )
    add_col_table(doc,
        ['Component', 'Weight', 'How It Is Computed'],
        [
            ['Bid Confidence',   '50%',
             'Existing vendor confidence score from Bid Compare — based on bid '
             'consistency and sample size.'],
            ['Invoice Accuracy', '30%',
             'Ratio of approved/paid invoices to total invoices. '
             'Formula: approved_count / max(total_count, 1)'],
            ['Edit Efficiency',  '20%',
             'Ratio of shots at DELIVERED or APPROVED status vs total shots awarded. '
             'Formula: delivered_shots / max(awarded_shots, 1)'],
        ],
        col_widths_cm=[3.2, 1.8, 11.4]
    )

    add_heading2(doc, 'Performance Score Labels')
    add_info_table(doc, [
        ('STRONG', 'Score ≥ 0.65 — reliable vendor, strong track record'),
        ('MED',    'Score 0.40–0.65 — adequate performance, room to improve'),
        ('WEAK',   'Score < 0.40 — underperforming; investigate before awarding new shots'),
    ])

    add_heading2(doc, 'Performance Panel — Invoice Log Section E')
    add_body(doc, (
        'Scroll to the bottom of the Invoice Log page to find the '
        'VENDOR PERFORMANCE SCORE panel. For each vendor it shows:'
    ))
    add_bullet(doc, 'Overall Score — the composite 0.0–1.0 value')
    add_bullet(doc, 'Label — STRONG / MED / WEAK badge')
    add_bullet(doc, (
        'Component bars — three horizontal progress bars for '
        'Bid Confidence, Invoice Accuracy, and Edit Efficiency'
    ))
    add_tip(doc, (
        'Use performance scores when making vendor award decisions alongside bid amounts. '
        'A cheap bid from a WEAK vendor may cost more in rework than a higher bid from a STRONG vendor.'
    ))

    add_heading2(doc, 'Scores Update Automatically')
    add_body(doc, (
        'Performance scores re-compute each time the Invoice Log page loads. '
        'As you approve invoices, deliver shots, and import more bids, '
        'scores reflect the latest data without manual refresh.'
    ))

    add_info_table(doc, [
        ('API Endpoint', 'GET /api/vendor_performance'),
        ('Response',     'List of {vendor, bid_confidence, invoice_accuracy, edit_efficiency, score, label}'),
    ])

    page_break(doc)


# ── Chapter 8 ──────────────────────────────────────────────────────────────────
def ch8_data_flow(doc):
    add_heading1(doc, 'Chapter 8 — Updated Data Flow & API Reference')
    add_horizontal_rule(doc)

    add_heading2(doc, 'New Data Connections Map')
    add_col_table(doc,
        ['Source', 'Data Provided', 'Consumed By'],
        [
            ['Capacity Tracker',
             'shots_per_month, efficiency_pct per vendor',
             'Risk Forecast (capacity_risk), Vendor Load panel, Optimizer'],
            ['Bid Compare',
             'vendor bids per shot, confidence scores',
             'Optimizer (proposals), Risk Forecast (confidence_risk), Perf Score (bid_confidence)'],
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
        col_widths_cm=[3.5, 6.5, 6.4]
    )

    add_heading2(doc, 'All New API Endpoints')
    add_col_table(doc,
        ['Endpoint', 'Method', 'Description'],
        [
            ['/api/risk_forecast',               'GET',   'Per-EP 3-component risk scores'],
            ['/api/vendor_loads',                'GET',   'Vendor capacity utilization'],
            ['/api/cost_actuals',               'GET',   'Historical EFC actuals for LLM injection'],
            ['/api/optimizer/run',              'POST',  'Run optimizer; returns proposed assignments'],
            ['/api/optimizer/vendors',          'GET',   'Vendor list from bid_compare for checklist'],
            ['/api/optimizer/apply',            'POST',  'Write optimizer assignments to shots'],
            ['/api/invoicelog/<id>/shots',      'GET',   'Shot IDs linked to an invoice'],
            ['/api/invoicelog/<id>/shots',      'POST',  'Add a shot link to an invoice'],
            ['/api/invoicelog/<id>/shots',      'DELETE','Remove a shot link from an invoice'],
            ['/api/invoicelog/<id>/shots/bulk', 'POST',  'Bulk replace all shot links for an invoice'],
            ['/api/vendor_performance',         'GET',   'Vendor performance composite scores'],
        ],
        col_widths_cm=[5.8, 1.8, 8.8]
    )

    add_heading2(doc, 'Modified Files Reference')
    add_col_table(doc,
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
             'Added SHOTS column + Tag Shots modal + Section E Vendor Performance Score panel'],
            ['templates/base.html',
             'Added OPTIMIZER nav link'],
            ['app.py',
             'Registered optimizer blueprint'],
        ],
        col_widths_cm=[4.8, 11.6]
    )

    add_horizontal_rule(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run('End of Update Tutorial  —  VFX Budget System UPDATE-SISTEM10')
    r.font.size = Pt(10)
    r.font.color.rgb = MUTED
    r.font.name = 'Calibri'

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run('All features are backwards-compatible. Existing project data is unaffected.')
    r2.font.size = Pt(9)
    r2.font.color.rgb = MUTED
    r2.font.italic = True
    r2.font.name = 'Calibri'


# ── Main ───────────────────────────────────────────────────────────────────────
def build():
    doc = make_doc()
    cover_page(doc)
    toc(doc)
    ch1_overview(doc)
    ch2_risk_forecast(doc)
    ch3_capacity_load(doc)
    ch4_cost_learning(doc)
    ch5_optimizer(doc)
    ch6_invoice_shot_linking(doc)
    ch7_vendor_performance(doc)
    ch8_data_flow(doc)
    doc.save(OUT)
    print(f'\nWord doc generated: {OUT}\n')


if __name__ == '__main__':
    build()
