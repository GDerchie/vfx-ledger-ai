"""
llm.py — LLM client abstraction for VFX Budget System
Supports: Ollama (local) | Claude API | OpenAI-compatible API
All network calls use stdlib urllib only — no extra dependencies.
"""
import json
import os
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "provider":        "ollama",
    "ollama_model":    "qwen2.5:7b",
    "ollama_url":      "http://localhost:11434",
    "claude_model":    "claude-haiku-4-5-20251001",
    "claude_api_key":  "",
    "openai_model":    "gpt-4o-mini",
    "openai_api_key":  "",
    "openai_base_url": "https://api.openai.com/v1",
    "max_tokens":      600,
    "temperature":     0.3,
}

SYSTEM_PROMPT = (
    "You are an assistant for a professional VFX budget tracking system used on "
    "film and TV productions. Be concise and factual. Output only what is requested. "
    "Do not add explanations or preamble unless asked."
)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

def build_prompt(task: str, ctx: dict) -> str:
    """Return a filled prompt string for the given task and context dict."""
    t = {
        # ── EP Page ─────────────────────────────────────────────────────────
        "vfx_desc": (
            "Scene: SC{scene_code}  Location: {location} ({ext_int})\n"
            "Script description: {script_desc}\n"
            "Asset/Subject: {asset}\n"
            "---\n"
            "Write a concise VFX description (1–2 sentences) for the VFX supervisor. "
            "Focus on what must be created or manipulated digitally. "
            "Start directly with the description, no preamble."
        ),
        "shot_type": (
            "VFX Description: {vfx_desc}\n"
            "Script description: {script_desc}\n"
            "---\n"
            "Classify this shot into EXACTLY ONE of: "
            "CG, Comp, Roto, Paint, Grade, Crowd, Extension, Creature, FX, Title\n"
            "Reply with ONLY the type name, nothing else."
        ),
        "cost_est": (
            "VFX Type: {shot_type}\n"
            "VFX Description: {vfx_desc}\n"
            "Location: {location}\n"
            "{actuals_context}\n"
            "---\n"
            "Estimate the VFX cost for this single shot in USD.\n"
            "Reference tiers (use only when no project actuals are available above):\n"
            "  Simple (Roto/Paint/Grade): $3,000–$15,000\n"
            "  Medium (Comp/Extension/FX): $15,000–$60,000\n"
            "  Heavy (CG/Creature/Crowd): $60,000–$200,000+\n"
            "When project actuals are shown above, anchor your estimate to that range.\n"
            "Reply with ONLY valid JSON: "
            '{{"estimate": 25000, "tier": "medium", "reasoning": "one sentence"}}'
        ),
        "complexity_tag": (
            "VFX Description: {vfx_desc}\n"
            "VFX Type: {shot_type}\n"
            "---\n"
            "Rate complexity as SIMPLE, MEDIUM, or HEAVY.\n"
            "Reply with ONLY the word."
        ),
        "complexity_batch": (
            "Rate the VFX complexity of each shot below. "
            "For each line reply: ID|SIMPLE or ID|MEDIUM or ID|HEAVY\n\n"
            "{shots_list}\n"
            "---\n"
            "Reply with ONLY the ID|COMPLEXITY lines, one per line."
        ),

        # ── Distribution Page ────────────────────────────────────────────────
        "ep_narrative": (
            "Episode {ep} VFX Budget:\n"
            "  Shots: {est_shots} estimated  |  {edit_shots} in edit cut\n"
            "  EST Budget: ${est_budget}  |  EFC: ${efc_budget}  |  Variance: ${variance}\n"
            "  Status: {status}\n"
            "  Script v{script_v} / Edit v{edit_v}\n"
            "{reduction_line}"
            "---\n"
            "Write a 2-sentence producer memo summarising this episode's VFX budget status. "
            "Be direct and factual. No headings."
        ),

        # ── Assets Page ──────────────────────────────────────────────────────
        "asset_desc": (
            "Asset Name: {asset_name}\n"
            "Asset Type: {asset_type}\n"
            "Scene: SC {scene_code}  Episode: {ep}\n"
            "---\n"
            "Write a concise one-sentence description of this VFX asset for a "
            "production asset list. Start directly with the description."
        ),

        # ── Notes Page ───────────────────────────────────────────────────────
        "notes_summary": (
            "Open VFX Production Notes:\n\n"
            "{notes_text}\n"
            "---\n"
            "Summarise these notes as a concise bulleted action list. "
            "Group items under: URGENT / REVIEW / INFO. "
            "Use markdown bullets. Be brief."
        ),

        # ── Batch Operations ─────────────────────────────────────────────────
        "batch_vfx_desc": (
            "Write a one-sentence VFX description for each shot below. "
            "Focus on what must be created or manipulated digitally. "
            "For each shot reply on its own line: ID|Description\n\n"
            "{shots_list}\n"
            "---\n"
            "Reply with ONLY the ID|Description lines, one per shot, nothing else."
        ),

        # ── Vendor Recommendation ────────────────────────────────────────────
        "vendor_suggest": (
            "Shot details:\n"
            "  SC {scene_code}  EP{ep}  Type: {shot_type}  Complexity: {complexity}\n"
            "  VFX Description: {vfx_desc}\n"
            "  Est Cost: ${cost_est}\n"
            "Available vendors and their awarded totals:\n"
            "{vendor_list}\n"
            "---\n"
            "Recommend the single best vendor for this shot. "
            "Reply with ONLY valid JSON: "
            '{{"vendor": "VendorName", "reason": "one sentence"}}'
        ),

        # ── Budget Gap Analysis ───────────────────────────────────────────────
        "budget_gap_analysis": (
            "EP{ep} VFX Budget:\n"
            "  Total shots: {total_shots}  |  EST: ${total_est}  |  EFC: ${total_efc}\n"
            "  Variance: ${variance}\n\n"
            "Top over-budget shots:\n"
            "{top_shots}\n"
            "Shot type breakdown (type: count, total_est):\n"
            "{type_breakdown}\n"
            "---\n"
            "Identify the top 3 specific cost reduction opportunities for this episode. "
            "Be concrete — name shot types, vendors, or categories. "
            "Use markdown bullets. 3 bullets maximum, 1 sentence each."
        ),

        # ── Season Risk Memo ─────────────────────────────────────────────────
        "season_risk": (
            "Season VFX Budget Summary:\n"
            "  Total shots: {total_shots}  |  Season EST: ${total_est}  |  EFC: ${total_efc}\n"
            "  Season Variance: ${variance}\n\n"
            "Per-episode status:\n"
            "{ep_breakdown}\n"
            "Top vendors:\n"
            "{vendor_breakdown}\n"
            "---\n"
            "Write a 3-paragraph executive risk memo for the showrunner. "
            "Paragraph 1: overall budget status. "
            "Paragraph 2: top 2–3 specific risks by episode or vendor. "
            "Paragraph 3: recommended actions. "
            "Be direct, factual, no fluff."
        ),

        # ── Invoice Anomaly Check ─────────────────────────────────────────────
        "invoice_check": (
            "Vendor: {vendor}  Episode: {ep}\n"
            "Total Awarded: ${tot_award}\n"
            "Previously Paid: ${paid}\n"
            "This Invoice: ${amount}  ({inv_num}, {inv_date})\n"
            "Remaining after this invoice: ${remaining}\n"
            "---\n"
            "Evaluate if this invoice amount is consistent with the award and payment history. "
            "Flag any concerns. "
            "Reply with ONLY valid JSON: "
            '{{"status": "ok"|"warning"|"flag", "message": "one sentence"}}'
        ),
    }.get(task)

    if t is None:
        return ""

    # Fill placeholders safely
    safe = {k: (str(v) if v is not None else "") for k, v in ctx.items()}
    try:
        return t.format_map(safe)
    except KeyError:
        return t


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

