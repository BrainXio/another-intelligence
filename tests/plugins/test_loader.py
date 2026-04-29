"""Tests for PluginLoader discovery and lifecycle."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from another_intelligence.plugins import Plugin, PluginLoader


class DisplayPlugin(Plugin):
    name = "Display"
    version = "0.1.0"
    capabilities = ["display.render"]

    async def load(self, brain) -> None:
        self.brain = brain


class VoicePlugin(Plugin):
    name = "Voice"
    version = "0.2.0"
    capabilities = ["voice.tts"]

    async def load(self, brain) -> None:
        self.brain = brain

    async def unload(self) -> None:
        self.brain = None


class BrokenPlugin(Plugin):
    name = "Broken"

    async def load(self, brain) -> None:
        raise RuntimeError("load failed")

    async def unload(self) -> None:
        raise RuntimeError("unload failed")

    async def on_event(self, event) -> None:
        raise RuntimeError("event failed")


class TestPluginLoader:
    def test_empty_loader(self):
        loader = PluginLoader(plugin_dirs=[])
        classes = loader.discover()
        assert classes == []

    def test_directory_discovery(self, tmp_path: Path):
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text(
            "from another_intelligence.plugins import Plugin\n"
            "class MyPlugin(Plugin):\n"
            "    name = 'MyPlugin'\n"
            "    capabilities = ['my.cap']\n"
            "    async def load(self, brain): self.b = brain\n"
        )
        loader = PluginLoader(plugin_dirs=[tmp_path])
        classes = loader.discover()
        assert len(classes) == 1
        assert classes[0].name == "MyPlugin"

    @pytest.mark.asyncio
    async def test_load_all(self):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [DisplayPlugin, VoicePlugin]
        plugins = await loader.load_all("brain")
        assert len(plugins) == 2
        assert plugins[0].brain == "brain"
        assert plugins[1].brain == "brain"

    @pytest.mark.asyncio
    async def test_load_all_skips_broken(self, caplog):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [BrokenPlugin, DisplayPlugin]
        with caplog.at_level("ERROR", logger="another_intelligence.plugins.loader"):
            plugins = await loader.load_all("brain")
        assert len(plugins) == 1
        assert plugins[0].name == "Display"
        assert "Broken" in caplog.text

    @pytest.mark.asyncio
    async def test_unload_all(self):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [VoicePlugin]
        plugins = await loader.load_all("brain")
        assert len(plugins) == 1
        await loader.unload_all()
        assert plugins[0].brain is None

    @pytest.mark.asyncio
    async def test_dispatch_event(self):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [DisplayPlugin]
        plugins = await loader.load_all("brain")
        event = MagicMock()
        await loader.dispatch_event(event)
        assert plugins[0].brain == "brain"  # load ran

    @pytest.mark.asyncio
    async def test_dispatch_event_skips_broken(self, caplog):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [BrokenPlugin]
        with caplog.at_level("ERROR", logger="another_intelligence.plugins.loader"):
            plugins = await loader.load_all("brain")
        assert len(plugins) == 0
        event = MagicMock()
        await loader.dispatch_event(event)
        assert "event failed" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_plugins_for_capability(self):
        loader = PluginLoader(plugin_dirs=[])
        loader._plugin_classes = [DisplayPlugin, VoicePlugin]
        await loader.load_all("brain")
        display = loader.get_plugins_for_capability("display.render")
        voice = loader.get_plugins_for_capability("voice.tts")
        assert len(display) == 1
        assert display[0].name == "Display"
        assert len(voice) == 1
        assert voice[0].name == "Voice"

    def test_scan_for_changes(self, tmp_path: Path):
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("x = 1")
        loader = PluginLoader(plugin_dirs=[tmp_path])
        assert loader.scan_for_changes() is True
        assert loader.scan_for_changes() is False

    def test_scan_for_changes_missing_dir(self):
        loader = PluginLoader(plugin_dirs=["/nonexistent/path"])
        assert loader.scan_for_changes() is False
