"""
core.py — Backward-compatibility shim.
All logic has moved to services/. This file re-exports everything so
existing routes continue to work without modification.
"""
# DB
from services.db import (
    BASE_DIR, PROJECTS_DB, PROJECTS_DIR, _MAX_COST,
    _NullCache, cache, _GConn,
    get_projects_db, get_db, close_db_connections,
    get_episodes, require_project,
)
# Auth
from services.auth import (
    _AUTH_CONFIG_FILE,
    _load_auth_config, _save_auth_config, check_password, validate_api_token,
)
_check_password = check_password   # alias used by routes/projects.py token endpoint
# Audit
from services.audit import log_change
# Slack
from services.slack import (
    _SLACK_CONFIG_FILE,
    _load_slack_config, _save_slack_config, _init_slack, slack_alert,
)
# LLM
from services.llm_svc import get_llm_client, reset_llm_client, get_cost_actuals
# Vendors
from services.vendors_svc import _sfloat, sync_tracker_paid, get_vendor_loads, get_vendor_perf_scores
# Shots
from services.shots import COL_MAP, DB_FIELDS, _parse_rows_from_excel, clean_cost, get_project_setting
# Distribution
from services.distribution import compute_ep_risk
# Optimizer
from services.optimizer import run_season_optimizer
# Schema
from services.schema import init_project_db, init_projects_db, migrate_legacy_db, migrate_db_schema

# ---------------------------------------------------------------------------
# cache is a module-level variable — app.py does `core.cache = _real_cache`
# We also need to propagate it to services.db so get_db callers using
# services.db.cache get the same object.
# This is handled by app.py which sets both core.cache and services.db.cache.
# ---------------------------------------------------------------------------
