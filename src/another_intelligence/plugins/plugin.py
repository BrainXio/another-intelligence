"""Plugin system for Another-Intelligence.

Provides typed plugin lifecycle, discovery via entry points and directories,
and capability-aware loading.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Plugin:
    """Base class for all Another-Intelligence plugins.

    Subclasses must set class attributes and implement lifecycle hooks.
    """

    name: str = ""
    version: str = "0.0.0"
    requires: list[str] = []
    capabilities: list[str] = []

    async def load(self, brain: Any) -> None:
        """Called during session start.

        Args:
            brain: The DigitalBrain instance.
        """

    async def unload(self) -> None:
        """Called during session end for cleanup."""

    async def on_event(self, event: Any) -> None:
        """Receive brain events (optional).

        Args:
            event: A BrainEvent subclass instance.
        """

    def provide_tools(self) -> list[dict[str, Any]]:
        """Return additional MCP-style tool definitions.

        Returns:
            List of tool definition dicts.
        """
        return []
