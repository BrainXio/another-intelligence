"""Tests for Plugin base class."""

import pytest

from another_intelligence.plugins import Plugin


class DummyPlugin(Plugin):
    name = "Dummy"
    version = "1.0.0"
    requires = ["display.eyes"]
    capabilities = ["display.render.dummy"]

    def __init__(self) -> None:
        self.loaded = False
        self.unloaded = False
        self.events: list = []

    async def load(self, brain) -> None:
        self.loaded = True

    async def unload(self) -> None:
        self.unloaded = True

    async def on_event(self, event) -> None:
        self.events.append(event)


class TestPlugin:
    def test_class_attributes(self):
        assert DummyPlugin.name == "Dummy"
        assert DummyPlugin.version == "1.0.0"
        assert DummyPlugin.requires == ["display.eyes"]
        assert DummyPlugin.capabilities == ["display.render.dummy"]

    @pytest.mark.asyncio
    async def test_lifecycle(self):
        plugin = DummyPlugin()
        brain = object()
        await plugin.load(brain)
        assert plugin.loaded is True

        await plugin.unload()
        assert plugin.unloaded is True

    @pytest.mark.asyncio
    async def test_on_event(self):
        plugin = DummyPlugin()
        event = {"type": "test"}
        await plugin.on_event(event)
        assert plugin.events == [event]

    def test_provide_tools_default(self):
        plugin = DummyPlugin()
        assert plugin.provide_tools() == []
