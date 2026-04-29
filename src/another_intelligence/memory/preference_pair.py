"""Preference pair export for RPE-driven learning datasets."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PreferencePair:
    """A single chosen-vs-rejected preference pair for dataset generation.

    When |RPE| exceeds the learning threshold, the chosen action and the
    set of rejected alternatives are serialised to the training dataset
    directory so they can be used for downstream fine-tuning (e.g. QLoRA).
    """

    context: str
    chosen: str
    rejected: list[str]
    rpe: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serialisable dictionary."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreferencePair:
        """Reconstruct a *PreferencePair* from a dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(
            context=data["context"],
            chosen=data["chosen"],
            rejected=data["rejected"],
            rpe=data["rpe"],
            timestamp=timestamp,
        )

    def write(self, directory: Path) -> Path:
        """Serialise to a JSON file inside *directory* and return the path."""
        directory.mkdir(parents=True, exist_ok=True)
        ts = self.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        safe_ctx = "".join(c if c.isalnum() else "_" for c in self.context)[:30]
        filename = f"{ts}_{safe_ctx}.json"
        path = directory / filename
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