def load_config(base_dir: str) -> dict:
    """Load LLM config. Env vars CLAUDE_API_KEY and OPENAI_API_KEY take precedence over llm_config.json."""
    cfg = dict(DEFAULT_CONFIG)
    path = os.path.join(base_dir, "llm_config.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    # Phase 2: environment variables override file-stored keys (never store secrets in JSON)
    if os.environ.get('CLAUDE_API_KEY'):
        cfg['claude_api_key'] = os.environ['CLAUDE_API_KEY']
    if os.environ.get('OPENAI_API_KEY'):
        cfg['openai_api_key'] = os.environ['OPENAI_API_KEY']
    if os.environ.get('VFX_LLM_PROVIDER'):
        cfg['provider'] = os.environ['VFX_LLM_PROVIDER']
    return cfg


def save_config(base_dir: str, cfg: dict):
    path = os.path.join(base_dir, "llm_config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

class LLMClient:
    def __init__(self, config: dict):
        self.config = config

    def stream(self, prompt: str, system: str = SYSTEM_PROMPT):
        """Yield text chunks from the configured provider."""
        p = self.config.get("provider", "ollama")
        if p == "ollama":
            yield from self._ollama(prompt, system)
        elif p == "claude":
            yield from self._claude(prompt, system)
        elif p == "openai":
            yield from self._openai(prompt, system)
        else:
            yield f"[Unknown provider: {p}]"

    # ── Ollama ──────────────────────────────────────────────────────────────
    def _ollama(self, prompt, system):
        url     = self.config.get("ollama_url", "http://localhost:11434") + "/api/generate"
        payload = json.dumps({
            "model":  self.config.get("ollama_model", "qwen2.5:7b"),
            "prompt": f"{system}\n\n{prompt}",
            "stream": True,
            "options": {
                "temperature": float(self.config.get("temperature", 0.3)),
                "num_predict": int(self.config.get("max_tokens", 600)),
            },
        }).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                for raw in resp:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                        if data.get("response"):
                            yield data["response"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except urllib.error.URLError as e:
            yield f"[Ollama connection error: {e.reason}]"
        except Exception as e:
            yield f"[Ollama error: {e}]"

    # ── Claude API ──────────────────────────────────────────────────────────
    def _claude(self, prompt, system):
        api_key = self.config.get("claude_api_key", "").strip()
        if not api_key:
            yield "[Error: Claude API key not configured — go to Settings]"
            return
        payload = json.dumps({
            "model":      self.config.get("claude_model", "claude-haiku-4-5-20251001"),
            "max_tokens": int(self.config.get("max_tokens", 600)),
            "system":     system,
            "messages":   [{"role": "user", "content": prompt}],
            "stream":     True,
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    body = line[6:]
                    if body == "[DONE]":
                        break
                    try:
                        d = json.loads(body)
                        delta = d.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            yield f"[Claude HTTP {e.code}: {err_body[:200]}]"
        except Exception as e:
            yield f"[Claude error: {e}]"

    # ── OpenAI-compatible ───────────────────────────────────────────────────
    def _openai(self, prompt, system):
        api_key  = self.config.get("openai_api_key", "").strip()
        base_url = self.config.get("openai_base_url", "https://api.openai.com/v1").rstrip("/")
        if not api_key:
            yield "[Error: OpenAI API key not configured — go to Settings]"
            return
        payload = json.dumps({
            "model":       self.config.get("openai_model", "gpt-4o-mini"),
            "max_tokens":  int(self.config.get("max_tokens", 600)),
            "temperature": float(self.config.get("temperature", 0.3)),
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": prompt},
            ],
            "stream": True,
        }).encode()
        req = urllib.request.Request(
            base_url + "/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    body = line[6:]
                    if body == "[DONE]":
                        break
                    try:
                        d     = json.loads(body)
                        delta = d["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            yield f"[OpenAI HTTP {e.code}: {err_body[:200]}]"
        except Exception as e:
            yield f"[OpenAI error: {e}]"


# ---------------------------------------------------------------------------
# Connection test
# ---------------------------------------------------------------------------

def test_connection(config: dict) -> dict:
    provider = config.get("provider", "ollama")
    if provider == "ollama":
        url = config.get("ollama_url", "http://localhost:11434") + "/api/tags"
        try:
            with urllib.request.urlopen(url, timeout=4) as r:
                data   = json.loads(r.read())
                models = [m["name"] for m in data.get("models", [])]
            return {"ok": True, "provider": "ollama", "models": models}
        except Exception as e:
            return {"ok": False, "provider": "ollama", "error": str(e)}
    elif provider in ("claude", "openai"):
        key = config.get(f"{provider}_api_key", "").strip()
        if not key:
            return {"ok": False, "provider": provider, "error": "No API key configured"}
        return {"ok": True, "provider": provider, "message": "API key present — connection not verified"}
    return {"ok": False, "error": f"Unknown provider: {provider}"}
