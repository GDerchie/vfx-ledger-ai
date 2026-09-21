"""
routes/reports.py — Report builder Blueprint.
GET  /reports              — reports page
POST /api/reports/generate — generate a report (JSON or PDF)
GET  /api/reports/types    — list available report types
"""
import io
import json
from flask import Blueprint, render_template, request, jsonify, send_file, Response, stream_with_context
import core

bp = Blueprint('reports', __name__)


@bp.route('/reports')
def reports_page():
    r = core.require_project()
    if r: return r
    return render_template('reports.html')


@bp.route('/api/reports/types', methods=['GET'])
def report_types():
    return jsonify([
        {
            'id':          'season_summary',
            'name':        'Season Summary',
            'description': 'Full season KPIs, per-episode budget table, vendor breakdown, risk scores',
            'formats':     ['json', 'pdf'],
        },
        {
            'id':          'ep_status',
            'name':        'Episode Status Report',
            'description': 'Single-episode detail: shot list, type breakdown, vendor awards',
            'formats':     ['json', 'pdf'],
            'params':      ['ep'],
        },
        {
            'id':          'vendor_performance',
            'name':        'Vendor Performance Report',
            'description': 'Vendor-centric view: awards, invoices, capacity, performance scores',
            'formats':     ['json', 'pdf'],
        },
    ])


@bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """
    Generate a report.
    Body: { type, format, ep (optional), narrative (bool, default false) }
    format='json'  → returns JSON data
    format='pdf'   → returns PDF file download
    narrative=true → includes LLM-generated summary paragraph
    """
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400
    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project'}), 400

    d           = request.json or {}
    report_type = d.get('type', 'season_summary')
    fmt         = d.get('format', 'json')
    ep_param    = d.get('ep')
    narrative   = d.get('narrative', False)

    try:
        data = _build_report_data(conn, report_type, ep_param)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

    # Optional LLM narrative
    if narrative:
        try:
            data['narrative'] = _generate_narrative(data, report_type)
        except Exception as e:
            data['narrative'] = f'(narrative unavailable: {e})'

    conn.close()

    if fmt == 'json':
        return jsonify(data)

    if fmt == 'pdf':
        try:
            pdf_buf = _build_pdf(data, report_type, ep_param)
            filename = {
                'season_summary':      'season_summary_report.pdf',
                'ep_status':           f'ep{ep_param}_status_report.pdf',
                'vendor_performance':  'vendor_performance_report.pdf',
            }.get(report_type, 'report.pdf')
            return send_file(pdf_buf, as_attachment=True,
                             download_name=filename,
                             mimetype='application/pdf')
        except ImportError:
            return jsonify({'error': 'ReportLab not installed — JSON format only'}), 400
        except Exception as e:
            return jsonify({'error': f'PDF generation failed: {e}'}), 500

    return jsonify({'error': f'Unknown format: {fmt}'}), 400


# ── Report data builders ──────────────────────────────────────────────────────

def _build_report_data(conn, report_type: str, ep_param=None) -> dict:
    eps = core.get_episodes()

    if report_type == 'season_summary':
        return _season_summary_data(conn, eps)
    elif report_type == 'ep_status':
        if not ep_param:
            raise ValueError('ep parameter required for ep_status report')
        return _ep_status_data(conn, int(ep_param))
    elif report_type == 'vendor_performance':
        return _vendor_perf_data(conn)
    else:
        raise ValueError(f'Unknown report type: {report_type}')


