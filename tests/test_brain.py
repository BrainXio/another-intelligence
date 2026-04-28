"""Tests for the DigitalBrain orchestrator and strict serial PPAC loop."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from another_intelligence.brain import DigitalBrain
from another_intelligence.events import BrainRegionActivated, RPEUpdated
from another_intelligence.state import ActivityPhase


class TestDigitalBrainInit:
    """Construction and default state."""

    def test_default_state(self):
        brain = DigitalBrain()
        assert brain.state.current == ActivityPhase.IDLE

    def test_event_log_empty(self):
        brain = DigitalBrain()
        assert brain.events == []

    def test_context_window_initialized(self):
        brain = DigitalBrain()
        assert brain.context.total_tokens == 0
        assert brain.context.max_tokens > 0


class TestDecideStages:
    """Strict serial PPAC loop: Strategist → Executor → Reflex → Outcome → Learning."""

    def test_decide_returns_decision(self):
        brain = DigitalBrain()
        result = brain.decide(query="What should I do?")
        assert isinstance(result, dict)
        assert "chosen_action" in result
        assert "options" in result

    def test_decide_emits_strategist_event(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        assert "strategist" in regions

    def test_decide_emits_executor_event(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        assert "executor" in regions

    def test_decide_emits_reflex_event(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        assert "reflex" in regions

    def test_decide_emits_rpe_event(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert len(rpes) >= 1

    def test_stages_execute_in_order(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        strategist_idx = regions.index("strategist")
        executor_idx = regions.index("executor")
        reflex_idx = regions.index("reflex")
        assert strategist_idx < executor_idx < reflex_idx

    def test_state_returns_to_idle(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        assert brain.state.current == ActivityPhase.IDLE

    def test_state_transitions_through_all_phases(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        assert ActivityPhase.PROPOSING in brain.state.history
        assert ActivityPhase.ACCUMULATING in brain.state.history
        assert ActivityPhase.SELECTING in brain.state.history
        assert ActivityPhase.LEARNING in brain.state.history

    def test_decide_updates_context(self):
        brain = DigitalBrain()
        before = brain.context.total_tokens
        brain.decide(query="test")
        assert brain.context.total_tokens > before

    def test_decide_with_options(self):
        brain = DigitalBrain()
        result = brain.decide(query="test", options=["a", "b", "c"])
        assert result["chosen_action"] in ["a", "b", "c"]
        assert len(result["options"]) == 3

    def test_decide_without_options_generates_defaults(self):
        brain = DigitalBrain()
        result = brain.decide(query="test")
        assert len(result["options"]) > 0
        assert result["chosen_action"] in result["options"]


class TestDecideHooks:
    """Hook registration and invocation."""

    def test_hook_called_on_region_activation(self):
        brain = DigitalBrain()
        mock_hook = MagicMock()
        brain.register_hook("BrainRegionActivated", mock_hook)
        brain.decide(query="test")
        assert mock_hook.called

    def test_hook_called_with_event(self):
        brain = DigitalBrain()
        calls: list[Any] = []

        def capture(event: Any) -> None:
            calls.append(event)

        brain.register_hook("BrainRegionActivated", capture)
        brain.decide(query="test")
        assert len(calls) > 0
        assert all(isinstance(c, BrainRegionActivated) for c in calls)

    def test_multiple_hooks_fire(self):
        brain = DigitalBrain()
        hook1 = MagicMock()
        hook2 = MagicMock()
        brain.register_hook("BrainRegionActivated", hook1)
        brain.register_hook("BrainRegionActivated", hook2)
        brain.decide(query="test")
        assert hook1.called
        assert hook2.called

    def test_unknown_event_type_ignored(self):
        brain = DigitalBrain()
        brain.register_hook("UnknownEvent", MagicMock())
        brain.decide(query="test")


class TestOutcomeRecording:
    """Outcome recording stage."""

    def test_record_outcome_computes_rpe(self):
        brain = DigitalBrain()
        brain.record_outcome(decision_id="d1", expected=0.5, actual=1.0)
        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert len(rpes) == 1
        assert rpes[0].rpe == 0.5

    def test_record_outcome_requires_decision_id(self):
        brain = DigitalBrain()
        with pytest.raises(ValueError, match="decision_id"):
            brain.record_outcome(decision_id="", expected=0.5, actual=1.0)


class TestLearning:
    """Learning stage updates memory."""

    def test_learning_updates_memory_value(self):
        brain = DigitalBrain()
        brain.decide(query="test")
        assert len(brain.memory) > 0

    def test_learning_triggered_by_large_rpe(self):
        brain = DigitalBrain()
        brain.record_outcome(decision_id="d1", expected=0.1, actual=0.9)
        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert any(abs(e.rpe) > 0.1 for e in rpes)


class TestConcurrencySafety:
    """Serial execution guards."""

    def test_decide_raises_if_already_active(self):
        brain = DigitalBrain()
        brain._state.transition_to(ActivityPhase.PROPOSING)  # simulate in-flight
        with pytest.raises(RuntimeError, match="already active"):
            brain.decide(query="test")
