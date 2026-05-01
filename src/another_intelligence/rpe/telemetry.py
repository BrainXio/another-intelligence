"""Structured JSONL telemetry for every PPAC decision cycle."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TelemetryRecord(BaseModel):
    """Complete record of a single PPAC cycle.

    Captures inputs, all stage outputs, and the learning signal.  The
    ``outcome`` field starts as ``None`` and is back-filled when
    :meth:`DigitalBrain.record_outcome` closes the loop with real
    external feedback.
    """

    decision_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    query: str

    # Stage 1 — Strategist
    options: list[str]
    expected_values: list[float]

    # Stage 2 — Executor
    valences: list[float]
    go_scores: list[float]

    # Stage 3 — Reflex
    accumulated_evidence: list[float]
    chosen_idx: int
    chosen_action: str
    expected_outcome: float

    # Stage 4 — Outcome (None until external feedback arrives)
    expected: float
    actual: float
    rpe: float
    outcome: dict[str, Any] | None = None

    # Stage 5 — Learning
    memory_key: str
    memory_value_after: float


class TelemetryAnalyzer:
    """Read telemetry logs and produce aggregate metrics."""

    def __init__(self, recorder: TelemetryRecorder) -> None:
        self._recorder = recorder

    def analyze(
        self,
        since: str | None = None,
        region: str | None = None,
    ) -> dict[str, Any]:
        """Compute summary statistics over telemetry records.

        Args:
            since: Earliest date string (``YYYY-MM-DD``) to include.
            region: If set, only consider decisions involving this option string.

        Returns:
            A dict with ``count``, ``mean_rpe``, ``abs_max_rpe``,
            ``trend``, ``threshold_suggestion``, and ``top_events``.
        """
        days = self._recorder.list_days()
        if since is not None:
            days = [d for d in days if d >= since]

        records: list[TelemetryRecord] = []
        for day in days:
            records.extend(self._recorder.read_day(day))

        if region is not None:
            records = [r for r in records if region in r.options]

        if not records:
            return {
                "count": 0,
                "mean_rpe": 0.0,
                "abs_max_rpe": 0.0,
                "trend": "no data",
                "threshold_suggestion": None,
                "top_events": [],
            }

        rpe_values = [r.rpe for r in records]
        count = len(rpe_values)
        mean_rpe = sum(rpe_values) / count
        abs_max = max(abs(v) for v in rpe_values)

        # Trend: compare first half vs second half mean RPE
        mid = count // 2
        first_half_mean = sum(rpe_values[:mid]) / mid if mid > 0 else mean_rpe
        second_half_mean = sum(rpe_values[mid:]) / (count - mid) if (count - mid) > 0 else mean_rpe
        if abs(second_half_mean - first_half_mean) < 0.01:
            trend = "stable"
        elif second_half_mean > first_half_mean:
            trend = "improving"
        else:
            trend = "declining"

        # Threshold suggestion: 75th percentile of |RPE|
        abs_sorted = sorted(abs(v) for v in rpe_values)
        pct75_idx = int(count * 0.75)
        threshold_suggestion = round(abs_sorted[min(pct75_idx, count - 1)], 3)

        # Top |RPE| events (up to 5)
        indexed = list(enumerate(rpe_values))
        indexed.sort(key=lambda x: abs(x[1]), reverse=True)
        top_events = [
            {
                "decision_id": records[i].decision_id,
                "query": records[i].query[:80],
                "chosen_action": records[i].chosen_action,
                "rpe": round(records[i].rpe, 4),
                "timestamp": records[i].timestamp.isoformat(),
            }
            for i, _ in indexed[:5]
        ]

        return {
            "count": count,
            "mean_rpe": round(mean_rpe, 4),
            "abs_max_rpe": round(abs_max, 4),
            "trend": trend,
            "threshold_suggestion": threshold_suggestion,
            "top_events": top_events,
        }


class TelemetryRecorder:
    """Append-only JSONL logger with daily rotation.

    Each line is a JSON-serialised :class:`TelemetryRecord`.  Files are
    named ``YYYY-MM-DD.jsonl`` inside *directory*.
    """

    def __init__(self, directory: str | Path = "telemetry") -> None:
        self._directory = Path(directory)

    @property
    def directory(self) -> Path:
        return self._directory

    def _current_path(self) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return self._directory / f"{today}.jsonl"

    def record(self, record: TelemetryRecord) -> Path:
        """Append a telemetry record and return the file path written to."""
        path = self._current_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        return path

    def read_day(self, date_str: str | None = None) -> list[TelemetryRecord]:
        """Read all records for a given day (default: today)."""
        if date_str is None:
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        path = self._directory / f"{date_str}.jsonl"
        if not path.exists():
            return []
        records: list[TelemetryRecord] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(TelemetryRecord.model_validate_json(line))
        return records

    def list_days(self) -> list[str]:
        """Return sorted list of available date strings."""
        if not self._directory.exists():
            return []
        days = sorted(p.stem for p in self._directory.glob("????-??-??.jsonl") if p.is_file())
        return days
