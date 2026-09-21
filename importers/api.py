"""
importers/api.py — Unified import API Blueprint.
POST /api/import/<type>         — live import
POST /api/import/<type>/preview — dry-run preview (no DB writes)
"""
from flask import Blueprint, request, jsonify
import core

bp = Blueprint('importers_api', __name__)

SUPPORTED = ('shots', 'assets', 'invoices')


@bp.route('/api/import/<import_type>', methods=['POST'])
@bp.route('/api/import/<import_type>/preview', methods=['POST'])
def import_data(import_type):
    """
    Unified import endpoint.
    /preview suffix → dry_run=True, returns diff only, no DB writes.
    Accepts multipart/form-data with:
      file: Excel file
      ep:   episode number
      mode: upsert | append | replace  (default: upsert)
      sheet: optional sheet name hint
    """
    if import_type not in SUPPORTED:
        return jsonify({'error': f'Unknown import type: {import_type}. Supported: {SUPPORTED}'}), 400

    r = core.require_project()
    if r: return jsonify({'error': 'no project'}), 400

    conn = core.get_db()
    if not conn: return jsonify({'error': 'No project DB'}), 400

    dry_run = request.path.endswith('/preview')
    ep      = request.form.get('ep', type=int)
    mode    = request.form.get('mode', 'upsert')
    sheet   = request.form.get('sheet', None)

    if not ep:
        return jsonify({'error': 'ep (episode number) required'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'file required'}), 400

    file_bytes = file.read()
    llm_client = core.get_llm_client() if import_type == 'shots' else None

    try:
        if import_type == 'shots':
            from importers.shots_importer import run
            result = run(file_bytes, ep, conn, mode=mode, sheet_hint=sheet,
                         llm_client=llm_client, dry_run=dry_run)

        elif import_type == 'assets':
            from importers.assets_importer import run
            result = run(file_bytes, ep, conn, mode=mode,
                         sheet_hint=sheet, dry_run=dry_run)

        elif import_type == 'invoices':
            from importers.invoices_importer import run
            result = run(file_bytes, ep, conn, mode=mode, dry_run=dry_run)

        if not dry_run:
            core.cache.clear()

        response = result.to_dict()
        response['dry_run'] = dry_run
        response['import_type'] = import_type
        response['ep'] = ep
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
