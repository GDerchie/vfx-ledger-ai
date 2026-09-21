"""
services/schema.py — DB schema initialization and migration.
"""
import sqlite3
import os
from datetime import datetime
from services.db import BASE_DIR, get_projects_db


def init_project_db(db_path, ep_start=101, ep_end=108):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL, shot_num INTEGER,
        scene_code TEXT, s_code TEXT, location TEXT, ext_int TEXT, pg TEXT, img TEXT,
        asset TEXT, script_desc TEXT, vfx_desc TEXT, shot_type TEXT, omit INTEGER DEFAULT 0,
        complexity TEXT DEFAULT '', history_notes TEXT, shot_est INTEGER DEFAULT 1,
        cost_est REAL DEFAULT 0, budget_est REAL DEFAULT 0, award_vendor TEXT,
        edit_count INTEGER DEFAULT 0, budget_award_cost REAL DEFAULT 0, efc REAL DEFAULT 0,
        notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ep_meta (
        ep INTEGER PRIMARY KEY, script_v TEXT DEFAULT '', edit_v TEXT DEFAULT '',
        status TEXT DEFAULT '', est_reduction REAL DEFAULT 0,
        reduction_notes TEXT DEFAULT '', notes TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL, seq_name TEXT,
        location TEXT, omit INTEGER DEFAULT 0, est_shots INTEGER DEFAULT 0,
        current_cut INTEGER DEFAULT 0, lbudget REAL DEFAULT 0, efc REAL DEFAULT 0,
        variance_val REAL DEFAULT 0, status TEXT, est_reductions TEXT, est_ctd REAL DEFAULT 0,
        turnover_deadline TEXT, notes TEXT, auto_sync INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL, record_date TEXT,
        version_label TEXT, script_v TEXT, edit_v TEXT, est_shots INTEGER DEFAULT 0,
        edit_shots INTEGER DEFAULT 0, est_budget REAL DEFAULT 0, efc_budget REAL DEFAULT 0,
        variance_val REAL DEFAULT 0, status TEXT, est_reduction REAL DEFAULT 0,
        reduction_notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vfx_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_num INTEGER, author TEXT,
        note_text TEXT, note_date TEXT, resolved INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, orig_id INTEGER, ep INTEGER,
        scene_code TEXT, turnover TEXT, asset_name TEXT, description TEXT,
        reference TEXT, asset_type TEXT, repeat_asset INTEGER DEFAULT 0,
        hero_id INTEGER DEFAULT 0, omit INTEGER DEFAULT 0, ref TEXT, notes TEXT,
        lidar INTEGER DEFAULT 0, photogrammetry INTEGER DEFAULT 0,
        est_budget REAL DEFAULT 0, actual_spend REAL DEFAULT 0,
        award_vendor TEXT, vendor_bids TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bid_compare (
        id INTEGER PRIMARY KEY AUTOINCREMENT, orig_id INTEGER, ep INTEGER,
        sc TEXT, setting TEXT, novfx INTEGER DEFAULT 0, scount INTEGER DEFAULT 0,
        edit_count INTEGER DEFAULT 0, vfxtype TEXT, version INTEGER DEFAULT 1,
        award TEXT, lockbudget REAL DEFAULT 0, efc REAL DEFAULT 0, vendor_bids TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, region TEXT, ep INTEGER,
        asset_award REAL, award_ep REAL, tot_award REAL, paid REAL DEFAULT 0,
        pending REAL DEFAULT 0, remaining REAL, tax_reb REAL, gross_local REAL,
        gross_usd REAL, sale_tax_amount REAL, gross_plus_tax REAL,
        tax_rebate_amt REAL, net_after_rebate REAL, final_price REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invoice_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, episode INTEGER,
        inv_num TEXT, inv_date TEXT, amount REAL DEFAULT 0, status TEXT,
        approve_date TEXT, notes TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget_scenario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, scenario_type TEXT DEFAULT 'Conservative',
        ep INTEGER DEFAULT 101, tax_pct REAL DEFAULT 0, eligible_pct REAL DEFAULT 0,
        net_cost REAL DEFAULT 0, notes TEXT DEFAULT '', region_mix TEXT DEFAULT '[]'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ep_forecast (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL UNIQUE,
        contingency REAL DEFAULT 0.2, budget REAL DEFAULT 0, award REAL DEFAULT 0,
        eligible REAL DEFAULT 0, global_rebate_pct REAL DEFAULT 0,
        global_pct REAL DEFAULT 0, notes TEXT DEFAULT '',
        region_mix TEXT DEFAULT '[]'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_forecast (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT DEFAULT '', ep INTEGER DEFAULT 101,
        gross_local REAL DEFAULT 0, gross_usd REAL DEFAULT 0, region TEXT DEFAULT '',
        eligible_pct REAL DEFAULT 0, rebate_pct REAL DEFAULT 0, notes TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL UNIQUE,
        region TEXT DEFAULT '', fx_rate REAL DEFAULT 1.0, tax_pct REAL DEFAULT 0.0,
        rebate_pct REAL DEFAULT 0.0, contact TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_capacity (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL UNIQUE,
        shots_per_month INTEGER DEFAULT 100, efficiency_pct REAL DEFAULT 0.95
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS change_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT, row_id INTEGER,
        field TEXT, old_value TEXT, new_value TEXT, user TEXT DEFAULT 'system',
        timestamp TEXT DEFAULT (datetime('now'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shot_asset_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shot_id INTEGER NOT NULL, asset_id INTEGER NOT NULL,
        UNIQUE(shot_id, asset_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invoice_shot_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL, shot_id INTEGER NOT NULL,
        UNIQUE(invoice_id, shot_id)
    )''')
    for ep in range(ep_start, ep_end + 1):
        c.execute('INSERT OR IGNORE INTO ep_meta (ep) VALUES (?)', (ep,))
        c.execute('INSERT OR IGNORE INTO ep_forecast (ep) VALUES (?)', (ep,))
    conn.commit()
    conn.close()


def init_projects_db():
    conn = get_projects_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        season TEXT NOT NULL DEFAULT 'S1', db_filename TEXT NOT NULL,
        db_path TEXT NOT NULL, ep_start INTEGER DEFAULT 101,
        ep_end INTEGER DEFAULT 108, description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_opened TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def migrate_legacy_db():
    """Register vfx_system.db as a project if it exists and isn't registered yet."""
    legacy_path = os.path.join(BASE_DIR, 'vfx_system.db')
    if not os.path.exists(legacy_path):
        return
    conn = get_projects_db()
    already = conn.execute(
        "SELECT id FROM projects WHERE db_filename='vfx_system.db'"
    ).fetchone()
    if not already:
        conn.execute('''INSERT INTO projects
            (name, season, db_filename, db_path, ep_start, ep_end, description, last_opened)
            VALUES (?,?,?,?,?,?,?,?)''',
            ('SIDEWINDER', 'S1', 'vfx_system.db', legacy_path, 101, 108,
             'Migrated legacy project', datetime.now().isoformat()))
        conn.commit()
    conn.close()


def migrate_db_schema():
    """Add any missing columns/tables to existing project databases."""
    conn = get_projects_db()
    projects = conn.execute('SELECT db_path FROM projects').fetchall()
    conn.close()
    for proj in projects:
        try:
            pconn = sqlite3.connect(proj['db_path'])
            cols = [r[1] for r in pconn.execute('PRAGMA table_info(sequences)').fetchall()]
            if 'auto_sync' not in cols:
                pconn.execute('ALTER TABLE sequences ADD COLUMN auto_sync INTEGER DEFAULT 0')
                pconn.commit()
            tables = [r[0] for r in pconn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for tbl, ddl in [
                ('assets', '''CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, orig_id INTEGER, ep INTEGER,
                    scene_code TEXT, turnover TEXT, asset_name TEXT, description TEXT,
                    reference TEXT, asset_type TEXT, repeat_asset INTEGER DEFAULT 0,
                    hero_id INTEGER DEFAULT 0, omit INTEGER DEFAULT 0, ref TEXT,
                    notes TEXT, lidar INTEGER DEFAULT 0, photogrammetry INTEGER DEFAULT 0,
                    est_budget REAL DEFAULT 0, actual_spend REAL DEFAULT 0,
                    award_vendor TEXT, vendor_bids TEXT)'''),
                ('bid_compare', '''CREATE TABLE IF NOT EXISTS bid_compare (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, orig_id INTEGER, ep INTEGER,
                    sc TEXT, setting TEXT, novfx INTEGER DEFAULT 0, scount INTEGER DEFAULT 0,
                    edit_count INTEGER DEFAULT 0, vfxtype TEXT, version INTEGER DEFAULT 1,
                    award TEXT, lockbudget REAL DEFAULT 0, efc REAL DEFAULT 0, vendor_bids TEXT)'''),
                ('vendor_tracker', '''CREATE TABLE IF NOT EXISTS vendor_tracker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, region TEXT, ep INTEGER,
                    asset_award REAL, award_ep REAL, tot_award REAL, paid REAL DEFAULT 0,
                    pending REAL DEFAULT 0, remaining REAL, tax_reb REAL, gross_local REAL,
                    gross_usd REAL, sale_tax_amount REAL, gross_plus_tax REAL,
                    tax_rebate_amt REAL, net_after_rebate REAL, final_price REAL)'''),
                ('invoice_log', '''CREATE TABLE IF NOT EXISTS invoice_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, episode INTEGER,
                    inv_num TEXT, inv_date TEXT, amount REAL DEFAULT 0,
                    status TEXT, approve_date TEXT, notes TEXT)'''),
                ('budget_scenario', '''CREATE TABLE IF NOT EXISTS budget_scenario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, scenario_type TEXT DEFAULT \'Conservative\',
                    ep INTEGER DEFAULT 101, tax_pct REAL DEFAULT 0,
                    eligible_pct REAL DEFAULT 0, net_cost REAL DEFAULT 0,
                    notes TEXT DEFAULT \'\', region_mix TEXT DEFAULT \'[]\')'''),
                ('ep_forecast', '''CREATE TABLE IF NOT EXISTS ep_forecast (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ep INTEGER NOT NULL UNIQUE,
                    contingency REAL DEFAULT 0.2, budget REAL DEFAULT 0, award REAL DEFAULT 0,
                    eligible REAL DEFAULT 0, global_rebate_pct REAL DEFAULT 0,
                    global_pct REAL DEFAULT 0, notes TEXT DEFAULT \'\', region_mix TEXT DEFAULT \'[]\')'''),
                ('vendor_forecast', '''CREATE TABLE IF NOT EXISTS vendor_forecast (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT DEFAULT \'\',
                    ep INTEGER DEFAULT 101, gross_local REAL DEFAULT 0, gross_usd REAL DEFAULT 0,
                    region TEXT DEFAULT \'\', eligible_pct REAL DEFAULT 0,
                    rebate_pct REAL DEFAULT 0, notes TEXT DEFAULT \'\')'''),
                ('vendor_registry', '''CREATE TABLE IF NOT EXISTS vendor_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL UNIQUE,
                    region TEXT DEFAULT \'\', fx_rate REAL DEFAULT 1.0, tax_pct REAL DEFAULT 0.0,
                    rebate_pct REAL DEFAULT 0.0, contact TEXT DEFAULT \'\')'''),
                ('vendor_capacity', '''CREATE TABLE IF NOT EXISTS vendor_capacity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL UNIQUE,
                    shots_per_month INTEGER DEFAULT 100, efficiency_pct REAL DEFAULT 0.95)'''),
            ]:
                if tbl not in tables:
                    pconn.execute(ddl)
                    pconn.commit()
                    if tbl == 'ep_forecast':
                        for _ep in range(101, 109):
                            pconn.execute('INSERT OR IGNORE INTO ep_forecast (ep) VALUES (?)', (_ep,))
                        pconn.commit()
            shot_cols = [r[1] for r in pconn.execute('PRAGMA table_info(shots)').fetchall()]
            if 'complexity' not in shot_cols:
                pconn.execute("ALTER TABLE shots ADD COLUMN complexity TEXT DEFAULT ''")
                pconn.commit()
            epf_cols = [r[1] for r in pconn.execute('PRAGMA table_info(ep_forecast)').fetchall()]
            if 'region_mix' not in epf_cols:
                pconn.execute("ALTER TABLE ep_forecast ADD COLUMN region_mix TEXT DEFAULT '[]'")
                pconn.commit()
            sc_cols = [r[1] for r in pconn.execute('PRAGMA table_info(budget_scenario)').fetchall()]
            if 'region_mix' not in sc_cols:
                pconn.execute("ALTER TABLE budget_scenario ADD COLUMN region_mix TEXT DEFAULT '[]'")
                pconn.commit()
            pconn.execute('''CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT, row_id INTEGER,
                field TEXT, old_value TEXT, new_value TEXT, user TEXT DEFAULT 'system',
                timestamp TEXT DEFAULT (datetime('now')))''')
            pconn.execute('''CREATE TABLE IF NOT EXISTS project_settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
            pconn.execute('''CREATE TABLE IF NOT EXISTS shot_asset_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER NOT NULL, asset_id INTEGER NOT NULL,
                UNIQUE(shot_id, asset_id))''')
            pconn.execute('''CREATE TABLE IF NOT EXISTS invoice_shot_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL, shot_id INTEGER NOT NULL,
                UNIQUE(invoice_id, shot_id))''')
            pconn.commit()
            pconn.close()
        except Exception:
            pass
