"""
llm/__init__.py — Re-export everything from the original llm.py so that
existing code using `import llm as llm_module` continues to work unchanged.
The original llm.py content lives in llm/_legacy.py.
"""
from llm._legacy import (
    DEFAULT_CONFIG,
    SYSTEM_PROMPT,
    build_prompt,
    load_config,
    save_config,
    LLMClient,
    test_connection,
)

__all__ = [
    'DEFAULT_CONFIG', 'SYSTEM_PROMPT',
    'build_prompt', 'load_config', 'save_config',
    'LLMClient', 'test_connection',
]
