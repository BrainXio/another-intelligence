"""Tests for the MetricsCollector observability module."""

import json
import tempfile
from pathlib import Path

import pytest

from another_intelligence.events import (
    BrainRegionActivated,
    ContextWindowChanged,
    RPEUpdated,
)
from another_intelligence.metrics import MetricsCollector
from another_intelligence.state import ActivityPhase


class TestMetricsCollectorInit:
    """Construction and default state."""

    def test_default_state(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        assert metrics.latest_rpe is None
        assert metrics.latest_context is None
        assert metrics.active_regions == set()
        assert metrics.region_history == []
        assert metrics.uptime_seconds >= 0.0

    def test_custom_log_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            metrics = MetricsCollector(
                log_file=tmp.name,
                enable_system_metrics=False,
            )
            assert metrics._log_file == Path(tmp.name)


class TestEventRecording:
    """Recording brain events updates internal state."""

    def test_region_activated(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        event = BrainRegionActivated(region="strategist")
        metrics.record_event(event)
        assert "strategist" in metrics.active_regions
        assert metrics.region_history == ["strategist"]

    def test_multiple_regions(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        for region in ["strategist", "executor", "reflex"]:
            metrics.record_event(BrainRegionActivated(region=region))
        assert metrics.active_regions == {"strategist", "executor", "reflex"}
        assert metrics.region_history == ["strategist", "executor", "reflex"]

    def test_rpe_updated(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        metrics.record_event(RPEUpdated(expected=0.5, actual=0.8))
        assert metrics.latest_rpe == pytest.approx(0.3)

    def test_context_window_changed(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        metrics.record_event(ContextWindowChanged(total_tokens=1024, max_tokens=4096))
        ctx = metrics.latest_context
        assert ctx is not None
        assert ctx["total_tokens"] == 1024
        assert ctx["max_tokens"] == 4096
        assert ctx["utilization"] == 0.25

    def test_event_count_increments(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        assert metrics.snapshot()["event_count"] == 0
        metrics.record_event(BrainRegionActivated(region="strategist"))
        assert metrics.snapshot()["event_count"] == 1


class TestSnapshot:
    """Full metrics snapshot."""

    def test_snapshot_structure(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        snap = metrics.snapshot()
        assert "uptime_seconds" in snap
        assert "event_count" in snap
        assert "active_regions" in snap
        assert "region_history" in snap
        assert "latest_rpe" in snap
        assert "context" in snap
        assert "system" in snap
        assert "phase" in snap

    def test_snapshot_with_phase(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        snap = metrics.snapshot(phase=ActivityPhase.PROPOSING)
        assert snap["phase"] == "proposing"

    def test_snapshot_without_phase(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        snap = metrics.snapshot()
        assert snap["phase"] is None


class TestSystemMetrics:
    """System resource collection."""

    def test_disabled_returns_zero(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        sys_info = metrics.system_snapshot()
        assert sys_info["cpu_percent"] == 0.0
        assert sys_info["memory_percent"] == 0.0

    def test_enabled_returns_values(self):
        metrics = MetricsCollector(enable_system_metrics=True)
        sys_info = metrics.system_snapshot()
        assert isinstance(sys_info["cpu_percent"], float)
        assert isinstance(sys_info["memory_percent"], float)
        assert 0.0 <= sys_info["memory_percent"] <= 100.0


class TestLogPersistence:
    """Append-only JSONL event log."""

    def test_log_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            metrics = MetricsCollector(
                log_file=log_file,
                enable_system_metrics=False,
            )
            metrics.record_event(BrainRegionActivated(region="strategist"))
            assert log_file.exists()

    def test_log_is_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            metrics = MetricsCollector(
                log_file=log_file,
                enable_system_metrics=False,
            )
            metrics.record_event(BrainRegionActivated(region="executor"))
            with log_file.open("r") as fh:
                line = fh.readline()
                record = json.loads(line)
                assert "timestamp" in record
                assert "event_type" in record
                assert "payload" in record

    def test_read_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            metrics = MetricsCollector(
                log_file=log_file,
                enable_system_metrics=False,
            )
            for region in ["a", "b", "c"]:
                metrics.record_event(BrainRegionActivated(region=region))
            logs = metrics.read_log(limit=2)
            assert len(logs) == 2
            assert logs[-1]["payload"]["region"] == "c"

    def test_clear_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            metrics = MetricsCollector(
                log_file=log_file,
                enable_system_metrics=False,
            )
            metrics.record_event(BrainRegionActivated(region="x"))
            assert log_file.exists()
            metrics.clear_log()
            assert not log_file.exists()

    def test_read_empty_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            metrics = MetricsCollector(
                log_file=log_file,
                enable_system_metrics=False,
            )
            assert metrics.read_log() == []


class TestHookIntegration:
    """Integration with DigitalBrain hook system."""

    def test_as_hook(self):
        from another_intelligence.brain import DigitalBrain

        brain = DigitalBrain()
        metrics = MetricsCollector(enable_system_metrics=False)
        brain.register_hook("BrainRegionActivated", metrics.as_hook())
        brain.decide(query="test")
        assert "strategist" in metrics.active_regions
        assert len(metrics.region_history) >= 3

    def test_hook_records_rpe(self):
        from another_intelligence.brain import DigitalBrain

        brain = DigitalBrain()
        metrics = MetricsCollector(enable_system_metrics=False)
        brain.register_hook("RPEUpdated", metrics.as_hook())
        brain.decide(query="test")
        assert metrics.latest_rpe is not None
