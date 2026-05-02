"""Plugin discovery mechanisms."""

from __future__ import annotations

import importlib.util
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from another_intelligence.paths import PLUGINS_DIR
from another_intelligence.plugins.plugin import Plugin

logger = logging.getLogger(__name__)


def _discover_entry_points() -> list[type[Plugin]]:
    """Discover plugins via importlib.metadata entry points.

    Returns:
        List of Plugin subclasses.
    """
    plugins: list[type[Plugin]] = []
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return plugins

    eps = entry_points()
    group = eps.select(group="another_intelligence.plugins")
    for ep in group:
        try:
            cls = ep.load()
            if issubclass(cls, Plugin):
                plugins.append(cls)
        except (ImportError, AttributeError, TypeError):
            logger.exception("Failed to load plugin entry point: %s", ep.name)
    return plugins


def _discover_directory(path: Path | str) -> list[type[Plugin]]:
    """Discover plugins in a filesystem directory.

    Each ``.py`` file is loaded as a module and scanned for Plugin subclasses.

    Args:
        path: Directory to scan.

    Returns:
        List of Plugin subclasses.
    """
    plugins: list[type[Plugin]] = []
    dir_path = Path(path)
    if not dir_path.exists() or not dir_path.is_dir():
        return plugins

    for file in sorted(dir_path.glob("*.py")):
        if file.name.startswith("_"):
            continue
        module_name = f"_brainxio_plugin_{file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            for obj_name in dir(module):
                obj = getattr(module, obj_name)
                if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                    plugins.append(obj)
        except (ImportError, OSError, SyntaxError, TypeError):
            logger.exception("Failed to load plugin file: %s", file)
    return plugins


class PluginLoader:
    """Discovers, registers, and manages plugin lifecycle.

    Supports two discovery sources:

    1. Python entry points in the ``another_intelligence.plugins`` group.
    2. A configurable plugin directory (default ``~/.brainxio/plugins/``).
    """

    def __init__(self, plugin_dirs: Sequence[Path | str] | None = None) -> None:
        self._plugin_classes: list[type[Plugin]] = []
        self._plugins: list[Plugin] = []
        self._plugin_dirs = list(plugin_dirs) if plugin_dirs else [PLUGINS_DIR]
        self._capability_map: dict[str, list[Plugin]] = {}
        self._mtimes: dict[Path, float] = {}

    def discover(self) -> list[type[Plugin]]:
        """Run discovery across all sources.

        Returns:
            List of discovered Plugin subclasses.
        """
        self._plugin_classes = _discover_entry_points()
        for directory in self._plugin_dirs:
            self._plugin_classes.extend(_discover_directory(directory))
        return list(self._plugin_classes)

    async def load_all(self, brain: Any) -> list[Plugin]:
        """Instantiate and load all discovered plugins.

        Args:
            brain: The DigitalBrain instance.

        Returns:
            List of loaded Plugin instances.
        """
        self._plugins = []
        self._capability_map = {}
        classes = self._plugin_classes if self._plugin_classes else self.discover()
        for cls in classes:
            instance = cls()
            try:
                await instance.load(brain)
                self._plugins.append(instance)
                for cap in instance.capabilities:
                    self._capability_map.setdefault(cap, []).append(instance)
            except (RuntimeError, TypeError, ValueError, OSError, ImportError):
                logger.exception("Plugin %s failed to load", cls.__name__)
        return list(self._plugins)

    async def unload_all(self) -> None:
        """Unload all loaded plugins in reverse order."""
        for plugin in reversed(self._plugins):
            try:
                await plugin.unload()
            except (RuntimeError, TypeError, ValueError, OSError):
                logger.exception("Plugin %s failed to unload", plugin.name)
        self._plugins.clear()
        self._capability_map.clear()

    async def dispatch_event(self, event: Any) -> None:
        """Dispatch an event to all loaded plugins.

        Args:
            event: A BrainEvent subclass instance.
        """
        for plugin in self._plugins:
            try:
                await plugin.on_event(event)
            except (RuntimeError, TypeError, ValueError, OSError):
                logger.exception("Plugin %s failed to handle event", plugin.name)

    def get_plugins_for_capability(self, capability: str) -> list[Plugin]:
        """Return loaded plugins providing a given capability.

        Args:
            capability: Capability string (e.g. ``display.render.gtk``).

        Returns:
            Matching Plugin instances.
        """
        return list(self._capability_map.get(capability, []))

    def scan_for_changes(self) -> bool:
        """Check whether any plugin file on disk has changed.

        Useful for basic hot-reload during development.

        Returns:
            True if any file mtime differs from the last recorded value.
        """
        changed = False
        for directory in self._plugin_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            for file in dir_path.glob("*.py"):
                mtime = file.stat().st_mtime
                if self._mtimes.get(file) != mtime:
                    self._mtimes[file] = mtime
                    changed = True
        return changed

    async def reload(self, brain: Any) -> None:
        """Unload all plugins and re-discover / reload them.

        Args:
            brain: The DigitalBrain instance.
        """
        await self.unload_all()
        self.discover()
        await self.load_all(brain)
