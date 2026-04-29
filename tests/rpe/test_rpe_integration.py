"""Integration tests for RPE learning within DigitalBrain."""

from pathlib import Path

import pytest

from another_intelligence.brain import DigitalBrain
from another_intelligence.memory.value_index import MemoryValueIndex
from another_intelligence.rpe import RPEEngine


class TestBrainRPEInjection:
    def test_brain_uses_custom_rpe_engine(self):
        engine = RPEEngine(learning_threshold=0.5)
        brain = DigitalBrain(rpe_engine=engine)
        brain.decide(query="test")
        assert len(engine.history) == 1
        assert brain.rpe_engine is engine

    def test_brain_uses_custom_memory_index(self):
        idx = MemoryValueIndex(learning_rate=0.2)
        brain = DigitalBrain(memory_index=idx)
        brain.decide(query="test")
        assert len(idx.keys()) > 0
        assert brain.memory_index is idx

    def test_brain_memory_property_matches_index(self):
        idx = MemoryValueIndex()
        brain = DigitalBrain(memory_index=idx)
        brain.decide(query="test")
        assert brain.memory == idx.snapshot()


class TestBrainPreferenceExport:
    def test_export_when_rpe_exceeds_threshold(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.0)
        brain = DigitalBrain(memory_index=idx)
        brain._reflex.simulate_outcome = lambda action, memory: 1.0  # force non-zero RPE
        brain.decide(query="test")
        files = list(tmp_path.iterdir())
        assert len(files) >= 1

    def test_no_export_when_rpe_below_threshold(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=10.0)
        brain = DigitalBrain(memory_index=idx)
        brain.decide(query="test")
        files = list(tmp_path.iterdir())
        assert len(files) == 0


class TestBrainRecordOutcomeIntegration:
    def test_record_outcome_with_known_decision_exports(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.0)
        brain = DigitalBrain(memory_index=idx)
        result = brain.decide(query="test", options=["a", "b"])
        decision_id = result["decision_id"]
        brain.record_outcome(decision_id=decision_id, expected=0.5, actual=1.0)
        files = list(tmp_path.iterdir())
        assert len(files) >= 1

    def test_record_outcome_with_unknown_decision_no_export(self, tmp_path: Path):
        idx = MemoryValueIndex(training_dir=str(tmp_path), export_threshold=0.0)
        brain = DigitalBrain(memory_index=idx)
        brain.record_outcome(decision_id="unknown", expected=0.5, actual=1.0)
        files = list(tmp_path.iterdir())
        assert len(files) == 0

    def test_record_outcome_computes_rpe_via_engine(self):
        engine = RPEEngine()
        brain = DigitalBrain(rpe_engine=engine)
        brain.record_outcome(decision_id="d1", expected=0.5, actual=1.0)
        assert len(engine.history) == 1
        assert engine.history[0].rpe == pytest.approx(0.5)

    def test_record_outcome_updates_memory(self):
        idx = MemoryValueIndex()
        brain = DigitalBrain(memory_index=idx)
        brain.record_outcome(decision_id="d1", expected=0.5, actual=1.0)
        assert idx.get("d1") == pytest.approx(0.05)
