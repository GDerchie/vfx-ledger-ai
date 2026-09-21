"""
llm/parsers.py — Typed output extractors for LLM responses.
Handles JSON extraction, retry on parse failure, schema validation.
"""
import json
import re


def extract_json(text: str) -> str:
    """Extract first JSON object or array from text."""
    # Try direct parse first
    stripped = text.strip()
    try:
        json.loads(stripped)
        return stripped
    except Exception:
        pass
    # Find first { or [
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start == -1:
            continue
        # Find matching close
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        break
    return text


def parse_json(text: str) -> dict | list | None:
    """Extract and parse JSON from LLM text output."""
    try:
        return json.loads(extract_json(text))
    except Exception:
        return None


def parse_with_retry(client, prompt: str, max_retries: int = 2) -> dict | None:
    """
    Call LLM, try to parse JSON. On failure, send correction prompt.
    Returns parsed dict/list or None.
    """
    current_prompt = prompt
    last_raw = ''
    for attempt in range(max_retries + 1):
        chunks = list(client.stream(current_prompt))
        last_raw = ''.join(chunks)
        result = parse_json(last_raw)
        if result is not None:
            return result
        if attempt < max_retries:
            current_prompt = (
                f"Your previous response was not valid JSON:\n{last_raw}\n\n"
                f"Please respond with ONLY valid JSON, nothing else."
            )
    return None


def parse_id_value_lines(text: str, separator: str = '|') -> dict:
    """
    Parse lines of format: ID|VALUE
    Returns {id: value} dict. Used for batch ops.
    """
    result = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if separator in line:
            parts = line.split(separator, 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                if key:
                    result[key] = val
    return result


def parse_bullets(text: str) -> list[str]:
    """Extract bullet points from markdown text."""
    bullets = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('- ', '* ', '\u2022 ')):
            bullets.append(line[2:].strip())
        elif re.match(r'^\d+\.\s', line):
            bullets.append(re.sub(r'^\d+\.\s', '', line).strip())
    return bullets
