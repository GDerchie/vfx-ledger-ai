"""
services/auth.py — Authentication helpers.
"""
import json
import os
from services.db import BASE_DIR

_AUTH_CONFIG_FILE = os.path.join(BASE_DIR, 'auth_config.json')


def _load_auth_config():
    env_pw = os.environ.get('VFX_PASSWORD')
    if env_pw:
        return {'password': env_pw, 'enabled': True}
    try:
        with open(_AUTH_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {'password': '', 'enabled': False}


def _save_auth_config(cfg):
    with open(_AUTH_CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)


def check_password(pw):
    cfg = _load_auth_config()
    if not cfg.get('enabled') or not cfg.get('password'):
        return True  # auth disabled
    return pw == cfg['password']


def validate_api_token(token: str) -> bool:
    """Return True if the token matches any stored hash in auth_config."""
    import hashlib
    if not token or not token.startswith('vfx_'):
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    cfg    = _load_auth_config()
    tokens = cfg.get('api_tokens', [])
    return any(t.get('hash') == token_hash for t in tokens)
