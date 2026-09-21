"""
importers/base.py — Shared import validation, LLM column mapping, and diff preview.
"""
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportResult:
    rows_parsed:  int = 0
    rows_inserted: int = 0
    rows_updated:  int = 0
    rows_skipped:  int = 0
    errors:        list = field(default_factory=list)
    warnings:      list = field(default_factory=list)
    # Diff preview — list of {action, id, changes} dicts
    diff:          list = field(default_factory=list)
    column_mapping: dict = field(default_factory=dict)  # original_col → db_field
    unmapped_cols:  list = field(default_factory=list)  # columns not in COL_MAP

    def to_dict(self):
        return {
            'rows_parsed':   self.rows_parsed,
            'rows_inserted': self.rows_inserted,
            'rows_updated':  self.rows_updated,
            'rows_skipped':  self.rows_skipped,
            'errors':        self.errors,
            'warnings':      self.warnings,
            'diff':          self.diff[:100],   # cap diff at 100 rows for JSON response
            'column_mapping': self.column_mapping,
            'unmapped_cols':  self.unmapped_cols,
        }


def suggest_column_mapping(unmapped_cols: list, known_fields: list, client) -> dict:
    """
    Use LLM to suggest mappings for column names that didn't match COL_MAP.
    Returns {original_col: suggested_db_field_or_None}.
    Only called if there are unmapped columns.
    """
    if not unmapped_cols or not client:
        return {}

    import llm as llm_module
    fields_str = ', '.join(known_fields)
    cols_str   = '\n'.join(f'  - {c}' for c in unmapped_cols)

    prompt = (
        f"These Excel column names were not recognized in a VFX budget import:\n{cols_str}\n\n"
        f"Known database fields: {fields_str}\n\n"
        "For each unrecognized column, suggest the best matching database field, or null if no match.\n"
        "Reply with ONLY valid JSON: {\"original_col\": \"db_field_or_null\", ...}"
    )
    try:
        full_txt = ''.join(client.stream(prompt))
        suggestions = json.loads(_extract_json(full_txt))
        # Validate suggestions are real fields
        return {k: v for k, v in suggestions.items() if v in known_fields or v is None}
    except Exception:
        return {}


def _extract_json(text: str) -> str:
    """Extract first JSON object from text."""
    start = text.find('{')
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return text


def validate_cost(v, field_name: str, warnings: list) -> float:
    """Validate a cost field. Appends to warnings if value is suspicious."""
    MAX = 10_000_000
    try:
        val = float(str(v).replace(',', '').replace('$', '').strip())
        if val < 0:
            warnings.append(f"{field_name}: negative value {val} clamped to 0")
            return 0.0
        if val > MAX:
            warnings.append(f"{field_name}: {val:,.0f} exceeds $10M ceiling — skipped")
            return None
        return val
    except Exception:
        return 0.0


def build_diff(existing_row: dict, new_row: dict, key_fields: list) -> dict:
    """
    Compare existing DB row to incoming row.
    Returns diff dict {action, id, changes: [{field, old, new}]} or None if no changes.
    """
    if existing_row is None:
        return {'action': 'insert', 'changes': []}

    changes = []
    for field_name, new_val in new_row.items():
        if field_name in key_fields:
            continue
        old_val = existing_row.get(field_name)
        # Normalise for comparison
        old_s = str(old_val).strip() if old_val is not None else ''
        new_s = str(new_val).strip() if new_val is not None else ''
        if old_s != new_s and new_s:
            changes.append({'field': field_name, 'old': old_s, 'new': new_s})

    if not changes:
        return None
    return {'action': 'update', 'id': existing_row.get('id'), 'changes': changes}
