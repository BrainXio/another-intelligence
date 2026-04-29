"""Tests for the Reflex (Parietal LIP + Dopamine) brain region."""

import pytest

from another_intelligence.reflex import Reflex, Selection


class TestSelection:
    """Selection dataclass validation."""

    def test_basic_construction(self):
        s = Selection(chosen_idx=0, expected_outcome=0.5, accumulated_evidence=[0.5, 0.6])
        assert s.chosen_idx == 0
        assert s.expected_outcome == 0.5
        assert s.accumulated_evidence == [0.5, 0.6]

    def test_chosen_idx_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            Selection(chosen_idx=5, expected_outcome=0.5, accumulated_evidence=[0.5, 0.6])


class TestReflexInit:
    """Construction and configuration."""

    def test_default_noise_scale(self):
        r = Reflex()
        assert r._noise_scale == 0.0

    def test_custom_noise_scale(self):
        r = Reflex(noise_scale=0.05)
        assert r._noise_scale == 0.05

    def test_custom_seed(self):
        r1 = Reflex(noise_scale=0.1, seed=42)
        r2 = Reflex(noise_scale=0.1, seed=42)
        s1 = r1.accumulate(["a", "b"], [0.5, 0.6])
        s2 = r2.accumulate(["a", "b"], [0.5, 0.6])
        assert s1.accumulated_evidence == s2.accumulated_evidence


class TestReflexAccumulate:
    """Evidence accumulation and selection."""

    def test_returns_selection(self):
        r = Reflex()
        result = r.accumulate(["a", "b"], [0.5, 0.6])
        assert isinstance(result, Selection)

    def test_mismatched_lengths_raise(self):
        r = Reflex()
        with pytest.raises(ValueError, match="same length"):
            r.accumulate(["a", "b"], [0.5])

    def test_empty_scores_raise(self):
        r = Reflex()
        with pytest.raises(ValueError, match="not be empty"):
            r.accumulate([], [])

    def test_deterministic_when_noise_zero(self):
        r = Reflex(noise_scale=0.0)
        result = r.accumulate(["a", "b", "c"], [0.3, 0.8, 0.5])
        assert result.chosen_idx == 1
        assert result.expected_outcome == 0.8
        assert result.accumulated_evidence == [0.3, 0.8, 0.5]

    def test_first_wins_on_tie(self):
        r = Reflex(noise_scale=0.0)
        result = r.accumulate(["a", "b"], [0.5, 0.5])
        assert result.chosen_idx == 0

    def test_noise_changes_evidence(self):
        r = Reflex(noise_scale=1.0, seed=123)
        result = r.accumulate(["a", "b"], [0.5, 0.5])
        assert result.accumulated_evidence != [0.5, 0.5]


class TestReflexComputeRPE:
    """RPE computation."""

    def test_positive_rpe(self):
        assert Reflex.compute_rpe(expected=0.5, actual=0.8) == pytest.approx(0.3)

    def test_negative_rpe(self):
        assert Reflex.compute_rpe(expected=0.5, actual=0.2) == pytest.approx(-0.3)

    def test_zero_rpe(self):
        assert Reflex.compute_rpe(expected=0.5, actual=0.5) == 0.0


class TestReflexSimulateOutcome:
    """Outcome simulation."""

    def test_no_memory(self):
        r = Reflex()
        assert r.simulate_outcome("foo") == 0.5

    def test_with_memory(self):
        r = Reflex()
        assert r.simulate_outcome("foo", memory={"foo": 0.2}) == 0.7

    def test_custom_base_value(self):
        r = Reflex()
        assert r.simulate_outcome("foo", base_value=1.0) == 1.0
