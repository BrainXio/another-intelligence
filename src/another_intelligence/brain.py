"""DigitalBrain orchestrator with strict serial PPAC loop."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from another_intelligence.context import ContextWindow
from another_intelligence.events import (
    BrainEvent,
    BrainRegionActivated,
    RPEUpdated,
)
from another_intelligence.executor import Executor
from another_intelligence.memory.value_index import MemoryValueIndex
from another_intelligence.reflex import Reflex
from another_intelligence.rpe import RPEEngine
from another_intelligence.rpe.telemetry import TelemetryRecord, TelemetryRecorder
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

    def __init__(
        self,
        max_tokens: int = 8192,
        rpe_engine: RPEEngine | None = None,
        memory_index: MemoryValueIndex | None = None,
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self._state = StateMachine()
        self._events: list[BrainEvent] = []
        self._context = ContextWindow(max_tokens=max_tokens)
        self._hooks: dict[str, list[Callable[[BrainEvent], None]]] = {}
        self._rpe = rpe_engine if rpe_engine is not None else RPEEngine()
        self._memory = memory_index if memory_index is not None else MemoryValueIndex()
        self._decisions: dict[str, dict[str, Any]] = {}
        self._strategist = Strategist()
        self._executor = Executor()
        self._reflex = Reflex(noise_scale=0.0)
        self._telemetry = telemetry

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
        return self._memory.snapshot()

    @property
    def rpe_engine(self) -> RPEEngine:
        return self._rpe

    @property
    def memory_index(self) -> MemoryValueIndex:
        return self._memory

    @property
    def telemetry(self) -> TelemetryRecorder | None:
        return self._telemetry

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
        proposal = self._strategist.propose(query, options, self.memory)
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
            proposal.options, proposal.expected_values, self.memory
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
        actual = self._reflex.simulate_outcome(chosen_action, self.memory)
        rpe = self._rpe.compute(expected=expected, actual=actual)
        self._emit(
            RPEUpdated(
                region="reflex",
                expected=expected,
                actual=actual,
                rpe=rpe,
            )
        )

        # 5. Learning
        memory_key = chosen_action
        memory_value_after = self._memory.update(memory_key, rpe)
        self._maybe_export_preference_pair(
            decision_id=decision_id,
            query=query,
            chosen=chosen_action,
            rejected=[opt for i, opt in enumerate(proposal.options) if i != selection.chosen_idx],
            rpe=rpe,
        )
        self._decisions[decision_id] = {
            "query": query,
            "chosen": chosen_action,
            "options": proposal.options,
            "expected": expected,
            "actual": actual,
            "rpe": rpe,
        }
        self._emit(
            BrainRegionActivated(
                region="learning",
                metadata={
                    "decision_id": decision_id,
                    "rpe": rpe,
                    "memory_key": memory_key,
                },
            )
        )

        # Persist telemetry when recorder is configured
        if self._telemetry is not None:
            self._telemetry.record(
                TelemetryRecord(
                    decision_id=decision_id,
                    query=query,
                    options=proposal.options,
                    expected_values=proposal.expected_values,
                    valences=evaluation.valences,
                    go_scores=evaluation.go_scores,
                    accumulated_evidence=selection.accumulated_evidence,
                    chosen_idx=selection.chosen_idx,
                    chosen_action=chosen_action,
                    expected_outcome=expected,
                    expected=expected,
                    actual=actual,
                    rpe=rpe,
                    memory_key=memory_key,
                    memory_value_after=memory_value_after,
                )
            )

        self._state.transition_to(ActivityPhase.IDLE)
        self._context.add_message("assistant", chosen_action)

        return {
            "chosen_action": chosen_action,
            "options": proposal.options,
            "decision_id": decision_id,
        }

    def record_outcome(
        self,
        decision_id: str,
        expected: float,
        actual: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an external outcome and compute RPE.

        If the decision context is known and the RPE exceeds the export
        threshold, a preference pair is serialised to the training dataset
        directory.
        """
        if not decision_id:
            raise ValueError("decision_id is required")
        rpe = self._rpe.compute(expected=expected, actual=actual)
        self._emit(
            RPEUpdated(
                expected=expected,
                actual=actual,
                rpe=rpe,
                region="reflex",
            )
        )
        self._memory.update(decision_id, rpe)
        ctx = self._decisions.get(decision_id)
        if ctx is not None:
            self._maybe_export_preference_pair(
                decision_id=decision_id,
                query=ctx["query"],
                chosen=ctx["chosen"],
                rejected=[opt for opt in ctx["options"] if opt != ctx["chosen"]],
                rpe=rpe,
            )
        if self._telemetry is not None:
            self._telemetry.record(
                TelemetryRecord(
                    decision_id=decision_id,
                    query=ctx["query"] if ctx else "",
                    options=ctx["options"] if ctx else [],
                    expected_values=[],
                    valences=[],
                    go_scores=[],
                    accumulated_evidence=[],
                    chosen_idx=0,
                    chosen_action=ctx["chosen"] if ctx else "",
                    expected_outcome=expected,
                    expected=expected,
                    actual=actual,
                    rpe=rpe,
                    outcome=metadata,
                    memory_key=decision_id,
                    memory_value_after=self._memory.get(decision_id),
                )
            )

    def _maybe_export_preference_pair(
        self,
        decision_id: str,
        query: str,
        chosen: str,
        rejected: list[str],
        rpe: float,
    ) -> Path | None:
        """Export a preference pair when RPE is significant."""
        return self._memory.export_preference_pair(
            context=f"{decision_id}::{query}",
            chosen=chosen,
            rejected=rejected,
            rpe=rpe,
        )
