"""
jobs/api.py — Flask Blueprint for job status API.
Register this blueprint in app.py to enable job status polling.
"""
from flask import Blueprint, jsonify
from jobs.queue import get_status, cleanup_old_jobs

bp = Blueprint('jobs_api', __name__)


@bp.route('/api/jobs/<job_id>', methods=['GET'])
def job_status(job_id):
    """Poll job status. Frontend calls this every 500ms."""
    state = get_status(job_id)
    if state is None:
        return jsonify({'status': 'not_found'}), 404
    return jsonify(state)


@bp.route('/api/jobs/cleanup', methods=['POST'])
def cleanup():
    cleanup_old_jobs()
    return jsonify({'ok': True})
