# MACHIAVELLI_a004 — User Tutorial

**VFX Budget Tracking & Optimization System**
A Flask web application for managing episode-level VFX costs, shot inventory, vendor assignments, risk forecasting, and cost optimization across multi-episode TV/film seasons.

---

## Table of Contents

1. [Installation & Launch](#1-installation--launch)
2. [First-Time Setup](#2-first-time-setup)
3. [Project Management](#3-project-management)
4. [Episode & Shot Management](#4-episode--shot-management)
5. [Importing Shots from Excel](#5-importing-shots-from-excel)
6. [LLM-Assisted Workflows](#6-llm-assisted-workflows)
7. [Vendor Management](#7-vendor-management)
8. [Season Optimizer](#8-season-optimizer)
9. [Risk Forecasting](#9-risk-forecasting)
10. [Invoice Tracking](#10-invoice-tracking)
11. [Dashboard & Reporting](#11-dashboard--reporting)
12. [Audit Log](#12-audit-log)
13. [Slack Alerts](#13-slack-alerts)
14. [Authentication & API Access](#14-authentication--api-access)
15. [Key Reference Tables](#15-key-reference-tables)

---

## 1. Installation & Launch

### Requirements
- Python 3.9 or higher
- Packages: Flask 3.1, openpyxl 3.1.5, reportlab 4.2.5, requests 2.32.3

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the launcher with `--install`:

```bash
python launch.py --install
```

### Launch the App

**Windows:**
```batch
START.bat
```

**macOS / Linux:**
```bash
./START.sh
```

**Cross-platform (Python):**
```bash
python launch.py                  # default port 5000
python launch.py --port 5001      # custom port
python launch.py --no-browser     # no auto browser open
```

The app opens at `http://localhost:5000`.

---

## 2. First-Time Setup

### Create a Demo Project (Optional)

Populate a fully seeded demo project (SHOWCASE S1) with 5 vendors and 8 episodes of sample data:

```bash
python populate_demo.py
```

Then open `http://localhost:5000` and select **SHOWCASE S1** from the project list.

### Configure the LLM (Optional)

Edit `llm_config.json` to choose your LLM provider:

```json
{
  "provider": "ollama",
  "ollama_model": "qwen2.5:7b",
  "ollama_url": "http://localhost:11434",
  "claude_model": "claude-haiku-4-5-20251001",
  "claude_api_key": "YOUR_KEY_HERE",
  "openai_model": "gpt-4o-mini",
  "openai_api_key": "YOUR_KEY_HERE",
  "max_tokens": 600,
  "temperature": 0.3
}
```

| Provider | Requirement |
|----------|-------------|
| `ollama` | Ollama running locally with `qwen2.5:7b` pulled |
| `claude` | Anthropic API key |
| `openai` | OpenAI API key |

Set `provider` to your choice. LLM features are optional — the system works fully without them.

---

## 3. Project Management

### Home Page (`/`)

The home page lists all registered projects. Each project is an independent SQLite database stored in the `projects/` directory.

### Create a New Project

1. Click **New Project** on the home page.
2. Enter a project name (e.g., `ANDOR S2`).
3. Set episode range (e.g., 101–108 for 8 episodes).
4. The system creates a new `.vfxdb` file in `projects/`.

### Select a Project

Click any project name. All subsequent pages are scoped to that project.

### Project Settings (`/settings`)

Configure per-project options:

| Setting | Purpose |
|---------|---------|
| `ep_start` / `ep_end` | Episode number range |
| `efc_alert_threshold` | Multiplier that triggers Slack alert (default: 1.2 = 20% over EST) |
| `default_region` | Default vendor region for new bids |
| `slack_webhook_url` | Slack incoming webhook for cost overrun alerts |

---

## 4. Episode & Shot Management

### Episode Detail Page (`/ep/101`)

Each episode has a shots table showing all VFX work. Key columns:

| Column | Description |
|--------|-------------|
| SC | Scene number |
| LOCATION | Set/location name |
| EXT/INT | Exterior or interior |
| SCRIPT DESC | Script description |
| ASSET | Associated asset name |
| TYPE | Shot type (CG, Comp, Roto, Paint, FX, etc.) |
| COMPLEXITY | SIMPLE / MEDIUM / HEAVY |
| COST EST | Estimated cost (USD) |
| EFC | Expected Final Cost — updated as work progresses |
| AWARD VENDOR | Vendor awarded the shot |
| OMIT | Mark shot as omitted |

### Adding a Shot Manually

1. Navigate to `/ep/101` (or any episode).
2. Click **Add Shot**.
3. Fill in fields and click **Save**.
4. Shot is immediately saved to the project database.

### Editing a Shot

Click any cell in the shots table to edit inline. Changes are auto-saved and logged to the audit trail.

**Validation rules:**
- Cost fields (COST EST, EFC) must be ≤ $10,000,000.
- If EFC > COST EST × 1.2, a Slack alert fires (if configured).

### Deleting a Shot

Click the delete icon on the shot row. Action is logged to the audit trail.

---

## 5. Importing Shots from Excel

### Prepare Your Excel File

The importer auto-detects the header row and supports flexible column naming:

| Accepted Excel Column Names | Maps To |
|----------------------------|---------|
| EP, Episode | `ep` |
| SC, Scene, Scene #, Scene No | `sc` |
| Location, Set | `location` |
| EXT/INT | `ext_int` |
| Script Desc, Description, Beat | `script_desc` |
| Asset | `asset` |
| Type, VFX Type, Shot Type | `shot_type` |
| Complexity | `complexity` |
| Cost Est, EST, Budget | `cost_est` |
| EFC, Actuals | `efc` |
| Award Vendor, Vendor | `award_vendor` |
| Omit | `omit` |

### Import Steps

1. Navigate to the episode page (e.g., `/ep/101`).
2. Click **Import Shots**.
3. Upload your `.xlsx` file.
4. Click **Preview** — dry-run shows what will be added/updated, no DB writes.
5. Select import mode:
   - **Upsert** — add new rows, update existing ones (safe for re-imports)
   - **Append** — add only new rows, skip duplicates
   - **Replace** — delete all existing shots and insert fresh (destructive)
6. Click **Confirm Import**.

### LLM Enrichment During Import

If a compatible LLM is running, the importer auto-enriches each shot:
- Generates a VFX description from script context
- Classifies shot type
- Rates complexity (SIMPLE / MEDIUM / HEAVY)
- Estimates cost using historical project actuals as context

This runs as a background job. Check progress at `/jobs`.

---

## 6. LLM-Assisted Workflows

All LLM features require a configured provider (see Section 2).

### Available LLM Tasks

| Task | Endpoint | Output |
|------|----------|--------|
| **VFX Description** | `POST /api/llm/vfx_desc` | 1–2 sentence VFX-specific shot description |
| **Shot Type** | `POST /api/llm/shot_type` | CG / Comp / Roto / Paint / FX / Grade / Crowd / Extension / Creature / Title |
| **Cost Estimate** | `POST /api/llm/cost_est` | Estimated cost + tier (LOW/MED/HIGH) + reasoning |
| **Complexity Tag** | `POST /api/llm/complexity_tag` | SIMPLE / MEDIUM / HEAVY |
| **Batch Complexity** | `POST /api/llm/complexity_batch` | Rate multiple shots in one call |
| **EP Narrative** | `POST /api/llm/ep_narrative` | Producer memo summarizing the episode |
| **Gap Suggestions** | Background job | Identify under-estimated or missing shots |

### Cost Estimate Context

The cost estimator uses real project actuals as context. It queries historical shots with the same type, complexity, and vendor, then sends that history to the LLM for calibrated estimates.

### Invoking from the UI

On the Episode page, each shot has LLM action buttons:
- **Describe** — generates/overwrites VFX description
- **Classify** — sets shot type
- **Estimate** — sets cost_est

---

## 7. Vendor Management

### Vendor Registry (`/vendor-registry`)

The central registry stores vendor master data:

| Field | Description |
|-------|-------------|
| Name | Vendor company name |
| Region | Geographic region (UK, CAN, AU, US, etc.) |
| FX Rate | Currency conversion rate to USD |
| Tax % | Applicable tax rate |
| Rebate % | Tax rebate or incentive percentage |
| Contact | Primary contact name/email |

Add vendors here before assigning shots.

### Vendor Capacity

Set capacity per vendor:

| Field | Description |
|-------|-------------|
| Shots Per Month | Maximum shots the vendor can deliver per month |
| Efficiency % | Delivery efficiency factor (1.0 = 100%) |

Used by the Risk Forecast engine to compute capacity risk.

### Vendor Tracker (`/vendor-tracker`)

Tracks payments per vendor:

| Column | Description |
|--------|-------------|
| TOT AWARD | Total value awarded to vendor |
| PAID | Amount invoiced and paid |
| PENDING | Invoiced but not yet paid |
| REMAINING | Award minus paid (unbilled work) |
| TAX | Tax applied |
| REBATE | Rebate/incentive received |

### Bid Compare (`/bidcompare`)

Per-scene bid history from multiple vendors. Used by the optimizer to select the lowest-cost assignment. Add bids by scene number, then compare across vendors.

### Vendor Performance Score

Automatically computed composite score:

```
score = bid_confidence × 0.50 + invoice_accuracy × 0.30 + edit_efficiency × 0.20

STRONG  ≥ 0.65
MED     ≥ 0.40
WEAK    < 0.40
```

- **bid_confidence** — based on consistency of bids (low variation = high confidence)
- **invoice_accuracy** — invoiced amounts vs. awarded amounts
- **edit_efficiency** — edit rounds required per shot

View scores in the Vendor Tracker page.

---

## 8. Season Optimizer

### What It Does

The Season Optimizer assigns each shot to the vendor with the lowest bid cost, subject to configurable constraints. It produces a full-season assignment plan with total cost and workload distribution.

### Access

Navigate to `/optimizer`.

### Settings

| Setting | Description |
|---------|-------------|
| Min Confidence | Minimum vendor confidence score to be considered (0.0–1.0) |
| Max Vendor Share | Maximum % of total shots any single vendor can receive |
| Preferred Vendors | List of preferred vendors to prioritize |

### Algorithm

```
For each shot:
  Find the scene in bid_compare
  For each vendor with a bid:
    Skip if confidence < min_confidence
    Skip if vendor's current share > max_vendor_share
    Skip if a preferred vendor is specified for this scene
  Assign to vendor with minimum per-shot cost
```

Vendor confidence is computed using the Coefficient of Variation (CV) of their bids:

```
cv = std_dev(bids) / mean(bids)
sample_factor = min(num_bids / 30, 1.0)     # reaches full confidence at 30 samples
confidence = sample_factor × max(0, 1 − cv)
```

### Output

- **Assignments** — vendor recommended per shot
- **Vendor Summary** — shots assigned, workload %, estimated cost per vendor
- **Total Season Cost** — optimized total spend
- **Overall Confidence** — weighted average confidence across all assignments
- **Unassigned Shots** — shots with no eligible bids

### Export

Download the optimizer output as Excel for distribution to production finance.

---

## 9. Risk Forecasting

### What It Does

Computes a per-episode delivery risk score using three weighted factors:

```
risk = capacity_risk × 0.45 + complexity_risk × 0.30 + confidence_risk × 0.25
predicted_delay_days = int(risk × 30)
```

| Status | Risk Score | Meaning |
|--------|-----------|---------|
| SAFE | < 0.25 | On track |
| WATCH | 0.25–0.50 | Monitor closely |
| AT RISK | 0.50–0.75 | Intervention needed |
| HIGH RISK | > 0.75 | Immediate action required |

### Factor Definitions

| Factor | Weight | How Computed |
|--------|--------|-------------|
| Capacity Risk | 45% | Total shots assigned / vendor monthly capacity |
| Complexity Risk | 30% | Ratio of HEAVY shots in the episode |
| Confidence Risk | 25% | Inverse of average vendor bid confidence |

### Where to See It

Risk scores appear on the **Dashboard** (`/dashboard`) per episode, and in the **Distribution** view (`/distribution`) for side-by-side comparison across all episodes.

---

## 10. Invoice Tracking

### Invoice Log (`/invoicelog`)

Tracks all invoices received from vendors:

| Field | Description |
|-------|-------------|
| INV NUM | Invoice number |
| Vendor | Vendor name |
| Episode | Which episode |
| Amount | Invoice amount (USD) |
| Status | RECEIVED / APPROVED / PAID / DISPUTED |
| Date | Invoice date |

### Import Invoices from Excel

Navigate to **Import → Invoices**, upload an Excel file with the invoice log. Same upsert/append/replace modes as shot import.

### Invoice-Shot Links

Link invoices to specific shots for granular cost tracking:
- Navigate to an invoice record
- Click **Link Shots**
- Select the shots covered by this invoice

This enables accurate EFC tracking per shot as invoices arrive.

---

## 11. Dashboard & Reporting

### Season Dashboard (`/dashboard`)

Top-level season summary:

| Panel | Shows |
|-------|-------|
| Budget Overview | Total EST vs EFC, variance, % over/under |
| Episode Breakdown | Per-episode shot count, EST, EFC, risk status |
| Top Vendors | Top 5 vendors by EFC spend |
| Shot Type Split | CG / Comp / Roto / Paint / FX / Grade breakdown |
| Complexity Split | SIMPLE / MEDIUM / HEAVY counts |
| Asset Summary | Total asset estimate vs actual spend |

### Distribution View (`/distribution`)

Side-by-side multi-episode table:
- All episodes in columns
- Shots, EST cost, EFC cost, variance per episode
- Color-coded variance (green = under, red = over)

Useful for weekly production finance reviews.

### Reports (`/reports`)

Generate formatted reports:
- **Budget Summary** — season cost roll-up
- **Vendor Summary** — all vendor spend
- **Episode Detail** — full shot list per episode
- **Risk Report** — all episode risk scores

### Budget Scenarios (`/scenario`)

Model alternative budget outcomes:
- **Conservative** — apply contingency factor to EFC
- **Optimistic** — assume current velocity continues
- Custom scenarios with adjustable multipliers

---

## 12. Audit Log

### Access

Navigate to `/audit`.

### What Is Tracked

Every change to a financial or key field is logged:

| Field | Description |
|-------|-------------|
| Timestamp | When the change was made |
| Table | Which DB table was modified |
| Row ID | Which row |
| Field | Which field was changed |
| Old Value | Previous value |
| New Value | New value |
| User | Who made the change (session user or "system" for imports) |

### Filtering

Filter the audit log by:
- Date range
- Table name (shots, vendor_tracker, invoice_log, etc.)
- Field name
- User

---

## 13. Slack Alerts

### Setup

1. Create a Slack Incoming Webhook in your Slack workspace.
2. Paste the webhook URL into **Settings → slack_webhook_url**.

### When Alerts Fire

An alert fires when a shot's EFC is updated and:

```
EFC > COST_EST × efc_alert_threshold
```

Default threshold is **1.2** (20% over estimate).

The alert message includes: episode, scene, location, old EFC, new EFC, % over estimate, and award vendor.

---

## 14. Authentication & API Access

### Web Login

Navigate to `/login`. Enter your password. Session is maintained via cookie.

### API Bearer Token

For headless/scripted access, use a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/shots/101
```

Tokens are configured in **Settings → api_token**.

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/shots/<ep>` | All shots for an episode |
| `POST` | `/api/shots` | Create a new shot |
| `PUT` | `/api/shots/<id>` | Update a shot |
| `DELETE` | `/api/shots/<id>` | Delete a shot |
| `POST` | `/api/import/shots` | Import shots from Excel |
| `POST` | `/api/import/shots/preview` | Dry-run preview of import |
| `POST` | `/api/import/invoices` | Import invoice log |
| `GET` | `/api/jobs/<job_id>` | Background job status |
| `POST` | `/api/llm/cost_est` | LLM cost estimate for a shot |
| `POST` | `/api/llm/vfx_desc` | LLM VFX description |

---

## 15. Key Reference Tables

### Shot Types

| Type | Description |
|------|-------------|
| CG | Full CG element or environment |
| Comp | Compositing (layers, integration) |
| Roto | Rotoscoping |
| Paint | Wire removal, clean-up |
| Grade | Digital colour grade assist |
| Crowd | Crowd simulation / duplication |
| Extension | Set or environment extension |
| Creature | CG creature / character |
| FX | Practical or CG effects (fire, water, smoke) |
| Title | Title card / graphic |

### Complexity Levels

| Level | Typical Indicators |
|-------|--------------------|
| SIMPLE | Single-layer comp, static shot, clean plate |
| MEDIUM | 2–5 elements, camera movement, moderate interaction |
| HEAVY | Full CG environment, creature, 5+ element comp, simulation |

### Episode Risk Status

| Status | Score Range | Action |
|--------|------------|--------|
| SAFE | 0.00–0.25 | No action needed |
| WATCH | 0.25–0.50 | Review vendor capacity |
| AT RISK | 0.50–0.75 | Escalate to production |
| HIGH RISK | 0.75–1.00 | Immediate mitigation plan |

### Import Modes

| Mode | Behavior |
|------|----------|
| Upsert | Add new rows; update existing rows matched by SC + EP |
| Append | Add only new rows; skip rows that already exist |
| Replace | Delete all existing shots for the episode; insert fresh from file |

### Database Files

| File | Location | Contents |
|------|----------|---------|
| `projects.db` | Root | Master project registry |
| `*.vfxdb` | `projects/` | Per-project episode, shot, vendor, invoice data |
| `job_states/*.json` | `job_states/` | Background job status (auto-cleaned after completion) |

---

## Typical Workflow

```
1. Launch app → python launch.py
2. Create project → Home → New Project
3. Configure vendors → /vendor-registry (add regions, FX rates, rebates)
4. Set vendor capacity → /vendor-tracker
5. Import shots → /ep/101 → Import Shots (upsert mode)
6. LLM enrichment → runs automatically during import if LLM is configured
7. Enter bids → /bidcompare (one bid per vendor per scene)
8. Run optimizer → /optimizer → compute lowest-cost assignments
9. Award vendors → update AWARD VENDOR on shots
10. Track actuals → update EFC as vendor invoices arrive
11. Import invoice log → Import → Invoices
12. Monitor risk → /dashboard (risk status per episode)
13. Finance reporting → /reports or /distribution
14. Audit changes → /audit
```

---

*MACHIAVELLI_a004 — VFX Budget System*
*Path: C:\Users\gderc\OneDrive\Documents\DATABASE\VFX_SW_S1\11_AUTOMATION\MACHIAVELLI_a004*
