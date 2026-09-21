"""
services/audit.py — Change history logging.
"""
from services.db import get_db


def log_change(table_name, row_id, field, old_val, new_val):
    try:
        conn = get_db()
        if not conn:
            return
        conn.execute(
            'INSERT INTO change_log(table_name,row_id,field,old_value,new_value) VALUES(?,?,?,?,?)',
            (table_name, row_id, field, str(old_val), str(new_val))
        )
        conn.commit()
    except Exception:
        pass
