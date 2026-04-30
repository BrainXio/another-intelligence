"""Tests for MemoryValueIndex and PreferencePair."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from another_intelligence.memory.pairs import PreferencePairExporter
from another_intelligence.memory.preference_pair import PreferencePair
from another_intelligence.memory.value_index import MemoryValueIndex
from another_intelligence.rpe.telemetry import TelemetryRecord, TelemetryRecorder


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


def _make_telemetry_record(
    decision_id: str,
    query: str = "test",
    options: list[str] | None = None,
    rpe: float = 0.5,
) -> TelemetryRecord:
    opts = options or ["a", "b", "c"]
    idx = 0
    return TelemetryRecord(
        decision_id=decision_id,
        query=query,
        options=opts,
        expected_values=[0.5, 0.5, 0.5],
        valences=[0.1, 0.1, 0.1],
        go_scores=[0.6, 0.6, 0.6],
        accumulated_evidence=[0.6, 0.6, 0.6],
        chosen_idx=idx,
        chosen_action=opts[idx],
        expected_outcome=0.6,
        expected=0.6,
        actual=0.6 + rpe,
        rpe=rpe,
        memory_key=opts[idx],
        memory_value_after=0.05,
    )


class TestPreferencePairExporter:
    def test_export_writes_jsonl_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = TelemetryRecorder(directory=tmpdir)
            rec.record(_make_telemetry_record("d1", rpe=0.5))
            rec.record(_make_telemetry_record("d2", rpe=0.8))
            exporter = PreferencePairExporter(rec)
            result = exporter.export(output_dir=Path(tmpdir) / "qlora-pairs")
            assert result["exported"] == 2
            assert result["skipped"] == 0
            dataset = Path(result["output_dir"]) / "dataset.jsonl"
            assert dataset.exists()

    def test_min_abs_rpe_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = TelemetryRecorder(directory=tmpdir)
            rec.record(_make_telemetry_record("d1", rpe=0.05))
            rec.record(_make_telemetry_record("d2", rpe=0.5))
            exporter = PreferencePairExporter(rec)
            result = exporter.export(
                output_dir=Path(tmpdir) / "qlora-pairs",
                min_abs_rpe=0.3,
            )
            assert result["exported"] == 1
            assert result["skipped"] == 1

    def test_limit_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = TelemetryRecorder(directory=tmpdir)
            for i in range(10):
                rec.record(_make_telemetry_record(f"d{i}", rpe=0.5))
            exporter = PreferencePairExporter(rec)
            result = exporter.export(
                output_dir=Path(tmpdir) / "qlora-pairs",
                limit=3,
            )
            assert result["exported"] == 3

    def test_empty_records_produces_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = TelemetryRecorder(directory=tmpdir)
            exporter = PreferencePairExporter(rec)
            result = exporter.export(output_dir=Path(tmpdir) / "qlora-pairs")
            assert result["exported"] == 0

    def test_rejected_excludes_chosen(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = TelemetryRecorder(directory=tmpdir)
            rec.record(_make_telemetry_record("d1", options=["x", "y", "z"], rpe=0.5))
            exporter = PreferencePairExporter(rec)
            result = exporter.export(output_dir=Path(tmpdir) / "qlora-pairs")
            assert result["exported"] == 1
            data = json.loads(Path(result["files"][0]).read_text())
            assert data["chosen"] == "x"
            assert "x" not in data["rejected"]
            assert len(data["rejected"]) == 2
