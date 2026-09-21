"""
MACHIAVELLI_a004 — PowerPoint Presentation Generator
Generates a comprehensive deck describing each system aspect and utility.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
BG_DARK   = RGBColor(0x0D, 0x0D, 0x1A)   # deep navy
BG_PANEL  = RGBColor(0x14, 0x18, 0x2B)   # panel
ACCENT1   = RGBColor(0x00, 0xC8, 0xFF)   # cyan
ACCENT2   = RGBColor(0xA0, 0x5C, 0xFF)   # violet
ACCENT3   = RGBColor(0xFF, 0x6B, 0x35)   # orange
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LTGRAY    = RGBColor(0xCC, 0xCC, 0xDD)
MIDGRAY   = RGBColor(0x55, 0x55, 0x77)
GREEN     = RGBColor(0x00, 0xE5, 0x87)
YELLOW    = RGBColor(0xFF, 0xD7, 0x00)

# ─── SLIDE DIMENSIONS  (16:9  13.33 × 7.5 in) ────────────────────────────────
W = Inches(13.33)
H = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

blank_layout = prs.slide_layouts[6]   # truly blank

# ─── LOW-LEVEL HELPERS ────────────────────────────────────────────────────────

def add_rect(slide, x, y, w, h, fill_rgb, alpha=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)   # MSO_SHAPE_TYPE.RECTANGLE=1
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    shape.line.fill.background()
    return shape

def add_text(slide, text, x, y, w, h,
             size=18, bold=False, italic=False,
             color=WHITE, align=PP_ALIGN.LEFT, wrap=True):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return tb

def add_para(tf, text, size=14, bold=False, color=LTGRAY,
             align=PP_ALIGN.LEFT, space_before=0):
    p = tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return p

def slide_bg(slide, color=BG_DARK):
    add_rect(slide, 0, 0, W, H, color)

def accent_bar(slide, color=ACCENT1, height=Inches(0.06)):
    add_rect(slide, 0, 0, W, height, color)

def section_header_bar(slide, title, color=ACCENT1):
    add_rect(slide, 0, Inches(0.06), W, Inches(0.72), BG_PANEL)
    add_text(slide, title,
             Inches(0.4), Inches(0.10), Inches(12.5), Inches(0.68),
             size=24, bold=True, color=color)

def divider(slide, y, color=MIDGRAY):
    add_rect(slide, Inches(0.4), y, Inches(12.53), Inches(0.01), color)

def bullet_box(slide, items, x, y, w, h,
               dot_color=ACCENT1, text_color=LTGRAY, size=13.5):
    """items = list of strings (or (str, sub_items) tuples)"""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        # bullet dot
        dot = p.add_run()
        dot.text = "▸  "
        dot.font.size  = Pt(size)
        dot.font.bold  = True
        dot.font.color.rgb = dot_color
        # text
        run = p.add_run()
        run.text = item
        run.font.size  = Pt(size)
        run.font.color.rgb = text_color
    return tb

def kv_box(slide, pairs, x, y, w, h,
           key_color=ACCENT1, val_color=LTGRAY, size=12.5):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for k, v in pairs:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        kr = p.add_run()
        kr.text = f"{k}:  "
        kr.font.size = Pt(size)
        kr.font.bold = True
        kr.font.color.rgb = key_color
        vr = p.add_run()
        vr.text = v
        vr.font.size = Pt(size)
        vr.font.color.rgb = val_color
    return tb

def pill(slide, text, x, y, color=ACCENT1, bg=None, size=11):
    w = Inches(1.65); h = Inches(0.30)
    r = slide.shapes.add_shape(5, x, y, w, h)   # rounded rect = 5
    r.fill.solid(); r.fill.fore_color.rgb = RGBColor(0x1A,0x1E,0x3A)
    r.line.color.rgb = color; r.line.width = Pt(1)
    tf = r.text_frame; tf.word_wrap = False
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    run = p.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = True
    run.font.color.rgb = color

def metric_card(slide, label, value, x, y, w=Inches(2.6), h=Inches(1.3),
                accent=ACCENT1):
    add_rect(slide, x, y, w, h, RGBColor(0x14,0x18,0x2B))
    r = slide.shapes.add_shape(5, x, y, w, h)
    r.fill.background(); r.line.color.rgb = accent; r.line.width = Pt(1.2)
    add_text(slide, value, x, y+Inches(0.18), w, Inches(0.55),
             size=28, bold=True, color=accent, align=PP_ALIGN.CENTER)
    add_text(slide, label, x, y+Inches(0.72), w, Inches(0.45),
             size=11, color=LTGRAY, align=PP_ALIGN.CENTER)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s)

# top accent gradient bar
add_rect(s, 0, 0, W, Inches(0.08), ACCENT1)
add_rect(s, 0, Inches(0.08), W, Inches(0.04), ACCENT2)

# large hero text
add_text(s, "MACHIAVELLI_a004",
         Inches(0.6), Inches(1.3), Inches(12.1), Inches(1.1),
         size=52, bold=True, color=ACCENT1)

add_text(s, "VFX Budget Intelligence System",
         Inches(0.6), Inches(2.35), Inches(11.0), Inches(0.7),
         size=30, bold=False, color=WHITE)

add_text(s, "End-to-End Budget Tracking · Vendor Optimization · Risk Forecasting · AI-Assisted Workflows",
         Inches(0.6), Inches(3.05), Inches(12.0), Inches(0.5),
         size=16, italic=True, color=LTGRAY)

divider(s, Inches(3.7), ACCENT2)

# tech pills
pills = ["Flask 3.1", "SQLite WAL", "Ollama / Claude / OpenAI",
         "openpyxl", "reportlab", "8,651 Lines Python"]
for i, p_txt in enumerate(pills):
    pill(s, p_txt, Inches(0.6 + i*2.12), Inches(3.90), ACCENT1)

# bottom stats
metric_card(s, "Python Modules",   "54",  Inches(0.60), Inches(5.0), accent=ACCENT1)
metric_card(s, "Flask Blueprints", "12",  Inches(3.35), Inches(5.0), accent=ACCENT2)
metric_card(s, "LLM Prompt Tasks", "21",  Inches(6.10), Inches(5.0), accent=ACCENT3)
metric_card(s, "HTML Templates",   "17",  Inches(8.85), Inches(5.0), accent=GREEN)
metric_card(s, "Excel Templates",  "8",   Inches(11.60), Inches(5.0), accent=YELLOW)

add_text(s, "VFX Budget System  ·  2026",
         Inches(0.4), Inches(7.1), Inches(6.0), Inches(0.32),
         size=10, color=MIDGRAY)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 — SYSTEM OVERVIEW / ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT2)
section_header_bar(s, "SYSTEM OVERVIEW — Architecture", ACCENT2)

# left column: architecture description
bullet_box(s, [
    "Flask 3.1 Blueprint pattern — 12 route modules, clean separation of concerns",
    "SQLite with WAL mode — per-project .vfxdb databases + master projects.db",
    "Service layer — reusable business logic decoupled from HTTP handlers",
    "LLM abstraction — pluggable provider (Ollama / Claude / OpenAI) via llm_config.json",
    "Importer pipeline — Excel → validate → LLM column-map → upsert/append/replace",
    "Background jobs — threading-based async queue with Jobs/ dir state files",
    "Audit trail — every financial field change logged with old/new values",
    "Report engine — PDF via reportlab, Excel via openpyxl, Jinja2 HTML export",
], Inches(0.4), Inches(1.0), Inches(5.8), Inches(5.8), size=13)

# right column: module tree visual
add_rect(s, Inches(6.5), Inches(0.95), Inches(6.5), Inches(6.2), RGBColor(0x10,0x13,0x26))
add_text(s, "Module Tree",
         Inches(6.7), Inches(1.05), Inches(6.0), Inches(0.35),
         size=13, bold=True, color=ACCENT2)

tree_lines = [
    ("app.py", ACCENT2, 0),
    ("routes/  (12 blueprints)", ACCENT1, 1),
    ("episodes · vendors · dashboard", LTGRAY, 2),
    ("optimizer · reports · settings", LTGRAY, 2),
    ("services/  (12 modules)", ACCENT1, 1),
    ("db · schema · shots · vendors_svc", LTGRAY, 2),
    ("distribution · optimizer · llm_svc", LTGRAY, 2),
    ("slack · data_graph · audit", LTGRAY, 2),
    ("llm/  (5 modules + 21 prompts)", ACCENT1, 1),
    ("cache · parsers · registry", LTGRAY, 2),
    ("importers/  (5 modules)", ACCENT1, 1),
    ("shots · invoices · assets · base", LTGRAY, 2),
    ("jobs/  (queue + api)", ACCENT1, 1),
    ("templates/  (17 HTML)", ACCENT1, 1),
    ("static/  (3 JS + 2 CSS)", ACCENT1, 1),
]
tb = s.shapes.add_textbox(Inches(6.7), Inches(1.50), Inches(6.1), Inches(5.5))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line, col, indent in tree_lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run()
    run.text = ("    " * indent) + line
    run.font.size = Pt(11.5)
    run.font.color.rgb = col
    run.font.name = "Courier New"

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 3 — DATABASE LAYER
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, GREEN)
section_header_bar(s, "DATABASE LAYER — Schema & Storage", GREEN)

# left: key tables
add_text(s, "Core Tables",
         Inches(0.4), Inches(0.95), Inches(6.0), Inches(0.38),
         size=15, bold=True, color=GREEN)

tables = [
    ("shots",           "VFX work items — cost_est, EFC, complexity, award_vendor, omit"),
    ("vendor_registry", "Master vendor list — region, FX rates, tax %, rebate %"),
    ("vendor_capacity", "Per-vendor monthly capacity & efficiency %"),
    ("vendor_tracker",  "Payments — award, paid, pending, remaining, tax, rebate"),
    ("bid_compare",     "Scene-level bids from multiple vendors + VFX type"),
    ("invoice_log",     "Invoices received — vendor, amount, status, date"),
    ("assets",          "Asset registry — est_budget, actual_spend, description"),
    ("budget_scenario", "Conservative / Optimistic / Custom scenario modeling"),
    ("ep_forecast",     "Per-episode forecast — budget, contingency, eligible %"),
    ("ai_calls",        "LLM result cache — (task, content_hash) → result + token cost"),
    ("change_log",      "Audit trail — table, row, field, old/new value, user, timestamp"),
    ("project_settings","Slack webhook, alert threshold, API token, default region"),
]
tb = s.shapes.add_textbox(Inches(0.4), Inches(1.38), Inches(6.2), Inches(5.7))
tf = tb.text_frame; tf.word_wrap = True
first = True
for tname, desc in tables:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    r1 = p.add_run(); r1.text = f"{tname}  "; r1.font.size = Pt(11.5)
    r1.font.bold = True; r1.font.color.rgb = GREEN; r1.font.name = "Courier New"
    r2 = p.add_run(); r2.text = desc; r2.font.size = Pt(11.5)
    r2.font.color.rgb = LTGRAY

# right: architecture notes
add_rect(s, Inches(6.9), Inches(0.90), Inches(6.05), Inches(5.95), RGBColor(0x10,0x14,0x28))
add_text(s, "Storage Architecture",
         Inches(7.05), Inches(1.00), Inches(5.7), Inches(0.35),
         size=14, bold=True, color=GREEN)
bullet_box(s, [
    "projects.db — master registry, shared across all projects",
    "projects/*.vfxdb — per-project SQLite (one file per show/season)",
    "WAL mode enabled — concurrent reads during background writes",
    "Foreign key enforcement via PRAGMA on every connection open",
    "Per-request connection pool via Flask g context",
    "Connection teardown via teardown_appcontext (no leaks)",
    "Parameterized queries throughout — SQL injection prevention",
    "Schema migrations run on startup (schema.py init_db)",
    "Shot model: id, ep, shot_num, scene_code, location, ext_int,",
    "  asset, script_desc, vfx_desc, shot_type, complexity,",
    "  cost_est, efc, award_vendor, edit_count, omit, notes",
], Inches(7.05), Inches(1.42), Inches(5.7), Inches(5.3),
   dot_color=GREEN, size=12)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 4 — LLM INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT3)
section_header_bar(s, "LLM INTEGRATION — AI-Assisted Workflows", ACCENT3)

# provider pills row
add_text(s, "Supported Providers:",
         Inches(0.4), Inches(1.00), Inches(2.4), Inches(0.35),
         size=13, bold=True, color=ACCENT3)
for i, (lbl, col) in enumerate([("Ollama (local)", GREEN), ("Claude API", ACCENT1), ("OpenAI", ACCENT2)]):
    pill(s, lbl, Inches(2.65 + i*2.12), Inches(1.00), col)

add_text(s, "21 Task-Specific YAML Prompts",
         Inches(8.7), Inches(1.00), Inches(4.2), Inches(0.35),
         size=13, bold=True, color=ACCENT3)

divider(s, Inches(1.45), MIDGRAY)

# task table — left
add_text(s, "LLM Tasks & Outputs",
         Inches(0.4), Inches(1.55), Inches(6.5), Inches(0.35),
         size=13, bold=True, color=ACCENT3)
tasks = [
    ("vfx_desc",          "1–2 sentence VFX description from scene context"),
    ("shot_type",         "Classify: CG / Comp / Roto / Paint / Grade / FX…"),
    ("cost_est / v2",     "USD estimate + tier (LOW/MED/HIGH) + reasoning"),
    ("complexity_tag",    "SIMPLE / MEDIUM / HEAVY per shot"),
    ("complexity_batch",  "Multi-shot complexity ratings in one call"),
    ("ep_narrative",      "2-sentence producer memo from episode stats"),
    ("bid_analysis",      "Vendor cost summary + award recommendations"),
    ("budget_gap_analysis","Identify scenes with missing/under-estimated bids"),
    ("season_risk",       "Season-level risk summary from per-ep risk scores"),
    ("vendor_suggest_v2", "Recommend best vendor for shot given current load"),
    ("scenario_advice",   "Budget scenario guidance (conservative / optimistic)"),
    ("invoice_check",     "Invoice ↔ shot linking suggestions"),
    ("batch_vfx_desc",    "Batch VFX descriptions — multiple shots in one call"),
    ("vendor_narrative",  "Vendor performance summary from spend data"),
    ("notes_summarize",   "VFX notes thread summary"),
    ("audit_explain",     "Plain-English explanation of a change log entry"),
]
tb = s.shapes.add_textbox(Inches(0.4), Inches(1.96), Inches(6.4), Inches(5.1))
tf = tb.text_frame; tf.word_wrap = True
first = True
for task, desc in tasks:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    r1 = p.add_run(); r1.text = f"{task}  "; r1.font.size = Pt(10.5)
    r1.font.bold = True; r1.font.color.rgb = ACCENT3; r1.font.name = "Courier New"
    r2 = p.add_run(); r2.text = desc; r2.font.size = Pt(10.5)
    r2.font.color.rgb = LTGRAY

# right column: caching + context injection
add_rect(s, Inches(7.1), Inches(1.50), Inches(5.85), Inches(5.65), RGBColor(0x11,0x13,0x25))
add_text(s, "Intelligent Cost Context Injection",
         Inches(7.25), Inches(1.60), Inches(5.5), Inches(0.36),
         size=13, bold=True, color=ACCENT3)
bullet_box(s, [
    "LLM cost_est prompt anchored to project actuals:",
    "  → Query all shots of same type (e.g. Comp)",
    "  → Query same type + complexity (e.g. Comp/HEAVY)",
    "  → Query same type + vendor (e.g. Comp at SomeVendor)",
    "  → Inject min / max / avg into prompt",
    "  → LLM estimates within historical range",
    "Result caching — ai_calls table (task + content_hash key)",
    "Token cost tracking — Ollama free, Claude/OpenAI tracked per call",
    "Provider config in llm_config.json (hot-swap providers)",
    "max_tokens: 600  ·  temperature: 0.3 (deterministic)",
    "Retry logic + JSON extraction in llm/parsers.py",
    "Batch calls reduce round-trips for multi-shot operations",
], Inches(7.25), Inches(2.00), Inches(5.5), Inches(4.9),
   dot_color=ACCENT3, size=11.5)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 5 — VENDOR SCORING & OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT1)
section_header_bar(s, "VENDOR SCORING & SEASON OPTIMIZER", ACCENT1)

# formula panel left
add_rect(s, Inches(0.35), Inches(0.95), Inches(6.2), Inches(3.35), RGBColor(0x0E,0x11,0x22))
add_text(s, "Vendor Performance Score",
         Inches(0.55), Inches(1.05), Inches(5.8), Inches(0.36),
         size=14, bold=True, color=ACCENT1)

formula_lines = [
    "composite = bid_confidence × 0.50",
    "          + invoice_accuracy × 0.30",
    "          + edit_efficiency  × 0.20",
    "",
    "bid_confidence:",
    "  cv = std_dev(bids) / mean(bids)",
    "  sample = min(num_bids / 30, 1.0)",
    "  confidence = sample × max(0, 1 − cv)",
    "",
    "invoice_accuracy:",
    "  1 − |total_award − paid| / total_award",
    "",
    "edit_efficiency:",
    "  1 − (avg_edit_count / 20).clamp(0, 1)",
    "",
    "Labels:  STRONG ≥ 0.65  ·  MED ≥ 0.40  ·  WEAK < 0.40",
]
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.48), Inches(5.85), Inches(2.65))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line in formula_lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run(); run.text = line
    run.font.size = Pt(11); run.font.name = "Courier New"
    run.font.color.rgb = GREEN if "=" in line or ":" in line else LTGRAY

# optimizer panel right
add_rect(s, Inches(6.7), Inches(0.95), Inches(6.3), Inches(3.35), RGBColor(0x0E,0x11,0x22))
add_text(s, "Season Optimizer Algorithm",
         Inches(6.85), Inches(1.05), Inches(5.9), Inches(0.36),
         size=14, bold=True, color=ACCENT1)

opt_lines = [
    "For each unassigned shot:",
    "  1. Find bid_compare row by scene_code",
    "  2. For each vendor with a bid on that scene:",
    "     - Skip if confidence < min_confidence",
    "     - Skip if vendor workload share > max_vendor_share",
    "     - Skip if preferred_vendor constraint not met",
    "  3. Assign to vendor with lowest per-shot cost",
    "",
    "Output:",
    "  assignments  — {shot_id → vendor, cost, ep, type}",
    "  vendor_summary — shots, total_cost, workload %, confidence",
    "  overall_confidence — weighted average across all shots",
    "  unassigned_shots — shots with no eligible vendor bid",
    "",
    "UI controls: min_confidence slider · max_vendor_share %",
    "            preferred vendor constraints per shot type",
]
tb = s.shapes.add_textbox(Inches(6.85), Inches(1.48), Inches(6.0), Inches(2.65))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line in opt_lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run(); run.text = line
    run.font.size = Pt(11); run.font.name = "Courier New"
    run.font.color.rgb = ACCENT1 if line.strip().startswith(("For", "Output", "UI")) else LTGRAY

# bottom: key points
add_text(s, "Key Utility",
         Inches(0.35), Inches(4.45), Inches(12.6), Inches(0.35),
         size=14, bold=True, color=ACCENT1)
bullet_box(s, [
    "Eliminates manual spreadsheet comparison — lowest-cost vendor found algorithmically",
    "CV-based confidence prevents awarding shots to vendors with erratic bid histories",
    "Workload cap prevents over-concentration — balances pipeline across vendors",
    "Performance scoring compounds over time — rewards consistent, efficient vendors",
    "STRONG / MED / WEAK labels give producers instant vendor health at a glance",
], Inches(0.35), Inches(4.85), Inches(12.6), Inches(2.35),
   dot_color=ACCENT1, size=13)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 6 — RISK FORECASTING
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT3)
section_header_bar(s, "DELIVERY RISK FORECASTING", ACCENT3)

# formula
add_rect(s, Inches(0.35), Inches(0.95), Inches(6.0), Inches(4.05), RGBColor(0x0E,0x11,0x22))
add_text(s, "Risk Formula (per episode)",
         Inches(0.55), Inches(1.05), Inches(5.6), Inches(0.36),
         size=14, bold=True, color=ACCENT3)

risk_lines = [
    "risk_score =",
    "  capacity_risk   × 0.45",
    "  + complexity_risk × 0.30",
    "  + confidence_risk × 0.25",
    "",
    "capacity_risk:",
    "  util = assigned_shots / vendor_monthly_capacity",
    "  util > 1.0  → risk = 1.0  (OVERLOAD)",
    "  util > 0.85 → risk = 0.5  (CAUTION)",
    "",
    "complexity_risk (per shot):",
    "  HEAVY += 0.6 · HERO += 1.0",
    "  final = sum / n_shots  (clamped 0–1)",
    "",
    "confidence_risk:",
    "  per shot: 1 − vendor_bid_confidence",
    "  final = mean across all assigned shots",
    "",
    "predicted_delay_days = int(risk_score × 30)",
]
tb = s.shapes.add_textbox(Inches(0.55), Inches(1.48), Inches(5.65), Inches(3.35))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line in risk_lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run(); run.text = line
    run.font.size = Pt(10.8); run.font.name = "Courier New"
    run.font.color.rgb = ACCENT3 if "risk" in line.lower() and "=" in line else LTGRAY

# status legend
add_text(s, "Status Thresholds",
         Inches(0.55), Inches(5.10), Inches(5.6), Inches(0.35),
         size=13, bold=True, color=ACCENT3)
statuses = [
    ("SAFE",      "< 0.25",    GREEN),
    ("WATCH",     "0.25–0.50", YELLOW),
    ("AT RISK",   "0.50–0.75", ACCENT3),
    ("HIGH RISK", "> 0.75",    RGBColor(0xFF,0x30,0x30)),
]
for i, (lbl, rng, col) in enumerate(statuses):
    add_rect(s, Inches(0.55 + i*1.40), Inches(5.52), Inches(1.30), Inches(0.52), RGBColor(0x14,0x18,0x2B))
    r = s.shapes.add_shape(5, Inches(0.55 + i*1.40), Inches(5.52), Inches(1.30), Inches(0.52))
    r.fill.background(); r.line.color.rgb = col; r.line.width = Pt(1.2)
    add_text(s, lbl, Inches(0.55 + i*1.40), Inches(5.54), Inches(1.30), Inches(0.25),
             size=10, bold=True, color=col, align=PP_ALIGN.CENTER)
    add_text(s, rng, Inches(0.55 + i*1.40), Inches(5.76), Inches(1.30), Inches(0.22),
             size=9, color=LTGRAY, align=PP_ALIGN.CENTER)

# right column: utility
add_rect(s, Inches(6.6), Inches(0.95), Inches(6.4), Inches(6.2), RGBColor(0x0E,0x11,0x22))
add_text(s, "Utility & Application",
         Inches(6.78), Inches(1.05), Inches(6.0), Inches(0.36),
         size=14, bold=True, color=ACCENT3)
bullet_box(s, [
    "Distribution page — side-by-side risk scores all episodes",
    "Dashboard KPI — season health at a glance",
    "Identifies which episodes are capacity-constrained vs complexity-heavy",
    "Triggers producer action: reassign shots, reduce scope, add vendor",
    "Slack alert fires when EFC exceeds cost_est × alert_threshold (default 1.2)",
    "Risk compounds across three independent dimensions — no single-point blindspot",
    "predicted_delay_days gives concrete delivery impact estimate",
    "Confidence risk links to Vendor Performance Score — end-to-end signal flow",
    "AT RISK or HIGH RISK → recommended intervention escalation to production",
    "Historical risk data accumulates per project — improves forecasting over seasons",
], Inches(6.78), Inches(1.48), Inches(6.0), Inches(5.5),
   dot_color=ACCENT3, size=12.5)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 7 — DATA IMPORT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, YELLOW)
section_header_bar(s, "DATA IMPORT PIPELINE", YELLOW)

# left: import types
add_text(s, "Importable Data Types",
         Inches(0.4), Inches(0.95), Inches(5.9), Inches(0.36),
         size=14, bold=True, color=YELLOW)
bullet_box(s, [
    "Shots  —  from EP production templates (Excel)",
    "Invoices  —  vendor, amount, status, date",
    "Assets  —  asset_name, description, est_budget",
    "Bid Compare  —  scene-level vendor bids",
], Inches(0.4), Inches(1.38), Inches(5.9), Inches(1.55),
   dot_color=YELLOW, size=13)

add_text(s, "Import Modes",
         Inches(0.4), Inches(3.00), Inches(5.9), Inches(0.36),
         size=14, bold=True, color=YELLOW)
modes = [
    ("Upsert",  "Add new rows + update existing (matched by scene_code + ep)"),
    ("Append",  "Add only new rows, skip exact duplicates"),
    ("Replace", "Delete all episode shots, insert fresh from file"),
]
kv_box(s, modes, Inches(0.4), Inches(3.42), Inches(5.9), Inches(1.25),
       key_color=YELLOW, val_color=LTGRAY, size=13)

add_text(s, "Auto-Detection Features",
         Inches(0.4), Inches(4.82), Inches(5.9), Inches(0.36),
         size=14, bold=True, color=YELLOW)
bullet_box(s, [
    "Header row auto-detected (≥ 4 non-empty cells threshold)",
    "Sheet auto-found by episode number in sheet name",
    "COL_MAP fuzzy column name matching (aliases table)",
    "LLM column mapping for unrecognized headers",
    "Cost field validation — $10M ceiling guard",
], Inches(0.4), Inches(5.25), Inches(5.9), Inches(1.95),
   dot_color=YELLOW, size=12.5)

# right: dry-run flow diagram (text-art)
add_rect(s, Inches(6.6), Inches(0.95), Inches(6.4), Inches(6.25), RGBColor(0x0E,0x11,0x22))
add_text(s, "Import Execution Flow",
         Inches(6.78), Inches(1.05), Inches(6.0), Inches(0.36),
         size=14, bold=True, color=YELLOW)

flow = [
    ("Upload Excel file", YELLOW),
    ("  ↓", MIDGRAY),
    ("Auto-detect header row & sheet", LTGRAY),
    ("  ↓", MIDGRAY),
    ("Fuzzy column name matching (COL_MAP)", LTGRAY),
    ("  ↓ (if unrecognized headers)", MIDGRAY),
    ("LLM-assisted column mapping", ACCENT3),
    ("  ↓", MIDGRAY),
    ("Validate: required fields, cost ceiling", LTGRAY),
    ("  ↓", MIDGRAY),
    ("Dry-run diff preview (new / updated / skipped)", YELLOW),
    ("  ↓ (user confirms)", MIDGRAY),
    ("Upsert / Append / Replace into .vfxdb", GREEN),
    ("  ↓", MIDGRAY),
    ("LLM enrichment (vfx_desc, shot_type, complexity)", ACCENT1),
    ("  ↓", MIDGRAY),
    ("Background job status polling (jobs/ API)", LTGRAY),
]
tb = s.shapes.add_textbox(Inches(6.78), Inches(1.48), Inches(5.9), Inches(5.5))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line, col in flow:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run(); run.text = line
    run.font.size = Pt(12); run.font.color.rgb = col

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 8 — USER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT2)
section_header_bar(s, "USER INTERFACE — 14 Screens", ACCENT2)

pages = [
    ("Home",           "/",               "Project list, create new show/season",             ACCENT1),
    ("Episode",        "/ep/101",         "Shots table — inline edit, LLM action buttons",    ACCENT2),
    ("Distribution",   "/distribution",   "Multi-episode side-by-side summary + risk scores", ACCENT3),
    ("Dashboard",      "/dashboard",      "Season KPIs — budget, vendors, types, complexity", GREEN),
    ("Vendor Tracker", "/vendortracker",  "Payments — award, paid, pending, tax, rebate",     YELLOW),
    ("Bid Compare",    "/bidcompare",     "Vendor bids by scene + LLM bid analysis",          ACCENT1),
    ("Invoice Log",    "/invoicelog",     "Invoice management — RECEIVED→APPROVED→PAID flow", ACCENT2),
    ("Optimizer",      "/optimizer",      "Lowest-cost assignment algorithm UI",              ACCENT3),
    ("Scenario",       "/scenario",       "Budget scenario modeling (conservative/optimistic)", GREEN),
    ("Assets",         "/assets",         "Asset registry — CG char, prop, environment",      YELLOW),
    ("Reports",        "/reports",        "PDF / Excel export builder",                       ACCENT1),
    ("Audit",          "/audit",          "Change history — filter by date, table, field",    ACCENT2),
    ("Settings",       "/settings",       "Vendor registry, auth, Slack webhook, thresholds", ACCENT3),
    ("Notes",          "/notes",          "VFX notes thread per episode",                     GREEN),
]

cols = 2
col_w = Inches(6.3)
row_h = Inches(0.43)
start_x = [Inches(0.25), Inches(6.65)]
start_y = Inches(1.02)

for i, (name, route, desc, col) in enumerate(pages):
    col_idx = i % cols
    row_idx = i // cols
    x = start_x[col_idx]
    y = start_y + row_idx * row_h
    # card bg
    add_rect(s, x, y, col_w, row_h - Inches(0.04), RGBColor(0x10,0x13,0x24))
    # route badge
    add_text(s, route,
             x + Inches(0.08), y + Inches(0.05), Inches(1.6), row_h - Inches(0.10),
             size=9.5, bold=True, color=col, align=PP_ALIGN.LEFT)
    # name
    add_text(s, name,
             x + Inches(1.65), y + Inches(0.03), Inches(1.4), row_h - Inches(0.06),
             size=12, bold=True, color=WHITE)
    # desc
    add_text(s, desc,
             x + Inches(3.05), y + Inches(0.04), Inches(3.15), row_h - Inches(0.08),
             size=10.5, color=LTGRAY)

# frontend stack note
add_rect(s, Inches(0.25), Inches(7.08), Inches(12.8), Inches(0.30), RGBColor(0x10,0x13,0x24))
add_text(s, "Frontend:  Vanilla JavaScript (Fetch API)  ·  Jinja2 templates  ·  Inline cell editing  ·  D3.js charts",
         Inches(0.35), Inches(7.09), Inches(12.5), Inches(0.28),
         size=10.5, color=LTGRAY)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 9 — AUDIT, SECURITY & COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, GREEN)
section_header_bar(s, "AUDIT, SECURITY & COMPLIANCE", GREEN)

# left: audit
add_rect(s, Inches(0.30), Inches(0.95), Inches(6.0), Inches(5.95), RGBColor(0x0E,0x11,0x22))
add_text(s, "Audit Trail (change_log)",
         Inches(0.50), Inches(1.05), Inches(5.6), Inches(0.36),
         size=14, bold=True, color=GREEN)
bullet_box(s, [
    "Every write to financial / key fields triggers a log entry",
    "Fields recorded: timestamp, table, row_id, field, old_value, new_value, user",
    "Queryable by: date range · table · field · user",
    "Used for: compliance review, error recovery, dispute resolution",
    "UI: /audit — filterable, sortable change history table",
    "LLM task 'audit_explain' generates plain-English explanation per entry",
], Inches(0.50), Inches(1.48), Inches(5.6), Inches(2.75),
   dot_color=GREEN, size=12.5)

add_text(s, "Authentication & Authorization",
         Inches(0.50), Inches(4.35), Inches(5.6), Inches(0.36),
         size=14, bold=True, color=GREEN)
bullet_box(s, [
    "Per-project password — bcrypt hash stored in projects.db",
    "Session cookie authentication (authenticated flag)",
    "Bearer token support — SHA-256 hash, for API / headless access",
    "Public routes only: /login, /logout, /static",
    "API token configurable in Settings — rotate any time",
], Inches(0.50), Inches(4.78), Inches(5.6), Inches(1.90),
   dot_color=GREEN, size=12.5)

# right: security + slack
add_rect(s, Inches(6.60), Inches(0.95), Inches(6.4), Inches(5.95), RGBColor(0x0E,0x11,0x22))
add_text(s, "Security Practices",
         Inches(6.78), Inches(1.05), Inches(6.0), Inches(0.36),
         size=14, bold=True, color=GREEN)
bullet_box(s, [
    "Parameterized SQL queries throughout — no string interpolation",
    "Jinja2 auto-escaping — XSS prevention in all templates",
    "No plaintext secrets in codebase — keys in llm_config.json (user-set)",
    "OWASP Top 10 conscious design (SQLi, XSS, auth, audit)",
    "WAL mode prevents DB corruption during concurrent writes",
], Inches(6.78), Inches(1.48), Inches(6.0), Inches(2.30),
   dot_color=GREEN, size=12.5)

add_text(s, "Slack Alerting (services/slack.py)",
         Inches(6.78), Inches(3.90), Inches(6.0), Inches(0.36),
         size=14, bold=True, color=GREEN)
bullet_box(s, [
    "Fires when EFC > cost_est × alert_threshold (default: 1.20)",
    "Alert payload: episode, scene, location, old EFC, new EFC, % over",
    "Webhook URL configurable in Settings (per project)",
    "Threshold tunable — production can set 1.1 (10%) or 1.3 (30%)",
    "Silent if Slack webhook not configured — safe default",
    "Utility: real-time cost escalation warnings to producers without login",
], Inches(6.78), Inches(4.32), Inches(6.0), Inches(2.42),
   dot_color=YELLOW, size=12.5)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 10 — BACKGROUND JOBS & ASYNC PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT1)
section_header_bar(s, "BACKGROUND JOBS & ASYNC PROCESSING", ACCENT1)

# left
add_rect(s, Inches(0.30), Inches(0.95), Inches(6.0), Inches(5.95), RGBColor(0x0E,0x11,0x22))
add_text(s, "Job System (jobs/queue.py + jobs/api.py)",
         Inches(0.50), Inches(1.05), Inches(5.65), Inches(0.36),
         size=14, bold=True, color=ACCENT1)
bullet_box(s, [
    "In-memory job state dict — thread-safe with Lock",
    "Background threading — non-blocking relative to Flask request",
    "REST polling endpoint: GET /api/jobs/<job_id>",
    "Status values: pending → running → done | error",
    "Result payload stored in job state on completion",
    "Auto-cleanup of completed jobs older than 24 hours",
    "job_id returned immediately in HTTP response (202 Accepted)",
    "UI polls /api/jobs/<id> every 2s until done",
], Inches(0.50), Inches(1.48), Inches(5.6), Inches(3.50),
   dot_color=ACCENT1, size=12.5)

add_text(s, "Examples of Async Tasks",
         Inches(0.50), Inches(5.07), Inches(5.6), Inches(0.36),
         size=14, bold=True, color=ACCENT1)
bullet_box(s, [
    "Shot import with LLM enrichment (vfx_desc + shot_type + complexity)",
    "Batch complexity rating across entire episode",
    "Budget gap analysis — find under-estimated or missing-bid scenes",
    "Risk forecast generation across all episodes",
    "Vendor performance score re-calculation",
], Inches(0.50), Inches(5.50), Inches(5.6), Inches(1.65),
   dot_color=ACCENT1, size=12.5)

# right: why async matters
add_rect(s, Inches(6.60), Inches(0.95), Inches(6.4), Inches(5.95), RGBColor(0x0E,0x11,0x22))
add_text(s, "Why Async Matters",
         Inches(6.78), Inches(1.05), Inches(6.0), Inches(0.36),
         size=14, bold=True, color=ACCENT1)
bullet_box(s, [
    "LLM calls take 2–15 seconds each — synchronous would block the UI",
    "Batch processing 50-shot episode import could take 5–10 minutes",
    "Flask's single-threaded dev server would time out on long LLM calls",
    "Background threads keep UI responsive during data-intensive operations",
    "Job status polling gives user real-time progress feedback",
    "Error state captured in job — no silent failures",
    "Jobs/ dir writes allow future persistence of job history",
    "Architecture supports future migration to Celery / RQ if needed",
], Inches(6.78), Inches(1.48), Inches(6.0), Inches(5.5),
   dot_color=ACCENT3, size=12.5)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 11 — REPORTS & EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, ACCENT2)
section_header_bar(s, "REPORTS & DATA EXPORT", ACCENT2)

add_rect(s, Inches(0.30), Inches(0.95), Inches(12.7), Inches(2.05), RGBColor(0x0E,0x11,0x22))
add_text(s, "Export Formats",
         Inches(0.50), Inches(1.05), Inches(12.3), Inches(0.36),
         size=14, bold=True, color=ACCENT2)

exports = [
    ("PDF (reportlab)",   "Season summary, vendor summary, risk report — formatted for producer distribution"),
    ("Excel (openpyxl)",  "Shot list per episode, vendor tracker, bid compare — preserves column formatting"),
    ("ForDistribution",   "apply_export_layout.py — specialized EP-by-EP delivery format for VFX supervisors"),
    ("CSV (Pandas-free)", "Direct SQLite → CSV — fast, no dependency on data science stack"),
    ("D3.js charts",      "data_graph.py generates JSON → rendered in browser as interactive charts"),
]
kv_box(s, exports, Inches(0.50), Inches(1.48), Inches(12.3), Inches(1.38),
       key_color=ACCENT2, val_color=LTGRAY, size=12.5)

# Template inventory
add_text(s, "Excel Templates (LAYOOUTLOOK/)",
         Inches(0.30), Inches(3.10), Inches(12.6), Inches(0.36),
         size=14, bold=True, color=ACCENT2)
templates = [
    ("TEMPLATE_EP.xlsx",        "88K",  "Episode shot list master template"),
    ("BIDCOMPARE.xlsx",         "101K", "Vendor bid comparison per scene"),
    ("VENDORTRACKER.xlsx",      "736K", "Vendor payment tracking (award/paid/pending)"),
    ("ASSET.xlsx",              "74K",  "Asset registry template"),
    ("BUDGET_SCENARIO.xlsx",    "66K",  "Conservative / optimistic budget scenarios"),
    ("distribution.xlsx",       "101K", "Season distribution EP-by-EP summary"),
    ("VENDORSEQCOMPARE.xlsx",   "86K",  "Vendor sequence-level comparison"),
],
tb = s.shapes.add_textbox(Inches(0.30), Inches(3.52), Inches(12.6), Inches(2.65))
tf = tb.text_frame; tf.word_wrap = True
first = True
for row in templates[0]:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    fname, size, desc = row
    r1 = p.add_run(); r1.text = f"{fname}  ({size})  "; r1.font.size = Pt(11.5)
    r1.font.bold = True; r1.font.color.rgb = ACCENT2; r1.font.name = "Courier New"
    r2 = p.add_run(); r2.text = desc; r2.font.size = Pt(11.5); r2.font.color.rgb = LTGRAY

# utility note
add_rect(s, Inches(0.30), Inches(6.20), Inches(12.7), Inches(1.00), RGBColor(0x0E,0x11,0x22))
bullet_box(s, [
    "Reports page (/reports) allows selecting report type, date range, and per-episode filters before export",
    "ForDistribution formatter (apply_export_layout.py) applies VFX supervisor-standard column ordering — invoked via subprocess",
], Inches(0.50), Inches(6.25), Inches(12.3), Inches(0.90),
   dot_color=ACCENT2, size=12.5)

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 12 — INSTALLATION & WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s); accent_bar(s, GREEN)
section_header_bar(s, "INSTALLATION & FULL SEASON WORKFLOW", GREEN)

# left: install
add_rect(s, Inches(0.30), Inches(0.95), Inches(5.8), Inches(3.45), RGBColor(0x0E,0x11,0x22))
add_text(s, "Installation",
         Inches(0.50), Inches(1.05), Inches(5.4), Inches(0.36),
         size=14, bold=True, color=GREEN)
kv_box(s, [
    ("Python",      "3.9+ required"),
    ("Flask",       "3.1.0"),
    ("openpyxl",    "3.1.5"),
    ("reportlab",   "4.2.5"),
    ("requests",    "2.32.3"),
    ("flask-caching","2.3.0 (optional)"),
    ("python-docx", "≥1.1.0 (optional)"),
], Inches(0.50), Inches(1.44), Inches(5.4), Inches(1.90),
   key_color=GREEN, val_color=LTGRAY, size=12)

add_text(s, "Quick Start",
         Inches(0.50), Inches(3.42), Inches(5.4), Inches(0.36),
         size=13, bold=True, color=GREEN)
code_lines = [
    "START.bat                 # Windows",
    "./START.sh                # macOS/Linux",
    "python launch.py          # cross-platform",
    "python launch.py --port 5001",
    "python launch.py --install  # deps only",
]
tb = s.shapes.add_textbox(Inches(0.50), Inches(3.82), Inches(5.4), Inches(1.20))
tf = tb.text_frame; tf.word_wrap = False
first = True
for line in code_lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    run = p.add_run(); run.text = line
    run.font.size = Pt(11); run.font.name = "Courier New"; run.font.color.rgb = GREEN

# config note
add_rect(s, Inches(0.30), Inches(5.05), Inches(5.8), Inches(1.55), RGBColor(0x0E,0x11,0x22))
add_text(s, "Configuration (llm_config.json)",
         Inches(0.50), Inches(5.12), Inches(5.4), Inches(0.32),
         size=12.5, bold=True, color=GREEN)
kv_box(s, [
    ("provider",     "ollama | claude | openai"),
    ("ollama_model", "qwen2.5:7b  (local, free)"),
    ("max_tokens",   "600  ·  temperature: 0.3"),
    ("alert_thresh", "1.20  (EFC 20% over EST → Slack)"),
], Inches(0.50), Inches(5.46), Inches(5.4), Inches(1.00),
   key_color=GREEN, val_color=LTGRAY, size=11.5)

# right: workflow
add_rect(s, Inches(6.35), Inches(0.95), Inches(6.65), Inches(6.25), RGBColor(0x0E,0x11,0x22))
add_text(s, "Full Season Cycle (12 Steps)",
         Inches(6.55), Inches(1.05), Inches(6.25), Inches(0.36),
         size=14, bold=True, color=GREEN)
steps = [
    ("1", "Launch app — python launch.py",                GREEN),
    ("2", "Home → New Project (name, season, ep range)",  LTGRAY),
    ("3", "Settings → Add vendors (rates, tax, rebates)", LTGRAY),
    ("4", "Settings → Set vendor capacity (shots/month)", LTGRAY),
    ("5", "Episode → Import Shots from Excel",            LTGRAY),
    ("6", "LLM enrichment: vfx_desc, type, complexity",   ACCENT1),
    ("7", "Bid Compare → Enter vendor bids per scene",    LTGRAY),
    ("8", "Optimizer → Run lowest-cost assignment",        ACCENT3),
    ("9", "Dashboard → Monitor season KPIs",              LTGRAY),
    ("10","Invoice Log → Import invoices as they arrive",  LTGRAY),
    ("11","Distribution → Review risk scores by episode",  ACCENT3),
    ("12","Reports → Export season summary / vendor PDF",  GREEN),
]
tb = s.shapes.add_textbox(Inches(6.55), Inches(1.48), Inches(6.25), Inches(5.5))
tf = tb.text_frame; tf.word_wrap = True
first = True
for num, text, col in steps:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    r1 = p.add_run(); r1.text = f"  {num.rjust(2)}.  "
    r1.font.size = Pt(12.5); r1.font.bold = True; r1.font.color.rgb = GREEN
    r2 = p.add_run(); r2.text = text
    r2.font.size = Pt(12.5); r2.font.color.rgb = col

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 13 — SUMMARY / CLOSING
# ═══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout)
slide_bg(s)
add_rect(s, 0, 0, W, Inches(0.08), ACCENT1)
add_rect(s, 0, Inches(0.08), W, Inches(0.04), ACCENT2)

add_text(s, "MACHIAVELLI_a004",
         Inches(0.6), Inches(0.80), Inches(12.0), Inches(0.75),
         size=38, bold=True, color=ACCENT1)

add_text(s, "System Capabilities at a Glance",
         Inches(0.6), Inches(1.52), Inches(11.0), Inches(0.45),
         size=20, color=WHITE)

divider(s, Inches(2.05), ACCENT2)

# two-column bullets
left_items = [
    "54 Python modules in clean Blueprint architecture",
    "12 route blueprints — one per business domain",
    "SQLite WAL per-project database (no server required)",
    "LLM abstraction — Ollama / Claude / OpenAI hot-swap",
    "21 task-specific LLM prompts with result caching",
    "Cost estimation anchored to project historical actuals",
    "Vendor Performance Score — bid consistency × invoice accuracy × edit efficiency",
]
right_items = [
    "Season Optimizer — lowest-cost CV-confidence vendor assignment",
    "3-factor Risk Forecast — capacity + complexity + confidence",
    "Flexible Excel importer — upsert / append / replace modes",
    "Background job queue — non-blocking LLM enrichment",
    "Full audit trail — every financial change logged",
    "Slack real-time alerts on EFC cost escalation",
    "PDF + Excel + D3.js reports — producer-ready output",
]

bullet_box(s, left_items,  Inches(0.35), Inches(2.18), Inches(6.2), Inches(3.80),
           dot_color=ACCENT1, size=12.5)
bullet_box(s, right_items, Inches(6.75), Inches(2.18), Inches(6.2), Inches(3.80),
           dot_color=ACCENT2, size=12.5)

divider(s, Inches(6.08), MIDGRAY)

add_text(s,
         "Production-grade VFX budget management — from first bid to final invoice, "
         "with AI-assisted analysis and real-time delivery risk visibility.",
         Inches(0.6), Inches(6.18), Inches(12.0), Inches(0.62),
         size=14, italic=True, color=LTGRAY, align=PP_ALIGN.CENTER)

# ─── SAVE ────────────────────────────────────────────────────────────────────
out_path = os.path.join(
    r"C:\Users\gderc\OneDrive\Documents\DATABASE\VFX_SW_S1\11_AUTOMATION\MACHIAVELLI_a004",
    "MACHIAVELLI_a004_Overview.pptx"
)
prs.save(out_path)
print(f"Saved: {out_path}")
