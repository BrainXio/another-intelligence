"""Activity state machine for the DigitalBrain PPAC loop."""

from enum import Enum


class ActivityPhase(Enum):
    """Phases of the PPAC decision loop."""

    IDLE = "idle"
    PROPOSING = "proposing"
    ACCUMULATING = "accumulating"
    SELECTING = "selecting"
    LEARNING = "learning"


class StateMachine:
    """Tracks the current activity phase and transition history."""

    _VALID_TRANSITIONS: dict[ActivityPhase, set[ActivityPhase]] = {
        ActivityPhase.IDLE: {ActivityPhase.PROPOSING},
        ActivityPhase.PROPOSING: {ActivityPhase.ACCUMULATING},
        ActivityPhase.ACCUMULATING: {ActivityPhase.SELECTING},
        ActivityPhase.SELECTING: {ActivityPhase.LEARNING, ActivityPhase.IDLE},
        ActivityPhase.LEARNING: {ActivityPhase.IDLE},
    }

    def __init__(self) -> None:
        self._current: ActivityPhase = ActivityPhase.IDLE
        self._history: list[ActivityPhase] = [ActivityPhase.IDLE]

    @property
    def current(self) -> ActivityPhase:
        return self._current

    @property
    def history(self) -> list[ActivityPhase]:
        return self._history.copy()

    def can_transition_to(self, target: ActivityPhase) -> bool:
        if target == self._current:
            return True
        return target in self._VALID_TRANSITIONS.get(self._current, set())

    def transition_to(self, target: ActivityPhase) -> None:
        if target == self._current:
            return
        if not self.can_transition_to(target):
            raise ValueError(
                f"Invalid transition from {self._current.value} to {target.value}"
            )
        self._current = target
        self._history.append(target)

    def reset(self) -> None:
        self._current = ActivityPhase.IDLE
        self._history = [ActivityPhase.IDLE]

    def is_active(self) -> bool:
        return self._current != ActivityPhase.IDLE

    def __str__(self) -> str:
        return f"StateMachine({self._current.value})"

    def __repr__(self) -> str:
        return f"StateMachine(current=ActivityPhase.{self._current.name})"
