"""
llm/cache.py — LLM call caching and cost tracking.
Stores results keyed by (task, content_hash) in ai_calls table.
"""
import hashlib
import json
import sqlite3
import os
from datetime import datetime

# Token cost estimates per 1K tokens (USD)
COST_PER_1K = {
    'claude': {'in': 0.00025, 'out': 0.00125},   # haiku
    'openai': {'in': 0.00015, 'out': 0.0006},    # gpt-4o-mini
    'ollama': {'in': 0.0, 'out': 0.0},            # local
}

_cache_db_path = None


def init_cache(db_path: str):
    """Initialize the cache database."""
    global _cache_db_path
    _cache_db_path = db_path
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS ai_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        provider TEXT,
        model TEXT,
        tokens_in INTEGER DEFAULT 0,
        tokens_out INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0,
        result TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(task, content_hash)
    )''')
    conn.commit()
    conn.close()


def _hash_context(task: str, ctx: dict) -> str:
    payload = json.dumps({'task': task, 'ctx': ctx}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def get_cached(task: str, ctx: dict) -> str | None:
    """Return cached LLM result string, or None if not cached."""
    if not _cache_db_path:
        return None
    h = _hash_context(task, ctx)
    try:
        conn = sqlite3.connect(_cache_db_path)
        row = conn.execute(
            'SELECT result FROM ai_calls WHERE task=? AND content_hash=?', (task, h)
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def store_result(task: str, ctx: dict, result: str,
                 provider: str = '', model: str = '',
                 tokens_in: int = 0, tokens_out: int = 0):
    """Store an LLM result in the cache."""
    if not _cache_db_path:
        return
    h = _hash_context(task, ctx)
    rates = COST_PER_1K.get(provider, COST_PER_1K['ollama'])
    cost = (tokens_in / 1000 * rates['in']) + (tokens_out / 1000 * rates['out'])
    try:
        conn = sqlite3.connect(_cache_db_path)
        conn.execute(
            '''INSERT OR REPLACE INTO ai_calls
               (task, content_hash, provider, model, tokens_in, tokens_out, cost_usd, result, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (task, h, provider, model, tokens_in, tokens_out, cost, result,
             datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_usage_stats(db_path: str | None = None) -> dict:
    """Return usage statistics for the settings page."""
    path = db_path or _cache_db_path
    if not path:
        return {}
    try:
        conn = sqlite3.connect(path)
        rows = conn.execute(
            '''SELECT provider, COUNT(*) as calls,
               COALESCE(SUM(tokens_in),0) as tok_in,
               COALESCE(SUM(tokens_out),0) as tok_out,
               COALESCE(SUM(cost_usd),0) as cost
               FROM ai_calls GROUP BY provider'''
        ).fetchall()
        conn.close()
        return {r[0]: {'calls': r[1], 'tokens_in': r[2], 'tokens_out': r[3], 'cost_usd': round(r[4], 4)}
                for r in rows}
    except Exception:
        return {}
