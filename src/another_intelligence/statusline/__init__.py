"""Statusline renderer for live DigitalBrain state."""

from __future__ import annotations

from typing import Any

from another_intelligence.metrics import MetricsCollector
from another_intelligence.state import StateMachine

__all__ = ["StatuslineRenderer"]


class StatuslineRenderer:
    """Render a human-readable status line from current brain metrics.

    Supports plain text and rich-formatted output. Example usage::

        renderer = StatuslineRenderer(metrics, brain.state)
        print(renderer.render())
    """

    def __init__(
        self,
        metrics: MetricsCollector,
        state: StateMachine | None = None,
    ) -> None:
        self._metrics = metrics
        self._state = state

    def _format_rpe(self, rpe: float | None) -> str:
        if rpe is None:
            return "n/a"
        return f"{rpe:+.3f}"

    def _format_context(self, ctx: dict[str, Any] | None) -> str:
        if ctx is None:
            return "n/a"
        total = ctx.get("total_tokens", 0)
        max_tokens = ctx.get("max_tokens", 0)
        util = ctx.get("utilization", 0.0)
        return f"{total}/{max_tokens} ({util:.1%})"

    def _format_system(self, sys: dict[str, float] | None) -> str:
        if sys is None:
            return "n/a"
        cpu = sys.get("cpu_percent", 0.0)
        mem = sys.get("memory_percent", 0.0)
        return f"CPU {cpu:.0f}% | MEM {mem:.0f}%"

    def render(self, *, extended: bool = False) -> str:
        """Return a plain-text status line.

        Args:
            extended: Include region history and uptime.
        """
        snap = self._metrics.snapshot(
            self._state.current if self._state else None,
        )
        parts: list[str] = []

        phase = snap.get("phase") or "unknown"
        parts.append(f"[phase:{phase}]")

        rpe = self._format_rpe(snap.get("latest_rpe"))
        parts.append(f"rpe={rpe}")

        regions = snap.get("active_regions", [])
        parts.append(f"regions={','.join(regions) if regions else 'none'}")

        ctx = self._format_context(snap.get("context"))
        parts.append(f"context={ctx}")

        sys_info = self._format_system(snap.get("system"))
        parts.append(f"sys={sys_info}")

        if extended:
            hist = snap.get("region_history", [])
            parts.append(f"history={','.join(hist)}")
            uptime = snap.get("uptime_seconds", 0.0)
            parts.append(f"uptime={uptime:.1f}s")
            parts.append(f"events={snap.get('event_count', 0)}")

        return " ".join(parts)

    def render_rich(self, *, extended: bool = False) -> str:
        """Return a rich-formatted status line with colour tags.

        Requires the ``rich`` library to display properly.
        """
        try:
            from rich.text import Text

            snap = self._metrics.snapshot(
                self._state.current if self._state else None,
            )
            text = Text()

            phase = snap.get("phase") or "unknown"
            text.append(f"[phase:{phase}]", style="bold cyan")
            text.append(" ")

            rpe = snap.get("latest_rpe")
            rpe_str = self._format_rpe(rpe)
            rpe_style = "green" if rpe is not None and rpe >= 0 else "red"
            text.append(f"rpe={rpe_str}", style=rpe_style)
            text.append(" ")

            regions = snap.get("active_regions", [])
            text.append(
                f"regions={','.join(regions) if regions else 'none'}",
                style="yellow",
            )
            text.append(" ")

            ctx = self._format_context(snap.get("context"))
            text.append(f"context={ctx}", style="magenta")
            text.append(" ")

            sys_info = self._format_system(snap.get("system"))
            text.append(f"sys={sys_info}", style="blue")

            if extended:
                hist = snap.get("region_history", [])
                text.append(" ")
                text.append(f"history={','.join(hist)}", style="dim")
                uptime = snap.get("uptime_seconds", 0.0)
                text.append(" ")
                text.append(f"uptime={uptime:.1f}s", style="dim")
                text.append(" ")
                text.append(f"events={snap.get('event_count', 0)}", style="dim")

            return text.plain
        except Exception:
            return self.render(extended=extended)

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"StatuslineRenderer(metrics={self._metrics!r}, state={self._state!r})"
