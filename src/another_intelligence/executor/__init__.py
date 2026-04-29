"""Executor (Limbic + Basal Ganglia) — emotional valence and Go/NoGo selection."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Evaluation", "Executor"]


@dataclass
class Evaluation:
    """Structured output from the Executor region."""

    valences: list[float]
    go_scores: list[float]
    chosen_idx: int
    chosen_action: str

    def __post_init__(self):
        if len(self.valences) != len(self.go_scores):
            raise ValueError("valences and go_scores must have the same length")
        if not (0 <= self.chosen_idx < len(self.go_scores)):
            raise ValueError("chosen_idx is out of range")


class Executor:
    """Limbic + Basal Ganglia executor.

    Tags each candidate option with an emotional valence, computes Go/NoGo
    scores, and selects the action with the highest Go signal.
    """

    def __init__(self, valence_scale: float = 0.1) -> None:
        self._valence_scale = valence_scale

    def evaluate(
        self,
        options: list[str],
        expected_values: list[float],
        memory: dict[str, float] | None = None,
    ) -> Evaluation:
        """Tag options with valence and perform Go/NoGo selection.

        Args:
            options: Candidate action strings.
            expected_values: Expected value for each option (from Strategist).
            memory: Learned value index mapping option keys to scalar values.

        Returns:
            An ``Evaluation`` containing valences, Go scores, and the chosen index.
        """
        if len(options) != len(expected_values):
            raise ValueError("options and expected_values must have the same length")
        if not options:
            raise ValueError("options must not be empty")

        memory = memory or {}

        valences = [self._emotional_valence(opt, memory) for opt in options]
        go_scores = [ev + v for ev, v in zip(expected_values, valences, strict=True)]
        chosen_idx = self._select_action(go_scores)

        return Evaluation(
            valences=valences,
            go_scores=go_scores,
            chosen_idx=chosen_idx,
            chosen_action=options[chosen_idx],
        )

    def _emotional_valence(self, option: str, memory: dict[str, float]) -> float:
        """Assign emotional valence based on learned memory."""
        learned = memory.get(option, 0.0)
        return learned * self._valence_scale

    def _select_action(self, go_scores: list[float]) -> int:
        """Select the action with the highest Go score."""
        if not go_scores:
            raise ValueError("go_scores must not be empty")
        return go_scores.index(max(go_scores))
