"""
jobs/queue.py — In-process background job queue for long-running LLM tasks.
No Redis or Celery needed — uses Python threading.
Job state is written to the Jobs/ directory as JSON files.
"""
import threading
import json
import os
import uuid
from datetime import datetime

# On Windows, Jobs/ and jobs/ resolve to the same directory.
# Job state files go in a dedicated subfolder to avoid collision.
_BASE = os.path.dirname(os.path.dirname(__file__))
JOBS_DIR = os.path.join(_BASE, 'job_states')
os.makedirs(JOBS_DIR, exist_ok=True)

_lock = threading.Lock()
_running: dict[str, threading.Thread] = {}


def _job_path(job_id: str) -> str:
    return os.path.join(JOBS_DIR, f'{job_id}.json')


def _write_state(job_id: str, state: dict):
    with open(_job_path(job_id), 'w', encoding='utf-8') as f:
        json.dump(state, f)


def submit(task_fn, args: tuple = (), kwargs: dict = None, label: str = '') -> str:
    """
    Submit a function to run in a background thread.
    Returns a job_id. The function receives (job_id, *args, **kwargs).
    It should call update_progress(job_id, ...) and finish with complete(job_id, ...).
    """
    job_id = str(uuid.uuid4())[:8]
    _write_state(job_id, {
        'id': job_id, 'label': label, 'status': 'pending',
        'progress': 0, 'result': None, 'error': None,
        'created_at': datetime.utcnow().isoformat(),
    })

    def _run():
        try:
            update_progress(job_id, 5, 'running')
            task_fn(job_id, *(args or ()), **(kwargs or {}))
        except Exception as e:
            _write_state(job_id, {**_read_state(job_id), 'status': 'error', 'error': str(e)})
        finally:
            with _lock:
                _running.pop(job_id, None)

    t = threading.Thread(target=_run, daemon=True)
    with _lock:
        _running[job_id] = t
    t.start()
    return job_id


def update_progress(job_id: str, progress: int, status: str = 'running', partial: str = ''):
    state = _read_state(job_id)
    state.update({'status': status, 'progress': progress, 'partial': partial})
    _write_state(job_id, state)


def complete(job_id: str, result):
    state = _read_state(job_id)
    state.update({'status': 'done', 'progress': 100, 'result': result,
                  'completed_at': datetime.utcnow().isoformat()})
    _write_state(job_id, state)


def get_status(job_id: str) -> dict | None:
    return _read_state(job_id)


def _read_state(job_id: str) -> dict:
    try:
        with open(_job_path(job_id), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'id': job_id, 'status': 'unknown'}


def cleanup_old_jobs(max_age_hours: int = 24):
    """Remove job files older than max_age_hours."""
    import time
    cutoff = time.time() - max_age_hours * 3600
    for fname in os.listdir(JOBS_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(JOBS_DIR, fname)
        try:
            if os.path.getmtime(fpath) < cutoff:
                os.remove(fpath)
        except Exception:
            pass
