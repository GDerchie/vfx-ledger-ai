"""
services/llm_helpers.py — Shared LLM streaming + cache-aware completion helpers.

Eliminates the duplicated queue/thread/generate pattern that appears in
budget_gap_analysis, season_risk, and llm_stream_route.
"""
import queue
import threading
import json
from flask import Response, stream_with_context

import llm.cache as llm_cache
from llm.parsers import parse_with_retry as _parse_with_retry


# ---------------------------------------------------------------------------
# Streaming SSE response
# ---------------------------------------------------------------------------

def stream_llm(prompt: str, client, cache_task: str = '', cache_ctx: dict = None) -> Response:
    """
    Stream LLM output as Server-Sent Events.
    Accumulates the full text and stores to cache on completion.

    Returns a Flask Response with mimetype='text/event-stream'.
    """
    q = queue.Queue()
    SENTINEL = object()

    def _producer():
        try:
            for chunk in client.stream(prompt):
                q.put(chunk)
        except Exception as e:
            q.put({'__error__': str(e)})
        finally:
            q.put(SENTINEL)

    threading.Thread(target=_producer, daemon=True).start()

    def _generate():
        accumulated = []
        while True:
            try:
                item = q.get(timeout=120)
            except queue.Empty:
                yield f"data: {json.dumps({'error': 'LLM timeout'})}\n\n"
                yield 'data: [DONE]\n\n'
                break
            if item is SENTINEL:
                # Cache the completed result
                if cache_task and cache_ctx is not None:
                    try:
                        llm_cache.store_result(
                            cache_task, cache_ctx, ''.join(accumulated),
                            provider=client.config.get('provider', ''),
                            model=client.config.get(
                                f"{client.config.get('provider','ollama')}_model", ''),
                        )
                    except Exception:
                        pass
                yield 'data: [DONE]\n\n'
                break
            if isinstance(item, dict) and '__error__' in item:
                yield f"data: {json.dumps({'error': item['__error__']})}\n\n"
                yield 'data: [DONE]\n\n'
                break
            accumulated.append(item)
            yield f"data: {json.dumps({'t': item})}\n\n"

    return Response(
        stream_with_context(_generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


# ---------------------------------------------------------------------------
# Cache-aware completion (non-streaming, returns full text)
# ---------------------------------------------------------------------------

def complete_llm(prompt: str, client, cache_task: str = '', cache_ctx: dict = None) -> str:
    """
    Run a non-streaming LLM call. Checks cache first.
    Stores result to cache after a fresh call.
    Returns the full response text.
    """
    # Check cache
    if cache_task and cache_ctx is not None:
        cached = llm_cache.get_cached(cache_task, cache_ctx)
        if cached is not None:
            return cached

    full_text = ''.join(client.stream(prompt))

    # Store to cache
    if cache_task and cache_ctx is not None:
        try:
            llm_cache.store_result(
                cache_task, cache_ctx, full_text,
                provider=client.config.get('provider', ''),
                model=client.config.get(
                    f"{client.config.get('provider','ollama')}_model", ''),
            )
        except Exception:
            pass

    return full_text


# ---------------------------------------------------------------------------
# JSON-safe completion with retry
# ---------------------------------------------------------------------------

def complete_json(prompt: str, client, cache_task: str = '', cache_ctx: dict = None) -> dict | None:
    """
    Run a completion that should return JSON.
    Uses parse_with_retry for robustness. Checks cache first.
    Returns parsed dict/list or None.
    """
    if cache_task and cache_ctx is not None:
        cached = llm_cache.get_cached(cache_task, cache_ctx)
        if cached is not None:
            try:
                import json as _json
                return _json.loads(cached)
            except Exception:
                pass

    result = _parse_with_retry(client, prompt, max_retries=2)

    if result is not None and cache_task and cache_ctx is not None:
        try:
            llm_cache.store_result(
                cache_task, cache_ctx, json.dumps(result),
                provider=client.config.get('provider', ''),
                model=client.config.get(
                    f"{client.config.get('provider','ollama')}_model", ''),
            )
        except Exception:
            pass

    return result
