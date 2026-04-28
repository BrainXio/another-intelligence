"""Hook registry for loading and managing hook configurations."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from another_intelligence.hooks.models import HookConfig


class HookRegistry:
    """Loads hook configurations from settings.json and manages registrations."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[HookConfig]] = defaultdict(list)

    def register(self, config: HookConfig) -> None:
        """Register a hook configuration."""
        self._hooks[config.event_type].append(config)

    def unregister(self, event_type: str, config: HookConfig) -> bool:
        """Remove a specific hook configuration."""
        configs = self._hooks.get(event_type, [])
        if config in configs:
            configs.remove(config)
            return True
        return False

    def get_hooks(self, event_type: str) -> list[HookConfig]:
        """Return all registered hooks for an event type."""
        return list(self._hooks.get(event_type, []))

    def clear(self) -> None:
        """Remove all registered hooks."""
        self._hooks.clear()

    def load_from_settings(self, path: Path | str) -> None:
        """Load hook configurations from a JSON settings file.

        Expects the file to contain a ``hooks`` key mapping event types
        to lists of hook definitions.
        """
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        hooks_data = data.get("hooks", {})
        for event_type, entries in hooks_data.items():
            for entry in entries:
                entry["event_type"] = event_type
                config = HookConfig(**entry)
                self.register(config)

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """Load hook configurations from a plain dictionary."""
        hooks_data = data.get("hooks", {})
        for event_type, entries in hooks_data.items():
            for entry in entries:
                entry["event_type"] = event_type
                config = HookConfig(**entry)
                self.register(config)

    def load_merged(self, global_path: Path | str | None, project_path: Path | str | None) -> None:
        """Load global settings first, then merge project overrides.

        Project-level hooks are appended after global hooks for each event type.
        """
        if global_path is not None and Path(global_path).exists():
            self.load_from_settings(global_path)
        if project_path is not None and Path(project_path).exists():
            self.load_from_settings(project_path)

    def all_event_types(self) -> set[str]:
        """Return all event types with at least one registered hook."""
        return set(self._hooks.keys())
