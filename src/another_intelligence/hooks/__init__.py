"""Hook system for Another-Intelligence.

Provides typed event hooks that can be implemented as shell commands,
Python callables, or MCP tools.
"""

from another_intelligence.hooks.models import HookConfig, HookResult, HookType
from another_intelligence.hooks.registry import HookRegistry
from another_intelligence.hooks.runner import HookRunner

__all__ = [
    "HookConfig",
    "HookRegistry",
    "HookResult",
    "HookRunner",
    "HookType",
]
