"""Reflex (Parietal LIP + Dopamine) — evidence accumulation and RPE computation."""

from __future__ import annotations

import random
from dataclasses import dataclass

__all__ = ["Reflex", "Selection"]


@dataclass
class Selection:
    """Structured output from the Reflex region."""

    chosen_idx: int
    expected_outcome: float
    accumulated_evidence: list[float]

    def __post_init__(self):
        if not (0 <= self.chosen_idx < len(self.accumulated_evidence)):
            raise ValueError("chosen_idx is out of range")


class Reflex:
    """Parietal + Dopamine reflex region.

    Accumulates evidence toward a decision threshold (noisy Shadlen-style
    ramping) and computes Reward Prediction Error (RPE).
    """

    def __init__(self, noise_scale: float = 0.0, seed: int | None = None) -> None:
        self._noise_scale = noise_scale
        self._rng = random.Random(seed)

    def accumulate(self, options: list[str], go_scores: list[float]) -> Selection:
        """Noisy evidence accumulation toward a decision threshold.

        Args:
            options: Candidate action strings (for alignment checks).
            go_scores: Go scores for each option (from Executor).

        Returns:
            A ``Selection`` containing the chosen index, expected outcome,
            and the accumulated evidence vector.
        """
        if len(options) != len(go_scores):
            raise ValueError("options and go_scores must have the same length")
        if not go_scores:
            raise ValueError("go_scores must not be empty")

        accumulated = [score + self._rng.gauss(0, self._noise_scale) for score in go_scores]
        chosen_idx = accumulated.index(max(accumulated))

        return Selection(
            chosen_idx=chosen_idx,
            expected_outcome=accumulated[chosen_idx],
            accumulated_evidence=accumulated,
        )

    @staticmethod
    def compute_rpe(expected: float, actual: float) -> float:
        """Compute Reward Prediction Error.

        Returns ``actual - expected`` following the Schultz dopamine model.
        """
        return actual - expected

    def simulate_outcome(
        self,
        action: str,
        memory: dict[str, float] | None = None,
        base_value: float = 0.5,
    ) -> float:
        """Simulate the actual outcome of an action.

        This is a deterministic placeholder that will be replaced by real
        external feedback in production usage.
        """
        memory = memory or {}
        learned = memory.get(action, 0.0)
        return base_value + learned
