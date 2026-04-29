"""Tests for the Executor (Limbic + Basal Ganglia) brain region."""

import pytest

from another_intelligence.executor import Evaluation, Executor


class TestEvaluation:
    """Evaluation dataclass validation."""

    def test_basic_construction(self):
        e = Evaluation(
            valences=[0.1, 0.2],
            go_scores=[0.6, 0.7],
            chosen_idx=0,
            chosen_action="a",
        )
        assert e.valences == [0.1, 0.2]
        assert e.go_scores == [0.6, 0.7]
        assert e.chosen_idx == 0
        assert e.chosen_action == "a"

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError, match="same length"):
            Evaluation(
                valences=[0.1],
                go_scores=[0.6, 0.7],
                chosen_idx=0,
                chosen_action="a",
            )

    def test_chosen_idx_out_of_range(self):
        with pytest.raises(ValueError, match="out of range"):
            Evaluation(
                valences=[0.1, 0.2],
                go_scores=[0.6, 0.7],
                chosen_idx=5,
                chosen_action="a",
            )


class TestExecutorInit:
    """Construction and configuration."""

    def test_default_valence_scale(self):
        e = Executor()
        assert e._valence_scale == 0.1

    def test_custom_valence_scale(self):
        e = Executor(valence_scale=0.2)
        assert e._valence_scale == 0.2


class TestExecutorEvaluate:
    """Valence tagging and Go/NoGo selection."""

    def test_returns_evaluation(self):
        e = Executor()
        result = e.evaluate(["a", "b"], [0.5, 0.6])
        assert isinstance(result, Evaluation)

    def test_mismatched_options_and_values(self):
        e = Executor()
        with pytest.raises(ValueError, match="same length"):
            e.evaluate(["a", "b"], [0.5])

    def test_valences_are_zero_without_memory(self):
        e = Executor()
        result = e.evaluate(["a", "b"], [0.5, 0.6])
        assert result.valences == [0.0, 0.0]

    def test_valences_use_memory(self):
        e = Executor(valence_scale=0.1)
        result = e.evaluate(["a", "b"], [0.5, 0.6], memory={"a": 1.0})
        assert result.valences[0] == 0.1
        assert result.valences[1] == 0.0

    def test_go_scores_sum_expected_and_valence(self):
        e = Executor(valence_scale=0.1)
        result = e.evaluate(["a", "b"], [0.5, 0.6], memory={"a": 1.0})
        assert result.go_scores[0] == 0.5 + 0.1
        assert result.go_scores[1] == 0.6

    def test_selects_highest_go_score(self):
        e = Executor()
        result = e.evaluate(["a", "b"], [0.3, 0.8])
        assert result.chosen_idx == 1
        assert result.chosen_action == "b"

    def test_first_wins_on_tie(self):
        e = Executor()
        result = e.evaluate(["a", "b"], [0.5, 0.5])
        assert result.chosen_idx == 0
        assert result.chosen_action == "a"

    def test_empty_options_raises(self):
        e = Executor()
        with pytest.raises(ValueError, match="not be empty"):
            e.evaluate([], [])

    def test_empty_go_scores_in_select_raises(self):
        e = Executor()
        with pytest.raises(ValueError, match="not be empty"):
            e._select_action([])
