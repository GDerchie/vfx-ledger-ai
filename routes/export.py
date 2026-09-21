"""
routes/export.py — ForDistribution Excel layout Blueprint.

POST /api/export/apply_layout  — apply ForDistribution style to an uploaded or generated XLSX
"""
import io
import os
import sys
import subprocess
import tempfile
from flask import Blueprint, request, jsonify, send_file, session
import core

bp = Blueprint('export_bp', __name__)

# Path to apply_export_layout.py — lives next to app.py
_LAYOUT_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'apply_export_layout.py')
_PYTHON        = sys.executable


# ── apply ForDistribution layout to uploaded XLSX ─────────────────────────────

@bp.route('/api/export/apply_layout', methods=['POST'])
def apply_layout():
    """
    Apply the ForDistribution Excel style to an uploaded .xlsx file.
    Accepts:
      - multipart/form-data with file field 'file'      → apply to uploaded file
      - JSON { "source": "distribution" }               → generate + apply to season distribution
    Returns the styled XLSX as a file download.
    """
    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400

    source = request.args.get('source') or (request.json or {}).get('source', '')

    if source == 'distribution':
        # Generate the distribution XLSX first, then apply layout
        from routes.export import _generate_distribution_xlsx
        try:
            raw_buf = _generate_distribution_xlsx()
        except Exception as e:
            return jsonify({'error': f'Distribution export failed: {e}'}), 500
        in_bytes = raw_buf.read()
    elif 'file' in request.files:
        in_bytes = request.files['file'].read()
    else:
        return jsonify({'error': 'Provide file upload or source=distribution'}), 400

    # Write to temp file, run apply_layout.py, return result
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_in:
        tmp_in.write(in_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace('.xlsx', '_fmt.xlsx')
    try:
        result = subprocess.run(
            [_PYTHON, _LAYOUT_SCRIPT, tmp_in_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({'error': f'Layout script error: {result.stderr[:300]}'}), 500

        # apply_export_layout.py writes to same file or a _fmt variant
        out_path = tmp_out_path if os.path.exists(tmp_out_path) else tmp_in_path
        with open(out_path, 'rb') as f:
            out_bytes = f.read()

        proj_name = session.get('project_name', 'export')
        return send_file(
            io.BytesIO(out_bytes),
            as_attachment=True,
            download_name=f'{proj_name}_distribution_ForDist.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    finally:
        for p in [tmp_in_path, tmp_out_path]:
            try: os.unlink(p)
            except Exception: pass




def _generate_distribution_xlsx():
    """Build season distribution XLSX in-memory and return BytesIO."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    conn = core.get_db()
    if not conn:
        raise RuntimeError('No active project')

    eps = core.get_episodes()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Distribution'

    # Styles
    hdr_font    = Font(bold=True, color='FFFFFF', size=10)
    hdr_fill    = PatternFill('solid', fgColor='1A1D35')
    gold_fill   = PatternFill('solid', fgColor='F0B429')
    gold_font   = Font(bold=True, color='1A1D35', size=10)
    center      = Alignment(horizontal='center')
    right_align = Alignment(horizontal='right')
    thin        = Side(style='thin', color='2E3050')
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers = ['EP', 'STATUS', 'SCRIPT V', 'EDIT V', 'EST SHOTS',
               'EDIT SHOTS', 'EST BUDGET', 'EFC BUDGET', 'VARIANCE',
               'RISK STATUS', 'NOTES']
    ws.append(headers)
    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font      = hdr_font
        cell.fill      = hdr_fill
        cell.alignment = center
        cell.border    = border

    row_num = 2
    for ep in eps:
        r    = conn.execute(
            "SELECT COUNT(CASE WHEN omit=0 AND shot_est>0 THEN 1 END) as est_shots, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(edit_count,0) ELSE 0 END) as edit_shots, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) as est, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) as efc "
            "FROM shots WHERE ep=?", (ep,)
        ).fetchone()
        meta = conn.execute('SELECT status, script_v, edit_v, notes FROM ep_meta WHERE ep=?', (ep,)).fetchone()
        risk = core.compute_ep_risk(conn, ep)
        aa   = conn.execute(
            "SELECT SUM(CASE WHEN omit=0 THEN COALESCE(est_budget,0) ELSE 0 END) as ae, "
            "SUM(CASE WHEN omit=0 THEN COALESCE(actual_spend,0) ELSE 0 END) as af "
            "FROM assets WHERE ep=?", (ep,)
        ).fetchone()
        se = r['est'] or 0; sf = r['efc'] or 0
        ae = (aa['ae'] or 0) if aa else 0; af = (aa['af'] or 0) if aa else 0

        row_data = [
            f'EP{ep}',
            meta['status']   if meta else '',
            meta['script_v'] if meta else '',
            meta['edit_v']   if meta else '',
            r['est_shots'] or 0,
            r['edit_shots'] or 0,
            se + ae,
            sf + af,
            (sf + af) - (se + ae),
            risk['status'],
            meta['notes']    if meta else '',
        ]
        ws.append(row_data)
        for col_idx, _ in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_idx)
            cell.border    = border
            if col_idx in (7, 8, 9):
                cell.number_format = '#,##0'
                cell.alignment     = right_align
            elif col_idx in (5, 6):
                cell.alignment = right_align
        row_num += 1

    # Totals row
    est_col = get_column_letter(7); efc_col = get_column_letter(8); var_col = get_column_letter(9)
    ws.append([
        'TOTAL', '', '', '', '', '',
        f'=SUM({est_col}2:{est_col}{row_num-1})',
        f'=SUM({efc_col}2:{efc_col}{row_num-1})',
        f'=SUM({var_col}2:{var_col}{row_num-1})',
        '', '',
    ])
    for col_idx in range(1, 12):
        cell = ws.cell(row=row_num, column=col_idx)
        cell.font   = gold_font
        cell.fill   = gold_fill
        cell.border = border
        if col_idx in (7, 8, 9):
            cell.number_format = '#,##0'
            cell.alignment     = right_align

    # Column widths
    widths = [6, 12, 9, 9, 10, 10, 16, 16, 14, 12, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    conn.close()
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


