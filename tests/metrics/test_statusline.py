"""Tests for the StatuslineRenderer observability module."""

from another_intelligence.metrics import MetricsCollector
from another_intelligence.state import ActivityPhase, StateMachine
from another_intelligence.statusline import StatuslineRenderer


class TestStatuslineRendererInit:
    """Construction and default state."""

    def test_basic_init(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        assert renderer._metrics is metrics
        assert renderer._state is None

    def test_init_with_state(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        state = StateMachine()
        renderer = StatuslineRenderer(metrics, state=state)
        assert renderer._state is state


class TestRenderBasic:
    """Plain-text status line rendering."""

    def test_render_contains_phase(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render()
        assert "[phase:unknown]" in line

    def test_render_contains_rpe(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render()
        assert "rpe=n/a" in line

    def test_render_with_state(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        state = StateMachine()
        state.transition_to(ActivityPhase.PROPOSING)
        renderer = StatuslineRenderer(metrics, state=state)
        line = renderer.render()
        assert "[phase:proposing]" in line

    def test_render_with_regions(self):
        from another_intelligence.events import BrainRegionActivated

        metrics = MetricsCollector(enable_system_metrics=False)
        metrics.record_event(BrainRegionActivated(region="strategist"))
        renderer = StatuslineRenderer(metrics)
        line = renderer.render()
        assert "regions=strategist" in line

    def test_render_extended(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render(extended=True)
        assert "uptime=" in line
        assert "events=0" in line
        assert "history=" in line

    def test_render_with_context(self):
        from another_intelligence.events import ContextWindowChanged

        metrics = MetricsCollector(enable_system_metrics=False)
        metrics.record_event(ContextWindowChanged(total_tokens=100, max_tokens=1000))
        renderer = StatuslineRenderer(metrics)
        line = renderer.render()
        assert "context=100/1000" in line

    def test_render_with_system(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render()
        assert "sys=CPU 0% | MEM 0%" in line


class TestRenderRich:
    """Rich-formatted status line rendering."""

    def test_render_rich_fallback(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render_rich()
        assert "[phase:unknown]" in line

    def test_render_rich_extended(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        line = renderer.render_rich(extended=True)
        assert "uptime=" in line


class TestStrRepr:
    """String and repr behaviour."""

    def test_str_calls_render(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        assert str(renderer) == renderer.render()

    def test_repr(self):
        metrics = MetricsCollector(enable_system_metrics=False)
        renderer = StatuslineRenderer(metrics)
        rep = repr(renderer)
        assert "StatuslineRenderer" in rep
