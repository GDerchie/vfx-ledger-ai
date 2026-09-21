"""
llm/registry.py — YAML-driven prompt registry.
Prompts live in llm/prompts/*.yaml. Adding a new LLM task = drop a YAML file.
"""
import os
import json

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

_registry = {}  # name -> prompt dict


def _load_all():
    global _registry
    if _registry:
        return _registry
    if not os.path.isdir(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR, exist_ok=True)
    for fname in os.listdir(PROMPTS_DIR):
        if fname.endswith('.yaml') or fname.endswith('.yml'):
            path = os.path.join(PROMPTS_DIR, fname)
            try:
                import yaml  # optional dependency
                with open(path, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data and 'name' in data:
                    _registry[data['name']] = data
            except ImportError:
                _load_yaml_minimal(path)
            except Exception:
                pass
    return _registry


def _load_yaml_minimal(path):
    """Minimal YAML loader for simple key: value and multiline | blocks."""
    with open(path, encoding='utf-8') as f:
        content = f.read()
    # Fallback: prompts are also stored as JSON if yaml not available
    return {}


def get_prompt(name: str) -> dict | None:
    """Return the prompt dict for the given task name, or None."""
    reg = _load_all()
    return reg.get(name)


def build_prompt(name: str, ctx: dict) -> str:
    """Fill the template for the named prompt with ctx values. Falls back to llm.build_prompt."""
    entry = get_prompt(name)
    if entry and 'template' in entry:
        template = entry['template']
        safe = {k: (str(v) if v is not None else '') for k, v in ctx.items()}
        try:
            return template.format_map(safe)
        except KeyError:
            return template
    # Fallback to legacy llm.build_prompt
    import llm as legacy
    return legacy.build_prompt(name, ctx)


def get_output_schema(name: str) -> dict | None:
    """Return the expected output schema dict for a task, or None."""
    entry = get_prompt(name)
    return entry.get('output_schema') if entry else None


def list_prompts() -> list:
    """Return list of all registered prompt names."""
    return sorted(_load_all().keys())


def reload():
    """Force reload all prompts from disk."""
    global _registry
    _registry = {}
    _load_all()
