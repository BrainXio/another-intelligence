"""Tests for the activity state machine."""

import pytest

from another_intelligence.state import ActivityPhase, StateMachine


class TestActivityPhase:
    """Enum values and string representation."""

    def test_phase_values(self):
        assert ActivityPhase.IDLE.value == "idle"
        assert ActivityPhase.PROPOSING.value == "proposing"
        assert ActivityPhase.ACCUMULATING.value == "accumulating"
        assert ActivityPhase.SELECTING.value == "selecting"
        assert ActivityPhase.LEARNING.value == "learning"

    def test_phase_order(self):
        phases = list(ActivityPhase)
        assert phases == [
            ActivityPhase.IDLE,
            ActivityPhase.PROPOSING,
            ActivityPhase.ACCUMULATING,
            ActivityPhase.SELECTING,
            ActivityPhase.LEARNING,
        ]


class TestStateMachine:
    """StateMachine lifecycle and transitions."""

    def test_initial_state_is_idle(self):
        sm = StateMachine()
        assert sm.current == ActivityPhase.IDLE

    def test_transition_to_proposing(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        assert sm.current == ActivityPhase.PROPOSING

    def test_transition_records_history(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        sm.transition_to(ActivityPhase.ACCUMULATING)
        assert sm.history == [ActivityPhase.IDLE, ActivityPhase.PROPOSING, ActivityPhase.ACCUMULATING]

    def test_transition_to_same_phase_is_noop(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        sm.transition_to(ActivityPhase.PROPOSING)
        assert sm.history == [ActivityPhase.IDLE, ActivityPhase.PROPOSING]

    def test_invalid_transition_raises(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition_to(ActivityPhase.LEARNING)

    def test_can_transition_positive(self):
        sm = StateMachine()
        assert sm.can_transition_to(ActivityPhase.PROPOSING) is True

    def test_can_transition_negative(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        assert sm.can_transition_to(ActivityPhase.LEARNING) is False

    def test_reset_returns_to_idle(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        sm.transition_to(ActivityPhase.ACCUMULATING)
        sm.reset()
        assert sm.current == ActivityPhase.IDLE
        assert sm.history == [ActivityPhase.IDLE]

    def test_is_active_idle(self):
        sm = StateMachine()
        assert sm.is_active() is False

    def test_is_active_non_idle(self):
        sm = StateMachine()
        sm.transition_to(ActivityPhase.PROPOSING)
        assert sm.is_active() is True

    def test_str_and_repr(self):
        sm = StateMachine()
        assert str(sm) == "StateMachine(idle)"
        assert repr(sm) == "StateMachine(current=ActivityPhase.IDLE)"
