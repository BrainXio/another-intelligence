"""Tests for the Another-Intelligence CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from another_intelligence.cli import BrainStore, main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def isolated_store(tmp_path: Path) -> BrainStore:
    return BrainStore(base_dir=tmp_path)


class TestBrainStore:
    def test_load_state_default(self, isolated_store: BrainStore) -> None:
        state = isolated_store.load_state()
        assert state["session_id"] is None
        assert state["current_phase"] == "idle"

    def test_save_and_load_state(self, isolated_store: BrainStore) -> None:
        isolated_store.save_state(
            {"session_id": "abc", "memory": {"x": 1.0}, "current_phase": "idle"}
        )
        state = isolated_store.load_state()
        assert state["session_id"] == "abc"
        assert state["memory"]["x"] == 1.0

    def test_append_and_read_events(self, isolated_store: BrainStore) -> None:
        from another_intelligence.events import SessionStart

        isolated_store.append_event(SessionStart(session_id="s1"))
        events = isolated_store.read_events("SessionStart")
        assert len(events) == 1
        assert events[0]["session_id"] == "s1"

    def test_read_events_limit(self, isolated_store: BrainStore) -> None:
        from another_intelligence.events import SessionStart

        for i in range(5):
            isolated_store.append_event(SessionStart(session_id=f"s{i}"))
        events = isolated_store.read_events("SessionStart", limit=3)
        assert len(events) == 3

    def test_clear(self, isolated_store: BrainStore) -> None:
        isolated_store.save_state({"a": 1})
        from another_intelligence.events import SessionStart

        isolated_store.append_event(SessionStart(session_id="s1"))
        isolated_store.clear()
        assert not (isolated_store._base / "brain_state.json").exists()
        assert not (isolated_store._base / "brain_activity.jsonl").exists()


class TestCliHelp:
    def test_main_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "brain" in result.output
        assert "hook" in result.output
        assert "flush" in result.output
        assert "compile" in result.output
        assert "status" in result.output
        assert "permissions" in result.output

    def test_brain_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["brain", "--help"])
        assert result.exit_code == 0
        assert "decide" in result.output

    def test_hook_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["hook", "--help"])
        assert result.exit_code == 0
        assert "session-start" in result.output
        assert "session-end" in result.output

    def test_permissions_help(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["permissions", "--help"])
        assert result.exit_code == 0
        assert "check" in result.output


class TestBrainDecide:
    def test_decide_without_options(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["brain", "decide", "what should i do"], obj={"store": store})
        assert result.exit_code == 0
        assert "Chosen:" in result.output

    def test_decide_with_options(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(
            main,
            ["brain", "decide", "choose", "-o", "a", "-o", "b"],
            obj={"store": store},
        )
        assert result.exit_code == 0
        assert "Chosen:" in result.output

    def test_decide_persists_memory(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        runner.invoke(main, ["brain", "decide", "test query"], obj={"store": store})
        state = store.load_state()
        assert state["memory"] != {}


class TestBrainRegions:
    def test_regions_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["brain", "regions"], obj={"store": store})
        assert result.exit_code == 0
        assert "No region activations" in result.output

    def test_regions_with_events(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        from another_intelligence.events import BrainRegionActivated

        store.append_event(BrainRegionActivated(region="strategist", metadata={"x": 1}))
        result = runner.invoke(main, ["brain", "regions", "-n", "5"], obj={"store": store})
        assert result.exit_code == 0
        assert "strategist" in result.output


class TestHookCommands:
    def test_session_start(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["hook", "session-start"], obj={"store": store})
        assert result.exit_code == 0
        assert "Session started:" in result.output
        state = store.load_state()
        assert state["session_id"] is not None

    def test_session_end_without_session(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["hook", "session-end"], obj={"store": store})
        assert result.exit_code != 0

    def test_session_end_with_session(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        runner.invoke(main, ["hook", "session-start"], obj={"store": store})
        result = runner.invoke(
            main, ["hook", "session-end", "--reason", "done"], obj={"store": store}
        )
        assert result.exit_code == 0
        assert "done" in result.output
        state = store.load_state()
        assert state["session_id"] is None


class TestFlush:
    def test_flush(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        store.save_state({"a": 1})
        result = runner.invoke(main, ["flush"], input="y\n", obj={"store": store})
        assert result.exit_code == 0
        assert "cleared" in result.output


class TestCompile:
    def test_compile_empty_source(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(
            main,
            ["compile", "--source-dir", str(tmp_path), "--output-dir", str(tmp_path)],
            obj={"store": store},
        )
        assert result.exit_code == 0
        assert "Compiled" in result.output


class TestStatus:
    def test_status_basic(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["status"], obj={"store": store})
        assert result.exit_code == 0
        assert "Brain Status" in result.output
        assert "none" in result.output

    def test_status_extended(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        from another_intelligence.events import SessionStart

        store.append_event(SessionStart(session_id="s1"))
        result = runner.invoke(main, ["status", "--extended"], obj={"store": store})
        assert result.exit_code == 0
        assert "SessionStart" in result.output

    def test_status_with_memory(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        store.save_state({"memory": {"proceed": 0.5}, "session_id": None, "current_phase": "idle"})
        result = runner.invoke(main, ["status"], obj={"store": store})
        assert result.exit_code == 0
        assert "proceed" in result.output


class TestPermissionsCheck:
    def test_permissions_check_deny(self, runner: CliRunner, tmp_path: Path) -> None:
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(main, ["permissions", "check", "foo.bar"], obj={"store": store})
        assert result.exit_code == 0
        assert "deny" in result.output

    def test_permissions_check_with_config(self, runner: CliRunner, tmp_path: Path) -> None:
        config = tmp_path / "settings.json"
        config.write_text(json.dumps({"permissions": {"default_policy": "allow", "grants": []}}))
        store = BrainStore(base_dir=tmp_path)
        result = runner.invoke(
            main,
            ["permissions", "check", "foo.bar", "--config", str(config)],
            obj={"store": store},
        )
        assert result.exit_code == 0
        assert "allow" in result.output