def _season_summary_data(conn, eps: list) -> dict:
    # Season KPIs
    agg = conn.execute('''
        SELECT COUNT(CASE WHEN omit=0 THEN 1 END) as total_shots,
               SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) as total_est,
               SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) as total_efc,
               COUNT(DISTINCT CASE WHEN omit=0 AND award_vendor IS NOT NULL
                     AND award_vendor!='' THEN award_vendor END) as vendor_count
        FROM shots
    ''').fetchone()

    # Per-EP rows
    ep_rows = []
    for ep in eps:
        r    = conn.execute(
            "SELECT COUNT(CASE WHEN omit=0 THEN 1 END) as shots, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) as est, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) as efc "
            "FROM shots WHERE ep=?", (ep,)).fetchone()
        meta = conn.execute('SELECT status, script_v, edit_v FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        risk = core.compute_ep_risk(conn, ep)
        ep_rows.append({
            'ep':       ep,
            'status':   meta['status']   if meta else '',
            'script_v': meta['script_v'] if meta else '',
            'edit_v':   meta['edit_v']   if meta else '',
            'shots':    r['shots'] or 0,
            'est':      r['est']   or 0,
            'efc':      r['efc']   or 0,
            'variance': (r['efc'] or 0) - (r['est'] or 0),
            'risk_status': risk['status'],
            'risk_score':  risk['risk_score'],
        })

    # Top vendors
    vendors = conn.execute('''
        SELECT award_vendor as vendor, COUNT(*) as shots,
               SUM(COALESCE(cost_est,0)) as est,
               SUM(COALESCE(efc,0)) as efc
        FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!=''
        GROUP BY award_vendor ORDER BY efc DESC LIMIT 12
    ''').fetchall()

    # Type breakdown
    types = conn.execute('''
        SELECT shot_type, COUNT(*) as shots,
               SUM(COALESCE(cost_est,0)) as est
        FROM shots WHERE omit=0 AND shot_type IS NOT NULL AND shot_type!=''
        GROUP BY shot_type ORDER BY shots DESC
    ''').fetchall()

    total_est = agg['total_est'] or 0
    total_efc = agg['total_efc'] or 0
    return {
        'report_type': 'season_summary',
        'kpis': {
            'total_shots':   agg['total_shots']  or 0,
            'vendor_count':  agg['vendor_count'] or 0,
            'total_est':     total_est,
            'total_efc':     total_efc,
            'variance':      total_efc - total_est,
            'variance_pct':  round((total_efc / total_est - 1) * 100, 1) if total_est else 0,
        },
        'episodes': ep_rows,
        'vendors':  [dict(r) for r in vendors],
        'types':    [dict(r) for r in types],
    }


def _ep_status_data(conn, ep: int) -> dict:
    shots = conn.execute(
        'SELECT * FROM shots WHERE ep=? AND omit=0 ORDER BY shot_num', (ep,)
    ).fetchall()
    meta  = conn.execute('SELECT * FROM ep_meta WHERE ep=?', (ep,)).fetchone()
    risk  = core.compute_ep_risk(conn, ep)

    total_est = sum(s['cost_est'] or 0 for s in shots)
    total_efc = sum(s['efc']      or 0 for s in shots)

    # Vendor awards
    vendor_rows = conn.execute('''
        SELECT award_vendor, COUNT(*) as shots,
               SUM(COALESCE(cost_est,0)) as est,
               SUM(COALESCE(efc,0)) as efc
        FROM shots WHERE ep=? AND omit=0 AND award_vendor IS NOT NULL AND award_vendor!=''
        GROUP BY award_vendor ORDER BY efc DESC
    ''', (ep,)).fetchall()

    # Type breakdown
    type_rows = conn.execute('''
        SELECT shot_type, COUNT(*) as shots, SUM(COALESCE(cost_est,0)) as est
        FROM shots WHERE ep=? AND omit=0 AND shot_type IS NOT NULL AND shot_type!=''
        GROUP BY shot_type ORDER BY shots DESC
    ''', (ep,)).fetchall()

    return {
        'report_type': 'ep_status',
        'ep':          ep,
        'meta': {
            'status':   meta['status']   if meta else '',
            'script_v': meta['script_v'] if meta else '',
            'edit_v':   meta['edit_v']   if meta else '',
            'notes':    meta['notes']    if meta else '',
        },
        'kpis': {
            'total_shots': len(shots),
            'total_est':   total_est,
            'total_efc':   total_efc,
            'variance':    total_efc - total_est,
        },
        'risk':    risk,
        'vendors': [dict(r) for r in vendor_rows],
        'types':   [dict(r) for r in type_rows],
        'shots': [{
            'scene_code':   s['scene_code'],
            'shot_type':    s['shot_type'],
            'complexity':   s['complexity'],
            'award_vendor': s['award_vendor'],
            'cost_est':     s['cost_est'],
            'efc':          s['efc'],
            'vfx_desc':     (s['vfx_desc'] or '')[:120],
        } for s in shots],
    }


def _vendor_perf_data(conn) -> dict:
    from services.vendors_svc import get_vendor_loads, get_vendor_perf_scores
    loads       = get_vendor_loads(conn)
    scores_list = get_vendor_perf_scores(conn)
    scores      = {r['vendor']: r for r in scores_list}

    # Award totals from shots
    award_rows = conn.execute('''
        SELECT award_vendor as vendor, COUNT(*) as shots,
               SUM(COALESCE(cost_est,0)) as est,
               SUM(COALESCE(efc,0)) as efc
        FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!=''
        GROUP BY award_vendor ORDER BY efc DESC
    ''').fetchall()

    # Invoice totals
    inv_rows = conn.execute('''
        SELECT vendor, COUNT(*) as invoices,
               SUM(COALESCE(amount,0)) as total_invoiced,
               SUM(CASE WHEN UPPER(status)='PAID' THEN COALESCE(amount,0) ELSE 0 END) as paid
        FROM invoice_log GROUP BY vendor
    ''').fetchall()
    inv_map = {r['vendor'].upper(): dict(r) for r in inv_rows}

    vendors = []
    for r in award_rows:
        v     = r['vendor']
        load  = loads.get(v, {})
        score = scores.get(v.upper(), {})
        inv   = inv_map.get(v.upper(), {})
        vendors.append({
            'vendor':      v,
            'shots':       r['shots'],
            'est':         r['est'],
            'efc':         r['efc'],
            'utilization': load.get('utilization'),
            'perf_score':  score.get('composite_score'),
            'invoices':    inv.get('invoices', 0),
            'invoiced':    inv.get('total_invoiced', 0),
            'paid':        inv.get('paid', 0),
        })

    return {
        'report_type': 'vendor_performance',
        'vendors':     vendors,
    }


# ── LLM narrative generator ───────────────────────────────────────────────────

def _generate_narrative(data: dict, report_type: str) -> str:
    """Generate a short LLM narrative for the report cover section."""
    import llm as llm_module

    if report_type == 'season_summary':
        kpis = data.get('kpis', {})
        eps  = data.get('episodes', [])
        ctx = {
            'total_shots': kpis.get('total_shots', 0),
            'total_est':   f"{kpis.get('total_est', 0):,.0f}",
            'total_efc':   f"{kpis.get('total_efc', 0):,.0f}",
            'variance':    f"{kpis.get('variance', 0):+,.0f}",
            'ep_breakdown': '\n'.join(
                f"  EP{e['ep']} {e['status']} EST=${e['est']:,.0f} EFC=${e['efc']:,.0f} {e['risk_status']}"
                for e in eps
            ),
            'vendor_breakdown': '\n'.join(
                f"  {v['vendor']}: {v['shots']} shots EFC=${v['efc']:,.0f}"
                for v in data.get('vendors', [])[:5]
            ),
        }
        prompt = llm_module.build_prompt('season_risk', ctx)

    elif report_type == 'ep_status':
        kpis = data.get('kpis', {})
        risk = data.get('risk',  {})
        ctx = {
            'ep':          data.get('ep', ''),
            'total_shots': kpis.get('total_shots', 0),
            'total_est':   f"{kpis.get('total_est', 0):,.0f}",
            'total_efc':   f"{kpis.get('total_efc', 0):,.0f}",
            'variance':    f"{kpis.get('variance', 0):+,.0f}",
            'status':      data.get('meta', {}).get('status', ''),
            'script_v':    data.get('meta', {}).get('script_v', ''),
            'edit_v':      data.get('meta', {}).get('edit_v', ''),
            'est_shots':   kpis.get('total_shots', 0),
            'edit_shots':  kpis.get('total_shots', 0),
            'est_budget':  f"{kpis.get('total_est', 0):,.0f}",
            'efc_budget':  f"{kpis.get('total_efc', 0):,.0f}",
            'reduction_line': '',
        }
        prompt = llm_module.build_prompt('ep_narrative', ctx)

    else:
        return ''

    if not prompt:
        return ''

    client = core.get_llm_client()
    return ''.join(client.stream(prompt))


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(data: dict, report_type: str, ep_param=None) -> io.BytesIO:
    """Build a PDF report using ReportLab. Returns BytesIO buffer."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    if report_type in ('season_summary', 'vendor_performance'):
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                                leftMargin=12*mm, rightMargin=12*mm,
                                topMargin=12*mm, bottomMargin=12*mm)
    else:
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=14*mm, rightMargin=14*mm,
                                topMargin=14*mm, bottomMargin=14*mm)

    styles = getSampleStyleSheet()
    C_BG   = colors.HexColor('#07080f')
    C_GOLD = colors.HexColor('#f0b429')
    C_TEXT = colors.HexColor('#d0d8f0')
    C_DIM  = colors.HexColor('#4a5080')
    C_RED  = colors.HexColor('#e05252')
    C_GRN  = colors.HexColor('#52c46a')

    def P(text, size=9, color=C_TEXT, bold=False, align='LEFT'):
        al = {'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(align, 0)
        st = ParagraphStyle('x', fontSize=size, textColor=color,
                            fontName='Helvetica-Bold' if bold else 'Helvetica',
                            alignment=al, leading=size * 1.4)
        return Paragraph(str(text), st)

    def money(v):
        try:
            return f'${float(v):,.0f}'
        except Exception:
            return str(v) if v else '—'

    def tbl(rows, col_widths, row_heights=None):
        t = Table(rows, colWidths=col_widths, rowHeights=row_heights)
        t.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),   colors.HexColor('#10121e')),
            ('TEXTCOLOR',   (0, 0), (-1, 0),   C_GOLD),
            ('FONTNAME',    (0, 0), (-1, 0),   'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0),   7.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0d0e1a'), colors.HexColor('#10121e')]),
            ('TEXTCOLOR',   (0, 1), (-1, -1),  C_TEXT),
            ('FONTNAME',    (0, 1), (-1, -1),  'Helvetica'),
            ('FONTSIZE',    (0, 1), (-1, -1),  7.5),
            ('GRID',        (0, 0), (-1, -1),  0.3, colors.HexColor('#1e2240')),
            ('TOPPADDING',  (0, 0), (-1, -1),  3),
            ('BOTTOMPADDING',(0,0), (-1, -1),  3),
            ('LEFTPADDING', (0, 0), (-1, -1),  5),
        ]))
        return t

    story = []

    if report_type == 'season_summary':
        kpis = data.get('kpis', {})
        story.append(P('SEASON SUMMARY REPORT', size=14, color=C_GOLD, bold=True))
        story.append(Spacer(1, 4*mm))
        if data.get('narrative'):
            story.append(P(data['narrative'], size=8.5, color=C_TEXT))
            story.append(Spacer(1, 4*mm))

        # KPI row
        kpi_rows = [[P('SHOTS', 7, C_DIM, bold=True),  P('EST BUDGET', 7, C_DIM, bold=True),
                      P('EFC',   7, C_DIM, bold=True),  P('VARIANCE',  7, C_DIM, bold=True),
                      P('VENDORS', 7, C_DIM, bold=True)],
                    [P(str(kpis.get('total_shots', 0)), 11, C_TEXT, bold=True),
                      P(money(kpis.get('total_est', 0)),  11, C_GOLD, bold=True),
                      P(money(kpis.get('total_efc', 0)),  11, C_TEXT, bold=True),
                      P(money(kpis.get('variance', 0)),   11, C_RED if (kpis.get('variance', 0) or 0) > 0 else C_GRN, bold=True),
                      P(str(kpis.get('vendor_count', 0)), 11, C_TEXT, bold=True)]]
        w = doc.width / 5
        story.append(tbl(kpi_rows, [w]*5, [7*mm, 10*mm]))
        story.append(Spacer(1, 4*mm))

        # Episode table
        story.append(P('EPISODE BREAKDOWN', 7, C_DIM, bold=True))
        story.append(Spacer(1, 1*mm))
        ep_header = [P(h, 7, C_GOLD, bold=True) for h in
                     ['EP', 'STATUS', 'SHOTS', 'EST', 'EFC', 'VARIANCE', 'RISK']]
        ep_data   = [ep_header]
        for e in data.get('episodes', []):
            var = e.get('variance', 0) or 0
            ep_data.append([
                P(str(e['ep']), 8),
                P(e.get('status',''), 7, C_DIM),
                P(str(e.get('shots',0)), 8, align='CENTER'),
                P(money(e.get('est',0)), 8),
                P(money(e.get('efc',0)), 8),
                P(money(var), 8, C_RED if var > 0 else C_GRN),
                P(e.get('risk_status',''), 7, C_RED if 'RISK' in e.get('risk_status','') else C_TEXT),
            ])
        cw = [15*mm, 35*mm, 18*mm, 42*mm, 42*mm, 42*mm, 28*mm]
        story.append(tbl(ep_data, cw))
        story.append(Spacer(1, 4*mm))

        # Vendor table
        story.append(P('TOP VENDORS BY EFC', 7, C_DIM, bold=True))
        story.append(Spacer(1, 1*mm))
        v_header = [P(h, 7, C_GOLD, bold=True) for h in ['VENDOR', 'SHOTS', 'EST', 'EFC']]
        v_data   = [v_header]
        for v in data.get('vendors', []):
            v_data.append([P(v.get('vendor',''), 8), P(str(v.get('shots',0)), 8, align='CENTER'),
                           P(money(v.get('est',0)), 8), P(money(v.get('efc',0)), 8)])
        story.append(tbl(v_data, [80*mm, 20*mm, 50*mm, 50*mm]))

    elif report_type == 'ep_status':
        ep   = data.get('ep', '')
        meta = data.get('meta', {})
        kpis = data.get('kpis', {})
        risk = data.get('risk', {})

        story.append(P(f'EP{ep} — STATUS REPORT', 13, C_GOLD, bold=True))
        story.append(P(f"{meta.get('status','')}  |  Script {meta.get('script_v','')}  |  Edit {meta.get('edit_v','')}", 8, C_DIM))
        story.append(Spacer(1, 3*mm))
        if data.get('narrative'):
            story.append(P(data['narrative'], size=8.5, color=C_TEXT))
            story.append(Spacer(1, 3*mm))

        # KPI strip
        kpi_rows = [[P('SHOTS', 7, C_DIM, bold=True), P('EST', 7, C_DIM, bold=True),
                      P('EFC',  7, C_DIM, bold=True), P('VARIANCE', 7, C_DIM, bold=True),
                      P('RISK', 7, C_DIM, bold=True)],
                    [P(str(kpis.get('total_shots', 0)), 11, C_TEXT, bold=True),
                      P(money(kpis.get('total_est', 0)),  11, C_GOLD, bold=True),
                      P(money(kpis.get('total_efc', 0)),  11, C_TEXT, bold=True),
                      P(money(kpis.get('variance',  0)),  11, C_RED  if (kpis.get('variance',0) or 0)>0 else C_GRN, bold=True),
                      P(risk.get('status', ''), 11,
                        C_RED if 'RISK' in risk.get('status','') else C_GRN, bold=True)]]
        w = doc.width / 5
        story.append(tbl(kpi_rows, [w]*5, [7*mm, 10*mm]))
        story.append(Spacer(1, 3*mm))

        # Shot table
        story.append(P('SHOT BREAKDOWN', 7, C_DIM, bold=True))
        story.append(Spacer(1, 1*mm))
        sh_h   = [P(h, 7, C_GOLD, bold=True) for h in ['SC', 'TYPE', 'CPLX', 'VENDOR', 'EST', 'EFC', 'VFX DESC']]
        sh_data = [sh_h]
        for s in data.get('shots', []):
            var = (s.get('efc') or 0) - (s.get('cost_est') or 0)
            sh_data.append([
                P(str(s.get('scene_code','')), 7),
                P(str(s.get('shot_type','')), 7),
                P(str(s.get('complexity','')), 7),
                P(str(s.get('award_vendor','')), 7),
                P(money(s.get('cost_est',0)), 7),
                P(money(s.get('efc',0)), 7, C_RED if var > 0 else C_TEXT),
                P((s.get('vfx_desc') or '')[:80], 7, C_DIM),
            ])
        story.append(tbl(sh_data, [14*mm, 18*mm, 14*mm, 28*mm, 22*mm, 22*mm, 68*mm]))

    elif report_type == 'vendor_performance':
        story.append(P('VENDOR PERFORMANCE REPORT', 13, C_GOLD, bold=True))
        story.append(Spacer(1, 4*mm))
        v_h = [P(h, 7, C_GOLD, bold=True) for h in
               ['VENDOR', 'SHOTS', 'EST', 'EFC', 'UTIL%', 'PERF', 'INVOICES', 'INVOICED', 'PAID']]
        v_data = [v_h]
        for v in data.get('vendors', []):
            util = v.get('utilization')
            util_s = f"{util*100:.0f}%" if util is not None else '—'
            perf   = v.get('perf_score')
            perf_s = f"{perf:.2f}" if perf is not None else '—'
            v_data.append([
                P(v.get('vendor',''), 7),
                P(str(v.get('shots', 0)), 7, align='CENTER'),
                P(money(v.get('est', 0)),      7),
                P(money(v.get('efc', 0)),      7),
                P(util_s, 7, C_RED if util and util > 1.0 else C_TEXT),
                P(perf_s, 7),
                P(str(v.get('invoices', 0)), 7, align='CENTER'),
                P(money(v.get('invoiced', 0)), 7),
                P(money(v.get('paid', 0)),     7),
            ])
        cw = [40*mm, 16*mm, 30*mm, 30*mm, 16*mm, 16*mm, 20*mm, 30*mm, 30*mm]
        story.append(tbl(v_data, cw))

    doc.build(story)
    buf.seek(0)
    return buf
