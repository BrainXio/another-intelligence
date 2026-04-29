"""Reward Prediction Error (RPE) computation and tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

__all__ = ["RPEEntry", "RPEEngine"]


@dataclass(frozen=True)
class RPEEntry:
    """Immutable record of a single RPE computation."""

    expected: float
    actual: float
    rpe: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class RPEEngine:
    """Computes reward prediction error and maintains a history of updates.

    RPE follows the Schultz dopamine model::

        RPE = actual_reward - expected_reward

    Positive RPE → chosen action was better than expected (strengthen Go).
    Negative RPE → chosen action was worse than expected (strengthen NoGo).
    """

    def __init__(self, learning_threshold: float = 0.3) -> None:
        self._learning_threshold = learning_threshold
        self._history: list[RPEEntry] = []

    def compute(self, expected: float, actual: float) -> float:
        """Compute RPE and append to history.

        Args:
            expected: Anticipated reward or value.
            actual: Observed reward or value.

        Returns:
            The computed RPE value.
        """
        rpe = actual - expected
        entry = RPEEntry(expected=expected, actual=actual, rpe=rpe)
        self._history.append(entry)
        return rpe

    def is_significant(self, rpe: float) -> bool:
        """Return whether the magnitude of *rpe* warrants learning updates."""
        return abs(rpe) > self._learning_threshold

    @property
    def history(self) -> list[RPEEntry]:
        """Return a shallow copy of the RPE history."""
        return self._history.copy()

    def summary(self) -> dict[str, float]:
        """Return aggregate statistics over the history."""
        if not self._history:
            return {"count": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
        values = [e.rpe for e in self._history]
        return {
            "count": float(len(values)),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def reset(self) -> Self:
        """Clear history and return *self* for chaining."""
        self._history.clear()
        return self
