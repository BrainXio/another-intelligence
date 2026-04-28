"""Tests for the typed event bus."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from another_intelligence.events import (
    BrainEvent,
    BrainRegionActivated,
    ContextWindowChanged,
    MCPToolCalled,
    PermissionRequested,
    PostToolUse,
    PreToolUse,
    RPEUpdated,
    SessionEnd,
    SessionStart,
)


class TestBrainEvent:
    """Base event behaviour."""

    def test_event_has_timestamp(self):
        before = datetime.now(UTC)
        event = BrainEvent()
        after = datetime.now(UTC)
        assert before <= event.timestamp <= after

    def test_event_accepts_custom_timestamp(self):
        ts = datetime(2026, 4, 28, 12, 0, 0, tzinfo=UTC)
        event = BrainEvent(timestamp=ts)
        assert event.timestamp == ts


class TestBrainRegionActivated:
    """BrainRegionActivated event validation."""

    def test_minimal_creation(self):
        event = BrainRegionActivated(region="strategist")
        assert event.region == "strategist"
        assert event.metadata is None

    def test_with_metadata(self):
        event = BrainRegionActivated(region="executor", metadata={"option_count": 3})
        assert event.metadata == {"option_count": 3}

    def test_region_required(self):
        with pytest.raises(ValidationError):
            BrainRegionActivated()  # type: ignore[call-arg]

    def test_region_must_be_string(self):
        with pytest.raises(ValidationError):
            BrainRegionActivated(region=123)  # type: ignore[arg-type]


class TestSessionEvents:
    """Session lifecycle events."""

    def test_session_start(self):
        event = SessionStart(session_id="sess-001")
        assert event.session_id == "sess-001"

    def test_session_end(self):
        event = SessionEnd(session_id="sess-001", reason="normal")
        assert event.session_id == "sess-001"
        assert event.reason == "normal"

    def test_session_start_requires_id(self):
        with pytest.raises(ValidationError):
            SessionStart()  # type: ignore[call-arg]


class TestToolEvents:
    """Tool use hook events."""

    def test_pre_tool_use(self):
        event = PreToolUse(tool_name="read_file", arguments={"path": "/tmp"})
        assert event.tool_name == "read_file"
        assert event.arguments == {"path": "/tmp"}

    def test_post_tool_use(self):
        event = PostToolUse(tool_name="read_file", success=True, duration_ms=42.0)
        assert event.tool_name == "read_file"
        assert event.success is True
        assert event.duration_ms == 42.0

    def test_pre_tool_use_requires_name(self):
        with pytest.raises(ValidationError):
            PreToolUse()  # type: ignore[call-arg]


class TestRPEUpdated:
    """RPE update event."""

    def test_creation(self):
        event = RPEUpdated(region="reflex", expected=0.5, actual=0.8, rpe=0.3)
        assert event.expected == 0.5
        assert event.actual == 0.8
        assert event.rpe == 0.3

    def test_rpe_computed_correctly(self):
        event = RPEUpdated(expected=0.5, actual=0.2)
        assert event.rpe == -0.3

    def test_rpe_explicit_override(self):
        event = RPEUpdated(expected=0.5, actual=0.8, rpe=99.0)
        assert event.rpe == 99.0

    def test_missing_expected(self):
        with pytest.raises(ValidationError):
            RPEUpdated(actual=0.8)  # type: ignore[call-arg]


class TestContextWindowChanged:
    """Context window events."""

    def test_creation(self):
        event = ContextWindowChanged(total_tokens=1024, max_tokens=4096)
        assert event.total_tokens == 1024
        assert event.max_tokens == 4096
        assert event.utilization == 0.25

    def test_utilization_computed(self):
        event = ContextWindowChanged(total_tokens=2048, max_tokens=4096)
        assert event.utilization == 0.5

    def test_utilization_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            ContextWindowChanged(total_tokens=-1, max_tokens=100)


class TestPermissionRequested:
    """Permission event."""

    def test_creation(self):
        event = PermissionRequested(capability="filesystem", action="write", granted=False)
        assert event.capability == "filesystem"
        assert event.action == "write"
        assert event.granted is False


class TestMCPToolCalled:
    """MCP tool call event."""

    def test_creation(self):
        event = MCPToolCalled(server="filesystem", tool="read", params={"path": "/"})
        assert event.server == "filesystem"
        assert event.tool == "read"
        assert event.params == {"path": "/"}
