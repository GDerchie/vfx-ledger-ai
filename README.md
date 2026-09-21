# VFX Ledger AI — MACHIAVELLI_a004

A modular Flask web application for VFX production budget management. Tracks shots, vendors, episodes, invoices, and costs across a TV season, with an integrated LLM layer for analysis and forecasting.

## Features

- **Shot tracking** — per-episode shot lists with complexity, VFX type, cost estimates, and EFC
- **Vendor management** — tracker, bid compare, capacity planning, performance scoring
- **Budget forecasting** — episode-level EFC, tax rebate modeling, season optimizer, Monte Carlo risk
- **Invoice log** — invoice-to-shot linking, approval workflow, payment tracking
- **Audit trail** — every field change logged with old/new value and timestamp
- **LLM integration** — cost estimation, complexity tagging, vendor suggestions, budget gap analysis, season risk narrative (Ollama / Claude / OpenAI)
- **Background jobs** — long-running LLM tasks run in background threads with polling API
- **Excel import/export** — shots, assets, and invoices importable from Excel; ForDistribution layout export
- **Game theory optimizer** — season-level vendor allocation solver
- **Auth** — optional password gate with Bearer token support for API access

## Stack

- Python 3.9+ / Flask 3.1
- SQLite (per-project `.vfxdb` files + shared `projects.db`)
- Jinja2 templates, vanilla JS
- LLM: Ollama (local), Claude, or OpenAI — configurable via `llm_config.json`

## Quick Start

### Windows
```bat
START.bat
```

### macOS / Linux
```bash
chmod +x START.sh
./START.sh
```

### Cross-platform (Python)
```bash
python launch.py
```

App runs at **http://localhost:5100**

### Custom port
```bash
python launch.py --port 5200
python app.py --port 5200
./START.sh --port 5200
```

### Install dependencies only
```bash
python launch.py --install
# or
pip install -r requirements.txt
```

## Project Structure

```
app.py                  # Flask factory — blueprint wiring, auth gate
core.py                 # Backward-compat shim (re-exports from services/)
launch.py               # Cross-platform launcher
START.bat               # Windows launcher
START.sh                # macOS/Linux launcher
requirements.txt

routes/                 # Flask blueprints (one per domain)
  auth.py               # Login / logout / token
  projects.py           # Project list, create, open
  episodes.py           # Shot list, ep meta, budget history
  dashboard.py          # Season dashboard
  vendors.py            # Vendor tracker, registry, capacity
  assets.py             # Asset list, bid compare
  notes.py              # VFX notes
  audit.py              # Change log viewer
  optimizer.py          # Season optimizer
  reports.py            # Reports
  export.py             # Excel export
  game_theory.py        # Game theory allocation
  settings_bp.py        # App settings, LLM config, auth config

services/               # Business logic layer
  db.py                 # DB connection helpers, constants
  schema.py             # Schema init and migrations
  auth.py               # Password check, API token validation
  audit.py              # Change log writer
  slack.py              # Slack alert integration
  shots.py              # Shot parsing, COL_MAP, Excel import helpers
  vendors_svc.py        # Vendor loads, paid sync, performance scores
  distribution.py       # EP risk computation
  optimizer.py          # Season optimizer solver
  llm_svc.py            # LLM client factory, cost actuals
  llm_helpers.py        # Prompt helpers
  monte_carlo.py        # Monte Carlo simulation
  game_theory.py        # Game theory solver
  data_graph.py         # Data graph utilities

jobs/                   # Background job queue
  queue.py              # Thread pool, job state management
  api.py                # /api/jobs/<id> polling endpoint

llm/                    # LLM provider layer
  registry.py           # Provider registry (ollama/claude/openai)
  cache.py              # Result caching + cost tracking (ai_calls table)
  parsers.py            # Response parsers
  prompts/              # YAML prompt templates (20+ prompts)

importers/              # Excel importers
  shots_importer.py
  assets_importer.py
  invoices_importer.py
  api.py                # /import/* endpoints

templates/              # Jinja2 HTML templates
static/                 # CSS and JS

projects/               # Per-project .vfxdb SQLite databases (git-ignored)
projects.db             # Project registry (git-ignored)
llm_config.json         # LLM provider configuration
```

## Configuration

### LLM (`llm_config.json`)

```json
{
  "provider": "ollama",
  "ollama_model": "qwen2.5:7b",
  "ollama_url": "http://localhost:11434",
  "claude_model": "claude-haiku-4-5-20251001",
  "claude_api_key": "",
  "openai_model": "gpt-4o-mini",
  "openai_api_key": "",
  "max_tokens": 600,
  "temperature": 0.3
}
```

Switch `provider` to `claude` or `openai` and supply the API key. All LLM calls are cached in the `ai_calls` table — repeated identical requests are served from cache at zero cost.

### Auth

Auth is disabled by default. Enable via the Settings page in the UI, or set a password in `auth_config.json`. API clients pass `Authorization: Bearer <token>`.

### Secret key

```bash
set VFX_SECRET_KEY=your-random-secret-here   # Windows
export VFX_SECRET_KEY=your-random-secret-here  # macOS/Linux
```

Falls back to the built-in default if the env var is not set.

### Slack alerts

Configure webhook URL in the Settings page. Alerts fire on budget threshold breaches.

## Database

Each project gets its own `.vfxdb` SQLite file stored in `projects/`. The shared `projects.db` holds the project registry.

Schema is auto-initialized on first run and auto-migrated on startup — no manual SQL needed.

Key tables per project: `shots`, `sequences`, `ep_meta`, `ep_forecast`, `assets`, `bid_compare`, `vendor_tracker`, `invoice_log`, `invoice_shot_links`, `shot_asset_links`, `budget_history`, `budget_scenario`, `vendor_registry`, `vendor_capacity`, `vendor_forecast`, `change_log`, `project_settings`.

## Seeding Demo Data

```bash
python seed_demo.py
python populate_demo.py
```

## Apply ForDistribution Layout to Excel Export

```bash
START.bat apply path\to\file.xlsx [SheetName] [v2.3]
# or
python apply_export_layout.py path/to/file.xlsx
```

## Requirements

- Python 3.9+
- Flask 3.1, flask-caching, requests, openpyxl, reportlab, python-docx
- Ollama (optional, for local LLM) — https://ollama.ai
