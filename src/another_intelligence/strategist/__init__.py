"""Strategist (PFC / DLPFC-OFC) — proposes options and computes expected values."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Proposal", "Strategist"]


@dataclass
class Proposal:
    """Structured output from the Strategist region."""

    options: list[str]
    expected_values: list[float]
    attributes: dict[str, list[float]] = field(default_factory=dict)
    query: str = ""

    def __post_init__(self) -> None:
        if len(self.options) != len(self.expected_values):
            raise ValueError("options and expected_values must have the same length")


class Strategist:
    """Prefrontal Cortex strategist.

    Proposes candidate actions and computes a multi-attribute expected
    value for each option, incorporating learned memory values.
    """

    _DEFAULT_OPTIONS: list[str] = ["proceed", "wait", "abort"]

    def __init__(self, base_value: float = 0.5) -> None:
        self._base_value = base_value

    def propose(
        self,
        query: str,
        options: list[str] | None = None,
        memory: dict[str, float] | None = None,
    ) -> Proposal:
        """Produce a structured proposal for the given query.

        Args:
            query: The user prompt or decision context.
            options: Explicit candidate actions. Defaults to ``["proceed", "wait", "abort"]``.
            memory: Learned value index mapping option keys to scalar values.

        Returns:
            A ``Proposal`` containing options and their expected values.
        """
        candidates = list(options) if options is not None else list(self._DEFAULT_OPTIONS)
        memory = memory or {}

        expected_values: list[float] = []
        for opt in candidates:
            learned = memory.get(opt, 0.0)
            expected_values.append(self._base_value + learned)

        return Proposal(
            options=candidates,
            expected_values=expected_values,
            query=query,
        )

    def expected_value(self, option: str, memory: dict[str, float] | None = None) -> float:
        """Compute the expected value of a single option."""
        memory = memory or {}
        learned = memory.get(option, 0.0)
        return self._base_value + learned

    def ingest_prototypes(
        self,
        shortlist: list[dict[str, str]],
        memory: dict[str, float] | None = None,
        top_n: int = 5,
    ) -> list[dict[str, object]]:
        """Rank prototype candidates by expected value.

        Args:
            shortlist: List of dicts with at least ``name`` and ``description`` keys.
            memory: Learned value index for option evaluation.
            top_n: Number of top-ranked candidates to return.

        Returns:
            A list of ranked dicts, each containing ``name``, ``expected_value``,
            ``rationale``, and ``dependencies``.
        """
        memory = memory or {}
        evaluated: list[dict[str, object]] = []

        for item in shortlist:
            name = item.get("name", "unknown")
            desc = item.get("description", "")
            deps = item.get("dependencies", [])
            ev = self.expected_value(name, memory)

            rationale = (
                "Strong prior learning"
                if memory.get(name, 0.0) > 0.2
                else "High baseline value"
                if self._base_value >= 0.5
                else f"Moderate expected value ({ev:.2f})"
            )

            evaluated.append(
                {
                    "name": name,
                    "description": desc,
                    "expected_value": round(ev, 4),
                    "rationale": rationale,
                    "dependencies": deps,
                }
            )

        evaluated.sort(key=lambda x: float(x["expected_value"]), reverse=True)
        return evaluated[:top_n]
