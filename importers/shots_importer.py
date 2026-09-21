"""
importers/shots_importer.py — Validated shot import with diff preview and LLM column mapping.
Wraps the existing _parse_rows_from_excel with validation and diff.
"""
from importers.base import ImportResult, suggest_column_mapping, validate_cost, build_diff
from services.shots import COL_MAP, DB_FIELDS, _parse_rows_from_excel


def run(file_bytes: bytes, ep: int, conn, mode: str = 'upsert',
        sheet_hint: str = None, llm_client=None, dry_run: bool = False) -> ImportResult:
    """
    Import shot rows from Excel bytes into the shots table.

    mode:
      'upsert' — insert new shots, update existing (matched on scene_code + ep)
      'append' — insert only, never update
      'replace' — delete all shots for ep first, then insert

    dry_run=True: build diff but do not write to DB.
    """
    result = ImportResult()

    # Parse Excel
    try:
        rows, sheet_names = _parse_rows_from_excel(file_bytes, ep, sheet_hint)
    except Exception as e:
        result.errors.append(f"Excel parse error: {e}")
        return result

    result.rows_parsed = len(rows)
    if not rows:
        result.warnings.append("No data rows found in file")
        return result

    # Detect unmapped columns (columns present in file but not in COL_MAP)
    # _parse_rows_from_excel already does the mapping — we report what didn't map
    # by checking which DB_FIELDS are absent from most rows
    present_fields  = set()
    for r in rows[:5]:
        present_fields.update(r.keys())
    missing_fields = [f for f in DB_FIELDS if f not in present_fields and f != 'ep']
    if missing_fields:
        result.warnings.append(f"These DB fields have no source column: {missing_fields}")

    # LLM column mapping suggestion (only if there are obvious gaps and client provided)
    if llm_client and missing_fields:
        suggestions = suggest_column_mapping(missing_fields, DB_FIELDS, llm_client)
        result.column_mapping = suggestions

    # Validate and build diff
    if mode == 'replace' and not dry_run:
        conn.execute('DELETE FROM shots WHERE ep=?', (ep,))
        conn.commit()

    for row in rows:
        # Validate cost fields
        for cf in ('cost_est', 'budget_est', 'budget_award_cost', 'efc'):
            if cf in row and row[cf] is not None:
                validated = validate_cost(row[cf], cf, result.warnings)
                if validated is None:
                    row.pop(cf)   # drop field if it exceeds ceiling
                else:
                    row[cf] = validated

        # Find existing row for diff
        existing = None
        if row.get('scene_code'):
            ex_row = conn.execute(
                'SELECT * FROM shots WHERE ep=? AND scene_code=?',
                (ep, row['scene_code'])
            ).fetchone()
            existing = dict(ex_row) if ex_row else None

        diff = build_diff(existing, row, key_fields=['id', 'ep', 'created_at', 'updated_at'])
        if diff:
            diff['scene_code'] = row.get('scene_code', '')
            result.diff.append(diff)

        if dry_run:
            if diff:
                if diff['action'] == 'insert':
                    result.rows_inserted += 1
                else:
                    result.rows_updated += 1
            else:
                result.rows_skipped += 1
            continue

        # Write to DB
        try:
            if existing is None:
                fields = [k for k in row if k in DB_FIELDS + ['ep']]
                placeholders = ', '.join('?' * len(fields))
                cols = ', '.join(fields)
                conn.execute(
                    f'INSERT INTO shots ({cols}) VALUES ({placeholders})',
                    [row[f] for f in fields]
                )
                result.rows_inserted += 1
            elif mode != 'append' and diff:
                updates = {c['field']: c['new'] for c in diff['changes']
                           if c['field'] in DB_FIELDS}
                if updates:
                    set_clause = ', '.join(f'{k}=?' for k in updates)
                    conn.execute(
                        f'UPDATE shots SET {set_clause} WHERE id=?',
                        list(updates.values()) + [existing['id']]
                    )
                    result.rows_updated += 1
                else:
                    result.rows_skipped += 1
            else:
                result.rows_skipped += 1
        except Exception as e:
            result.errors.append(f"Row SC{row.get('scene_code','?')}: {e}")

    if not dry_run:
        conn.commit()

    return result
