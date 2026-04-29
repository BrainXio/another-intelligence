"""Memory-value index for context + option -> learned value mappings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

from another_intelligence.memory.preference_pair import PreferencePair


class MemoryValueIndex:
    """Associative store that maps a composite key to a learned scalar value.

    Keys are typically ``"context_hash::option_id"`` so that the same option
    in different contexts can have distinct learned values.

    Updates follow a simple delta rule::

        value[key] += learning_rate * RPE

    When |RPE| exceeds *export_threshold* a :class:`PreferencePair` is
    serialised to *training_dir* so it can be consumed by a trainer node.
    """

    def __init__(
        self,
        training_dir: str | None = None,
        learning_rate: float = 0.1,
        export_threshold: float = 0.3,
    ) -> None:
        self._values: dict[str, float] = {}
        self._learning_rate = learning_rate
        self._export_threshold = export_threshold
        if training_dir is None:
            training_dir = os.path.expanduser("~/.brainxio/training_datasets")
        self._training_dir = Path(training_dir)

    def get(self, key: str) -> float:
        """Return the learned value for *key*, defaulting to ``0.0``."""
        return self._values.get(key, 0.0)

    def __setitem__(self, key: str, value: float) -> None:
        """Set a value directly (for state hydration)."""
        self._values[key] = value

    def update(self, key: str, rpe: float) -> float:
        """Apply the delta rule and return the new value.

        Args:
            key: Composite lookup key.
            rpe: Reward prediction error (actual - expected).
        """
        current = self._values.get(key, 0.0)
        new_value = current + self._learning_rate * rpe
        self._values[key] = new_value
        return new_value

    def export_preference_pair(
        self,
        context: str,
        chosen: str,
        rejected: list[str],
        rpe: float,
    ) -> Path | None:
        """Serialise a preference pair when |RPE| is significant.

        Returns:
            Path to the written JSON file, or ``None`` if the RPE was
            below the export threshold.
        """
        if abs(rpe) <= self._export_threshold:
            return None
        pair = PreferencePair(
            context=context,
            chosen=chosen,
            rejected=rejected,
            rpe=rpe,
        )
        return pair.write(self._training_dir)

    def keys(self) -> set[str]:
        """Return the set of all stored keys."""
        return set(self._values.keys())

    def snapshot(self) -> dict[str, float]:
        """Return a shallow copy of the entire value table."""
        return self._values.copy()

    def reset(self) -> Self:
        """Clear all values and return *self* for chaining."""
        self._values.clear()
        return self
