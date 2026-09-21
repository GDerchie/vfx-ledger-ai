"""
services/slack.py — Slack alert helpers.
"""
import json
import os
from services.db import BASE_DIR

try:
    import requests as _requests
except ImportError:
    _requests = None

_SLACK_CONFIG_FILE = os.path.join(BASE_DIR, 'slack_config.json')


def _load_slack_config():
    try:
        with open(_SLACK_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {'webhook_url': ''}


def _save_slack_config(cfg):
    with open(_SLACK_CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)


def _init_slack(app):
    cfg = _load_slack_config()
    app.config['SLACK_WEBHOOK'] = cfg.get('webhook_url', '')


def slack_alert(msg):
    from flask import current_app
    if _requests is None:
        return
    webhook = current_app.config.get('SLACK_WEBHOOK') or ''
    if webhook:
        try:
            _requests.post(webhook, json={'text': msg}, timeout=3)
        except Exception:
            pass


def build_digest(conn, project_name: str, season: str) -> str:
    """
    Build a plain-text weekly budget digest for Slack.
    Returns the formatted message string.
    """
    try:
        agg = conn.execute('''
            SELECT COUNT(CASE WHEN omit=0 THEN 1 END) as shots,
                   SUM(CASE WHEN omit=0 THEN COALESCE(cost_est,0) ELSE 0 END) as est,
                   SUM(CASE WHEN omit=0 THEN COALESCE(efc,0) ELSE 0 END) as efc
            FROM shots
        ''').fetchone()

        vendors_over = conn.execute('''
            SELECT award_vendor, COUNT(*) as n
            FROM shots WHERE omit=0 AND award_vendor IS NOT NULL AND award_vendor!=''
            GROUP BY award_vendor ORDER BY n DESC LIMIT 5
        ''').fetchall()

        pending_inv = conn.execute(
            "SELECT COUNT(*) as n, COALESCE(SUM(amount),0) as total "
            "FROM invoice_log WHERE UPPER(status) IN ('PENDING','APPROVED')"
        ).fetchone()

        shots    = agg['shots']  or 0
        est      = agg['est']    or 0
        efc      = agg['efc']    or 0
        variance = efc - est
        pct      = f"{variance/est*100:+.1f}%" if est else "N/A"
        v_list   = ' | '.join(f"{r['award_vendor']} ({r['n']})" for r in vendors_over)

        lines = [
            f"*{project_name} {season} — Weekly Budget Digest*",
            f"  Season EFC: *${efc:,.0f}* vs EST ${est:,.0f}  ({pct})",
            f"  Shots tracked: {shots}",
            f"  Top vendors: {v_list or 'none'}",
            f"  Pending invoices: {pending_inv['n']} (${pending_inv['total']:,.0f})",
        ]
        return '\n'.join(lines)
    except Exception as e:
        return f"Digest error: {e}"


def send_digest(conn, project_name: str, season: str):
    """Build and send the weekly digest via Slack webhook."""
    msg = build_digest(conn, project_name, season)
    slack_alert(msg)
    return msg
