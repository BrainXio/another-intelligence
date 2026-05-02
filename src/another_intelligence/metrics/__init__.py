"""Metrics collection and event logging for DigitalBrain observability."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psutil

from another_intelligence.paths import STATE_DIR

from another_intelligence.events import (
    BrainEvent,
    BrainRegionActivated,
    ContextWindowChanged,
    RPEUpdated,
)
from another_intelligence.state import ActivityPhase


class MetricsCollector:
    """Collects real-time metrics and maintains an append-only event log.

    Tracks context window usage, system resources, brain activity, and
    model performance. Events are optionally persisted to
    ``~/.brainxio/state/brain_activity.jsonl``.
    """

    _DEFAULT_LOG_DIR = STATE_DIR
    _DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "brain_activity.jsonl"

    def __init__(
        self,
        *,
        log_file: str | Path | None = None,
        enable_system_metrics: bool = True,
    ) -> None:
        self._enable_system = enable_system_metrics
        self._log_file = Path(log_file) if log_file else self._DEFAULT_LOG_FILE
        self._ensure_log_dir()

        self._latest_rpe: float | None = None
        self._latest_context: dict[str, Any] | None = None
        self._active_regions: set[str] = set()
        self._region_history: list[str] = []
        self._event_count: int = 0
        self._start_time: float = time.time()

    def _ensure_log_dir(self) -> None:
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def latest_rpe(self) -> float | None:
        return self._latest_rpe

    @property
    def latest_context(self) -> dict[str, Any] | None:
        return self._latest_context.copy() if self._latest_context else None

    @property
    def active_regions(self) -> set[str]:
        return self._active_regions.copy()

    @property
    def region_history(self) -> list[str]:
        return self._region_history.copy()

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def system_snapshot(self) -> dict[str, float]:
        """Return current CPU and memory utilization."""
        if not self._enable_system:
            return {"cpu_percent": 0.0, "memory_percent": 0.0}
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
        }

    def record_event(self, event: BrainEvent) -> None:
        """Process a brain event and append it to the log."""
        self._event_count += 1

        if isinstance(event, BrainRegionActivated):
            self._active_regions.add(event.region)
            self._region_history.append(event.region)

        if isinstance(event, RPEUpdated):
            self._latest_rpe = event.rpe

        if isinstance(event, ContextWindowChanged):
            self._latest_context = {
                "total_tokens": event.total_tokens,
                "max_tokens": event.max_tokens,
                "utilization": event.utilization,
            }

        self._append_to_log(event)

    def _append_to_log(self, event: BrainEvent) -> None:
        record = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": type(event).__name__,
            "payload": event.model_dump(mode="json"),
        }
        with self._log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def snapshot(self, phase: ActivityPhase | None = None) -> dict[str, Any]:
        """Return a full metrics snapshot."""
        return {
            "uptime_seconds": self.uptime_seconds,
            "event_count": self._event_count,
            "active_regions": sorted(self._active_regions),
            "region_history": self._region_history[-10:],
            "latest_rpe": self._latest_rpe,
            "context": self._latest_context,
            "system": self.system_snapshot(),
            "phase": phase.value if phase else None,
        }

    def as_hook(self) -> Callable[[BrainEvent], None]:
        """Return a callback suitable for ``DigitalBrain.register_hook``."""
        return self.record_event

    def read_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Read the last *limit* lines from the event log."""
        if not self._log_file.exists():
            return []
        with self._log_file.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return records[-limit:]

    def clear_log(self) -> None:
        """Truncate the event log file (testing helper)."""
        if self._log_file.exists():
            self._log_file.unlink()
        self._ensure_log_dir()


__all__ = ["MetricsCollector"]
