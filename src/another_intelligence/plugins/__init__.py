"""Plugin system for Another-Intelligence."""

from another_intelligence.plugins.loader import PluginLoader
from another_intelligence.plugins.plugin import Plugin

__all__ = [
    "Plugin",
    "PluginLoader",
]
