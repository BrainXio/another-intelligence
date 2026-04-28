"""Tests for MemoryValueIndex and PreferencePair."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from another_intelligence.memory.preference_pair import PreferencePair
from another_intelligence.memory.value_index import MemoryValueIndex


class TestMemoryValueIndexInit:
    def test_default_values(self):
        idx = MemoryValueIndex()
        assert idx.get("any_key") == 0.0
        assert idx.keys() == set()

    def test_custom_training_dir(self):
        idx = MemoryValueIndex(training_dir="/tmp/test_datasets")
        assert idx._training_dir == Path("/tmp/test_datasets")


class TestMemoryValueIndexUpdate:
    def test_update_starts_from_zero(self):
        idx = MemoryValueIndex()
        new_value = idx.update("opt_a", rpe=0.5)
        assert new_value == pytest.approx(0.05)
        assert idx.get("opt_a") == pytest.approx(0.05)

    def test_update_accumulates(self):
        idx = MemoryValueIndex()
        idx.update("opt_a", rpe=0.5)
        new_value = idx.update("opt_a", rpe=0.5)
        assert new_value == pytest.approx(0.10)
        assert idx.get("opt_a") == pytest.approx(0.10)

    def test_negative_rpe_decreases_value(self):
        idx = MemoryValueIndex()
        new_value = idx.update("opt_a", rpe=-1.0)
        assert new_value == pytest.approx(-0.1)

    def test_custom_learning_rate(self):
        idx = MemoryValueIndex(learning_rate=0.5)
        new_value = idx.update("opt_a", rpe=1.0)
        assert new_value == pytest.approx(0.5)


class TestMemoryValueIndexSnapshot:
    def test_snapshot_returns_copy(self):
        idx = MemoryValueIndex()
        idx.update("a", 1.0)
        snap = idx.snapshot()
        snap["a"] = 99.0
        assert idx.get("a") == pytest.approx(0.1)

    def test_keys_returns_all_keys(self):
        idx = MemoryValueIndex()
        idx.update("a", 1.0)
        idx.update("b", 1.0)
        assert idx.keys() == {"a", "b"}


class TestMemoryValueIndexExport:
    def test_export_when_rpe_above_threshold(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.3)
        path = idx.export_preference_pair(
            context="test_ctx",
            chosen="a",
            rejected=["b", "c"],
            rpe=0.5,
        )
        assert path is not None
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["chosen"] == "a"
        assert data["rejected"] == ["b", "c"]
        assert data["rpe"] == pytest.approx(0.5)
        assert data["context"] == "test_ctx"
        assert "timestamp" in data

    def test_no_export_when_rpe_below_threshold(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.3)
        path = idx.export_preference_pair(
            context="test_ctx",
            chosen="a",
            rejected=["b"],
            rpe=0.2,
        )
        assert path is None

    def test_no_export_when_rpe_exactly_at_threshold(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.3)
        path = idx.export_preference_pair(
            context="test_ctx",
            chosen="a",
            rejected=["b"],
            rpe=0.3,
        )
        assert path is None

    def test_export_creates_directory(self, tmp_path: Path):
        nested = tmp_path / "nested" / "datasets"
        idx = MemoryValueIndex(training_dir=str(nested), export_threshold=0.0)
        path = idx.export_preference_pair(
            context="ctx",
            chosen="a",
            rejected=["b"],
            rpe=0.1,
        )
        assert path is not None
        assert nested.exists()

    def test_export_negative_rpe(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.0)
        path = idx.export_preference_pair(
            context="ctx",
            chosen="a",
            rejected=["b"],
            rpe=-0.5,
        )
        assert path is not None
        data = json.loads(path.read_text())
        assert data["rpe"] == pytest.approx(-0.5)


class TestMemoryValueIndexReset:
    def test_reset_clears_values(self):
        idx = MemoryValueIndex()
        idx.update("a", 1.0)
        idx.reset()
        assert idx.get("a") == 0.0
        assert idx.keys() == set()

    def test_reset_returns_self(self):
        idx = MemoryValueIndex()
        result = idx.reset()
        assert result is idx


class TestPreferencePairSerialization:
    def test_round_trip(self):
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        pair = PreferencePair(
            context="ctx",
            chosen="a",
            rejected=["b"],
            rpe=0.5,
            timestamp=now,
        )
        d = pair.to_dict()
        restored = PreferencePair.from_dict(d)
        assert restored.context == "ctx"
        assert restored.chosen == "a"
        assert restored.rejected == ["b"]
        assert restored.rpe == pytest.approx(0.5)
        assert restored.timestamp == now

    def test_write_and_read(self, tmp_path: Path):
        pair = PreferencePair(
            context="test_ctx",
            chosen="x",
            rejected=["y", "z"],
            rpe=-0.2,
        )
        path = pair.write(tmp_path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["chosen"] == "x"
        assert data["rejected"] == ["y", "z"]

    def test_filename_includes_context_and_timestamp(self, tmp_path: Path):
        pair = PreferencePair(context="hello world", chosen="a", rejected=["b"], rpe=0.1)
        path = pair.write(tmp_path)
        assert "hello_world" in path.name or "hello" in path.name
