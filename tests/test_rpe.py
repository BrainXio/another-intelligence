"""Tests for the RPEEngine."""

import pytest

from another_intelligence.rpe import RPEEngine


class TestRPEEngineInit:
    def test_default_threshold(self):
        engine = RPEEngine()
        assert engine.is_significant(0.31) is True
        assert engine.is_significant(0.3) is False

    def test_custom_threshold(self):
        engine = RPEEngine(learning_threshold=0.5)
        assert engine.is_significant(0.51) is True
        assert engine.is_significant(0.5) is False


class TestRPEEngineCompute:
    def test_positive_rpe(self):
        engine = RPEEngine()
        rpe = engine.compute(expected=0.5, actual=1.0)
        assert rpe == pytest.approx(0.5)

    def test_negative_rpe(self):
        engine = RPEEngine()
        rpe = engine.compute(expected=1.0, actual=0.5)
        assert rpe == pytest.approx(-0.5)

    def test_zero_rpe(self):
        engine = RPEEngine()
        rpe = engine.compute(expected=0.7, actual=0.7)
        assert rpe == pytest.approx(0.0)

    def test_history_recorded(self):
        engine = RPEEngine()
        engine.compute(expected=0.5, actual=1.0)
        engine.compute(expected=1.0, actual=0.5)
        assert len(engine.history) == 2
        assert engine.history[0].rpe == pytest.approx(0.5)
        assert engine.history[1].rpe == pytest.approx(-0.5)

    def test_history_returns_copy(self):
        engine = RPEEngine()
        engine.compute(expected=0.5, actual=1.0)
        h1 = engine.history
        h1.clear()
        assert len(engine.history) == 1


class TestRPEEngineSummary:
    def test_empty_summary(self):
        engine = RPEEngine()
        summary = engine.summary()
        assert summary == {"count": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

    def test_summary_statistics(self):
        engine = RPEEngine()
        engine.compute(expected=0.0, actual=1.0)
        engine.compute(expected=0.0, actual=-1.0)
        summary = engine.summary()
        assert summary["count"] == 2.0
        assert summary["mean"] == pytest.approx(0.0)
        assert summary["min"] == pytest.approx(-1.0)
        assert summary["max"] == pytest.approx(1.0)


class TestRPEEngineReset:
    def test_reset_clears_history(self):
        engine = RPEEngine()
        engine.compute(expected=0.5, actual=1.0)
        engine.reset()
        assert len(engine.history) == 0

    def test_reset_returns_self(self):
        engine = RPEEngine()
        result = engine.reset()
        assert result is engine


class TestRPEEngineSignificance:
    def test_exact_threshold_not_significant(self):
        engine = RPEEngine(learning_threshold=0.3)
        assert engine.is_significant(0.3) is False
        assert engine.is_significant(-0.3) is False

    def test_above_threshold_significant(self):
        engine = RPEEngine(learning_threshold=0.3)
        assert engine.is_significant(0.31) is True
        assert engine.is_significant(-0.31) is True
