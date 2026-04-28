"""DigitalBrain orchestrator with strict serial PPAC loop."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from another_intelligence.context import ContextWindow
from another_intelligence.events import (
    BrainEvent,
    BrainRegionActivated,
    RPEUpdated,
)
from another_intelligence.executor import Executor
from another_intelligence.reflex import Reflex
from another_intelligence.state import ActivityPhase, StateMachine
from another_intelligence.strategist import Strategist


class DigitalBrain:
    """Orchestrator executing the 5-stage PPAC loop in strict serial order.

    Stages:
        1. Strategist — Propose options and compute expected value.
        2. Executor — Tag options with emotional valence and pre-select.
        3. Reflex — Accumulate evidence and compute RPE.
        4. Outcome Recording — Capture actual vs expected feedback.
        5. Learning — Update memory-value index based on RPE.
    """

    def __init__(self, max_tokens: int = 8192) -> None:
        self._state = StateMachine()
        self._events: list[BrainEvent] = []
        self._context = ContextWindow(max_tokens=max_tokens)
        self._hooks: dict[str, list[Callable[[BrainEvent], None]]] = {}
        self._memory: dict[str, float] = {}
        self._rpe_threshold: float = 0.1
        self._strategist = Strategist()
        self._executor = Executor()
        self._reflex = Reflex(noise_scale=0.0)

    @property
    def state(self) -> StateMachine:
        return self._state

    @property
    def events(self) -> list[BrainEvent]:
        return self._events.copy()

    @property
    def context(self) -> ContextWindow:
        return self._context

    @property
    def memory(self) -> dict[str, float]:
        return self._memory.copy()

    def register_hook(self, event_type: str, callback: Callable[[BrainEvent], None]) -> None:
        self._hooks.setdefault(event_type, []).append(callback)

    def _emit(self, event: BrainEvent) -> None:
        self._events.append(event)
        for callback in self._hooks.get(type(event).__name__, []):
            callback(event)

    def decide(self, query: str, options: list[str] | None = None) -> dict[str, Any]:
        """Execute the strict serial PPAC loop.

        Returns a dict with ``chosen_action`` and ``options``.
        """
        if self._state.is_active():
            raise RuntimeError("Brain is already active in a decision loop")

        decision_id = str(uuid.uuid4())
        self._context.add_message("user", query)

        # 1. Strategist
        self._state.transition_to(ActivityPhase.PROPOSING)
        proposal = self._strategist.propose(query, options, self._memory)
        self._emit(
            BrainRegionActivated(
                region="strategist",
                metadata={
                    "decision_id": decision_id,
                    "option_count": len(proposal.options),
                    "expected_values": proposal.expected_values,
                },
            )
        )

        # 2. Executor
        self._state.transition_to(ActivityPhase.ACCUMULATING)
        evaluation = self._executor.evaluate(
            proposal.options, proposal.expected_values, self._memory
        )
        self._emit(
            BrainRegionActivated(
                region="executor",
                metadata={
                    "decision_id": decision_id,
                    "valences": evaluation.valences,
                    "go_scores": evaluation.go_scores,
                },
            )
        )

        # 3. Reflex
        self._state.transition_to(ActivityPhase.SELECTING)
        selection = self._reflex.accumulate(proposal.options, evaluation.go_scores)
        chosen_action = proposal.options[selection.chosen_idx]
        expected = selection.expected_outcome
        self._emit(
            BrainRegionActivated(
                region="reflex",
                metadata={
                    "decision_id": decision_id,
                    "chosen_action": chosen_action,
                    "expected_outcome": expected,
                },
            )
        )

        # 4. Outcome Recording (simulated immediate outcome)
        self._state.transition_to(ActivityPhase.LEARNING)
        actual = self._reflex.simulate_outcome(chosen_action, self._memory)
        rpe = self._reflex.compute_rpe(expected, actual)
        self._emit(
            RPEUpdated(
                region="reflex",
                expected=expected,
                actual=actual,
                rpe=rpe,
            )
        )

        # 5. Learning
        self._update_memory(chosen_action, rpe)
        self._emit(
            BrainRegionActivated(
                region="learning",
                metadata={
                    "decision_id": decision_id,
                    "rpe": rpe,
                    "memory_key": chosen_action,
                },
            )
        )

        self._state.transition_to(ActivityPhase.IDLE)
        self._context.add_message("assistant", chosen_action)

        return {
            "chosen_action": chosen_action,
            "options": proposal.options,
            "decision_id": decision_id,
        }

    def record_outcome(self, decision_id: str, expected: float, actual: float) -> None:
        """Record an external outcome and compute RPE."""
        if not decision_id:
            raise ValueError("decision_id is required")
        rpe = self._reflex.compute_rpe(expected, actual)
        self._emit(
            RPEUpdated(
                expected=expected,
                actual=actual,
                rpe=rpe,
                region="reflex",
            )
        )
        if abs(rpe) > self._rpe_threshold:
            self._update_memory(decision_id, rpe)

    def _update_memory(self, key: str, rpe: float) -> None:
        """Update the memory-value index with the new RPE."""
        current = self._memory.get(key, 0.0)
        self._memory[key] = current + 0.1 * rpe
