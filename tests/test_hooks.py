"""Tests for the hook system (registry, runner, models)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from another_intelligence.events import BrainRegionActivated, SessionStart
from another_intelligence.hooks.models import HookConfig, HookResult, HookType
from another_intelligence.hooks.registry import HookRegistry
from another_intelligence.hooks.runner import HookRunner
from another_intelligence.permissions.engine import PermissionEngine


def _test_hook_callable(event: Any) -> dict[str, Any]:
    """Simple Python hook callable for testing."""
    return {"received": event.model_dump()}


async def _test_async_hook_callable(event: Any) -> dict[str, Any]:
    """Simple async Python hook callable for testing."""
    return {"async_received": event.model_dump()}


class TestHookType:
    def test_values(self):
        assert HookType.SHELL == "shell"
        assert HookType.PYTHON == "python"
        assert HookType.MCP == "mcp"


class TestHookConfig:
    def test_valid_shell(self):
        config = HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo hello")
        assert config.command == "echo hello"
        assert not config.critical

    def test_valid_python(self):
        config = HookConfig(
            event_type="PreToolUse",
            type=HookType.PYTHON,
            entry_point="another_intelligence.hooks.pre_tool_guard",
        )
        assert config.entry_point == "another_intelligence.hooks.pre_tool_guard"

    def test_valid_mcp(self):
        config = HookConfig(
            event_type="PostToolUse",
            type=HookType.MCP,
            server="memory",
            tool="inject",
        )
        assert config.server == "memory"
        assert config.tool == "inject"

    def test_critical_flag(self):
        config = HookConfig(
            event_type="PreToolUse",
            type=HookType.SHELL,
            command="echo ok",
            critical=True,
        )
        assert config.critical is True

    def test_shell_missing_command_raises(self):
        with pytest.raises(ValueError, match="shell hooks require"):
            HookConfig(event_type="SessionStart", type=HookType.SHELL)

    def test_python_missing_entry_point_raises(self):
        with pytest.raises(ValueError, match="python hooks require"):
            HookConfig(event_type="SessionStart", type=HookType.PYTHON)

    def test_mcp_missing_server_raises(self):
        with pytest.raises(ValueError, match="mcp hooks require"):
            HookConfig(event_type="SessionStart", type=HookType.MCP, tool="inject")

    def test_mcp_missing_tool_raises(self):
        with pytest.raises(ValueError, match="mcp hooks require"):
            HookConfig(event_type="SessionStart", type=HookType.MCP, server="memory")


class TestHookRegistry:
    def test_register_and_get(self):
        registry = HookRegistry()
        config = HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo hi")
        registry.register(config)
        assert registry.get_hooks("SessionStart") == [config]

    def test_get_empty(self):
        registry = HookRegistry()
        assert registry.get_hooks("UnknownEvent") == []

    def test_unregister(self):
        registry = HookRegistry()
        config = HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo hi")
        registry.register(config)
        assert registry.unregister("SessionStart", config) is True
        assert registry.get_hooks("SessionStart") == []

    def test_unregister_missing(self):
        registry = HookRegistry()
        config = HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo hi")
        assert registry.unregister("SessionStart", config) is False

    def test_clear(self):
        registry = HookRegistry()
        registry.register(HookConfig(event_type="A", type=HookType.SHELL, command="echo a"))
        registry.register(HookConfig(event_type="B", type=HookType.SHELL, command="echo b"))
        registry.clear()
        assert registry.get_hooks("A") == []
        assert registry.get_hooks("B") == []

    def test_all_event_types(self):
        registry = HookRegistry()
        registry.register(HookConfig(event_type="A", type=HookType.SHELL, command="echo a"))
        registry.register(HookConfig(event_type="B", type=HookType.SHELL, command="echo b"))
        assert registry.all_event_types() == {"A", "B"}

    def test_load_from_dict(self):
        registry = HookRegistry()
        registry.load_from_dict(
            {
                "hooks": {
                    "SessionStart": [
                        {"type": "shell", "command": "echo start"},
                    ],
                    "SessionEnd": [
                        {"type": "python", "entry_point": "mod.fn"},
                    ],
                }
            }
        )
        start_hooks = registry.get_hooks("SessionStart")
        assert len(start_hooks) == 1
        assert start_hooks[0].type == HookType.SHELL
        end_hooks = registry.get_hooks("SessionEnd")
        assert len(end_hooks) == 1
        assert end_hooks[0].type == HookType.PYTHON

    def test_load_from_settings_file(self):
        registry = HookRegistry()
        data = {
            "hooks": {"PreToolUse": [{"type": "shell", "command": "echo guard", "critical": True}]}
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            registry.load_from_settings(path)
            hooks = registry.get_hooks("PreToolUse")
            assert len(hooks) == 1
            assert hooks[0].critical is True
        finally:
            Path(path).unlink()

    def test_load_merged(self):
        global_data = {"hooks": {"SessionStart": [{"type": "shell", "command": "echo global"}]}}
        project_data = {"hooks": {"SessionStart": [{"type": "shell", "command": "echo project"}]}}
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as gf,
            tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as pf,
        ):
            json.dump(global_data, gf)
            global_path = gf.name
            json.dump(project_data, pf)
            project_path = pf.name
        try:
            registry = HookRegistry()
            registry.load_merged(global_path, project_path)
            hooks = registry.get_hooks("SessionStart")
            assert len(hooks) == 2
            assert hooks[0].command == "echo global"
            assert hooks[1].command == "echo project"
        finally:
            Path(global_path).unlink()
            Path(project_path).unlink()


class TestHookRunner:
    @pytest.fixture
    def registry(self):
        return HookRegistry()

    @pytest.fixture
    def runner(self, registry):
        return HookRunner(registry)

    @pytest.mark.asyncio
    async def test_run_hooks_empty(self, runner):
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert results == []

    @pytest.mark.asyncio
    async def test_run_shell_hook(self, registry, runner):
        shell_cmd = 'python3 -c "import sys, json; print(json.dumps({\\"ok\\": True}))"'
        registry.register(
            HookConfig(event_type="SessionStart", type=HookType.SHELL, command=shell_cmd)
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].output == {"ok": True}
        assert results[0].duration_ms >= 0

    @pytest.mark.asyncio
    async def test_run_python_sync_hook(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="BrainRegionActivated",
                type=HookType.PYTHON,
                entry_point="tests.test_hooks._test_hook_callable",
            )
        )
        event = BrainRegionActivated(region="strategist")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is True
        assert "received" in results[0].output

    @pytest.mark.asyncio
    async def test_run_python_async_hook(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="BrainRegionActivated",
                type=HookType.PYTHON,
                entry_point="tests.test_hooks._test_async_hook_callable",
            )
        )
        event = BrainRegionActivated(region="executor")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is True
        assert "async_received" in results[0].output

    @pytest.mark.asyncio
    async def test_run_mcp_hook_not_implemented(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="PostToolUse",
                type=HookType.MCP,
                server="memory",
                tool="inject",
            )
        )
        from another_intelligence.events import PostToolUse

        event = PostToolUse(tool_name="fs.read", success=True)
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is False
        assert (
            "NotImplementedError" in results[0].error
            or "require the MCP client" in results[0].error
        )

    @pytest.mark.asyncio
    async def test_critical_hook_failure_raises(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="SessionStart",
                type=HookType.SHELL,
                command="exit 1",
                critical=True,
            )
        )
        event = SessionStart(session_id="s1")
        with pytest.raises(RuntimeError, match="Critical hook failed"):
            await runner.run_hooks(event)

    @pytest.mark.asyncio
    async def test_non_critical_hook_failure_logged(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="SessionStart",
                type=HookType.SHELL,
                command="exit 1",
                critical=False,
            )
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is False
        assert "exited 1" in results[0].error

    @pytest.mark.asyncio
    async def test_permission_denied(self, registry):
        engine = PermissionEngine()
        runner = HookRunner(registry, permission_engine=engine)
        registry.register(
            HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo ok")
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is False
        assert "Permission denied" in results[0].error

    @pytest.mark.asyncio
    async def test_permission_granted(self, registry):
        engine = PermissionEngine()
        runner = HookRunner(registry, permission_engine=engine)
        registry.register(
            HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo ok")
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is False  # denied by default policy

    @pytest.mark.asyncio
    async def test_permission_allowed(self, registry):
        engine = PermissionEngine()
        runner = HookRunner(registry, permission_engine=engine)
        registry.register(
            HookConfig(event_type="SessionStart", type=HookType.SHELL, command="echo ok")
        )
        # grant the hook.execute.SessionStart capability
        from another_intelligence.permissions.engine import Grant

        engine._config.grants.append(
            Grant(capability="hook.execute.SessionStart", allowed_by="test")
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].output.strip() == "ok"

    @pytest.mark.asyncio
    async def test_runner_log(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="SessionStart",
                type=HookType.SHELL,
                command="echo logged",
            )
        )
        event = SessionStart(session_id="s1")
        await runner.run_hooks(event)
        assert len(runner.log) == 1
        assert runner.log[0].output.strip() == "logged"
        runner.clear_log()
        assert runner.log == []

    @pytest.mark.asyncio
    async def test_python_hook_not_found(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="SessionStart",
                type=HookType.PYTHON,
                entry_point="nonexistent.module.function",
            )
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is False
        assert "No module named" in results[0].error

    @pytest.mark.asyncio
    async def test_shell_hook_invalid_json_stdout(self, registry, runner):
        registry.register(
            HookConfig(
                event_type="SessionStart",
                type=HookType.SHELL,
                command="echo 'not json'",
            )
        )
        event = SessionStart(session_id="s1")
        results = await runner.run_hooks(event)
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].output == "not json"


class TestHookResult:
    def test_defaults(self):
        result = HookResult(success=True)
        assert result.success is True
        assert result.output is None
        assert result.error is None
        assert result.duration_ms == 0.0
        assert result.config is None
