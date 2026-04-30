"""Tests for telemetry recording."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from another_intelligence.brain import DigitalBrain
from another_intelligence.events import RPEUpdated
from another_intelligence.rpe.telemetry import TelemetryAnalyzer, TelemetryRecord, TelemetryRecorder


class TestTelemetryRecord:
    def test_constructs_with_minimal_fields(self) -> None:
        record = TelemetryRecord(
            decision_id="d1",
            query="test",
            options=["a", "b"],
            expected_values=[0.5, 0.6],
            valences=[0.1, 0.2],
            go_scores=[0.6, 0.8],
            accumulated_evidence=[0.6, 0.8],
            chosen_idx=1,
            chosen_action="b",
            expected_outcome=0.8,
            expected=0.8,
            actual=1.0,
            rpe=0.2,
            memory_key="b",
            memory_value_after=0.02,
        )
        assert record.decision_id == "d1"
        assert record.outcome is None

    def test_json_roundtrip(self) -> None:
        record = TelemetryRecord(
            decision_id="d1",
            query="test",
            options=["a"],
            expected_values=[0.5],
            valences=[0.1],
            go_scores=[0.6],
            accumulated_evidence=[0.6],
            chosen_idx=0,
            chosen_action="a",
            expected_outcome=0.6,
            expected=0.6,
            actual=0.7,
            rpe=0.1,
            memory_key="a",
            memory_value_after=0.01,
        )
        json_str = record.model_dump_json()
        reloaded = TelemetryRecord.model_validate_json(json_str)
        assert reloaded.decision_id == record.decision_id
        assert reloaded.rpe == pytest.approx(0.1)

    def test_timestamp_default(self) -> None:
        record = TelemetryRecord(
            decision_id="d1",
            query="test",
            options=["a"],
            expected_values=[0.5],
            valences=[0.1],
            go_scores=[0.6],
            accumulated_evidence=[0.6],
            chosen_idx=0,
            chosen_action="a",
            expected_outcome=0.6,
            expected=0.6,
            actual=0.7,
            rpe=0.1,
            memory_key="a",
            memory_value_after=0.01,
        )
        assert record.timestamp is not None


class TestTelemetryRecorder:
    def test_record_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            record = TelemetryRecord(
                decision_id="d1",
                query="test",
                options=["a"],
                expected_values=[0.5],
                valences=[0.1],
                go_scores=[0.6],
                accumulated_evidence=[0.6],
                chosen_idx=0,
                chosen_action="a",
                expected_outcome=0.6,
                expected=0.6,
                actual=0.7,
                rpe=0.1,
                memory_key="a",
                memory_value_after=0.01,
            )
            written_path = recorder.record(record)
            assert written_path.exists()
            assert written_path.suffix == ".jsonl"

    def test_record_appends_multiple(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            record1 = TelemetryRecord(
                decision_id="d1",
                query="q1",
                options=["a"],
                expected_values=[0.5],
                valences=[0.1],
                go_scores=[0.6],
                accumulated_evidence=[0.6],
                chosen_idx=0,
                chosen_action="a",
                expected_outcome=0.6,
                expected=0.6,
                actual=0.7,
                rpe=0.1,
                memory_key="a",
                memory_value_after=0.01,
            )
            record2 = TelemetryRecord(
                decision_id="d2",
                query="q2",
                options=["b"],
                expected_values=[0.7],
                valences=[0.2],
                go_scores=[0.9],
                accumulated_evidence=[0.9],
                chosen_idx=0,
                chosen_action="b",
                expected_outcome=0.9,
                expected=0.9,
                actual=1.0,
                rpe=0.1,
                memory_key="b",
                memory_value_after=0.01,
            )
            recorder.record(record1)
            recorder.record(record2)
            records = recorder.read_day()
            assert len(records) == 2
            assert records[0].decision_id == "d1"
            assert records[1].decision_id == "d2"

    def test_read_day_returns_empty_for_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            records = recorder.read_day("1999-01-01")
            assert records == []

    def test_list_days_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            record = TelemetryRecord(
                decision_id="d1",
                query="test",
                options=["a"],
                expected_values=[0.5],
                valences=[0.1],
                go_scores=[0.6],
                accumulated_evidence=[0.6],
                chosen_idx=0,
                chosen_action="a",
                expected_outcome=0.6,
                expected=0.6,
                actual=0.7,
                rpe=0.1,
                memory_key="a",
                memory_value_after=0.01,
            )
            recorder.record(record)
            days = recorder.list_days()
            assert len(days) >= 1
            assert all(d.endswith(".jsonl") is False for d in days)

    def test_list_days_empty_without_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=Path(tmpdir) / "nonexistent")
            assert recorder.list_days() == []

    def test_directory_property(self) -> None:
        recorder = TelemetryRecorder(directory="/tmp/foo")
        assert recorder.directory == Path("/tmp/foo")


class TestBrainTelemetryIntegration:
    def test_decide_records_telemetry_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            brain = DigitalBrain(telemetry=recorder)
            result = brain.decide(query="integration test")
            records = recorder.read_day()
            assert len(records) == 1
            assert records[0].decision_id == result["decision_id"]
            assert records[0].query == "integration test"

    def test_decide_captures_all_stages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            brain = DigitalBrain(telemetry=recorder)
            brain.decide(query="test", options=["x", "y"])
            records = recorder.read_day()
            assert len(records) == 1
            r = records[0]
            assert len(r.options) == 2
            assert len(r.expected_values) == 2
            assert len(r.valences) == 2
            assert len(r.go_scores) == 2
            assert len(r.accumulated_evidence) == 2
            assert r.chosen_action in r.options
            assert r.memory_key in r.options
            assert r.outcome is None

    def test_decide_without_telemetry_does_not_raise(self) -> None:
        brain = DigitalBrain()
        result = brain.decide(query="test")
        assert "chosen_action" in result

    def test_record_outcome_updates_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            brain = DigitalBrain(telemetry=recorder)
            brain.decide(query="pre", options=["a", "b"])
            brain.record_outcome(
                decision_id="ext-1",
                expected=0.5,
                actual=0.9,
                metadata={"source": "manual"},
            )
            records = recorder.read_day()
            outcome_records = [r for r in records if r.outcome is not None]
            assert len(outcome_records) == 1
            assert outcome_records[0].outcome == {"source": "manual"}
            assert outcome_records[0].rpe == pytest.approx(0.4)

    def test_record_outcome_emits_rpe_event(self) -> None:
        brain = DigitalBrain()
        brain.record_outcome(decision_id="d1", expected=0.5, actual=1.0)
        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert len(rpes) == 1
        assert rpes[0].rpe == pytest.approx(0.5)


def _make_record(
    decision_id: str,
    query: str = "test",
    options: list[str] | None = None,
    rpe: float = 0.1,
) -> TelemetryRecord:
    opts = options or ["a", "b"]
    idx = 0
    return TelemetryRecord(
        decision_id=decision_id,
        query=query,
        options=opts,
        expected_values=[0.5, 0.5],
        valences=[0.1, 0.1],
        go_scores=[0.6, 0.6],
        accumulated_evidence=[0.6, 0.6],
        chosen_idx=idx,
        chosen_action=opts[idx],
        expected_outcome=0.6,
        expected=0.6,
        actual=0.6 + rpe,
        rpe=rpe,
        memory_key=opts[idx],
        memory_value_after=0.01,
    )


class TestTelemetryAnalyzer:
    def test_empty_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze()
            assert result["count"] == 0
            assert result["trend"] == "no data"
            assert result["top_events"] == []

    def test_basic_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            recorder.record(_make_record("d1", rpe=0.5))
            recorder.record(_make_record("d2", rpe=-0.3))
            recorder.record(_make_record("d3", rpe=0.1))
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze()
            assert result["count"] == 3
            assert result["mean_rpe"] == pytest.approx(0.1)
            assert result["abs_max_rpe"] == pytest.approx(0.5)
            assert result["threshold_suggestion"] is not None

    def test_trend_improving(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            for i, rpe_val in enumerate([-0.3, -0.2, 0.1, 0.4]):
                recorder.record(_make_record(f"d{i}", rpe=rpe_val))
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze()
            assert result["trend"] == "improving"

    def test_trend_declining(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            for i, rpe_val in enumerate([0.4, 0.2, -0.1, -0.3]):
                recorder.record(_make_record(f"d{i}", rpe=rpe_val))
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze()
            assert result["trend"] == "declining"

    def test_region_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            recorder.record(_make_record("d1", options=["foo", "bar"]))
            recorder.record(_make_record("d2", options=["baz", "qux"]))
            recorder.record(_make_record("d3", options=["foo", "baz"]))
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze(region="foo")
            assert result["count"] == 2

    def test_since_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            # Write one record today — it should be included regardless of since date
            recorder.record(_make_record("d1"))
            # since="2999-01-01" should filter out all records
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze(since="2999-01-01")
            assert result["count"] == 0

    def test_top_events_sorted_by_abs_rpe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = TelemetryRecorder(directory=tmpdir)
            recorder.record(_make_record("d1", rpe=0.1))
            recorder.record(_make_record("d2", rpe=0.9))
            recorder.record(_make_record("d3", rpe=-0.4))
            recorder.record(_make_record("d4", rpe=0.05))
            analyzer = TelemetryAnalyzer(recorder)
            result = analyzer.analyze()
            assert len(result["top_events"]) == 4
            # First event should be the one with |rpe|=0.9
            assert result["top_events"][0]["rpe"] == pytest.approx(0.9)
