"""Typed event bus for brain activity and lifecycle events."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class BrainEvent(BaseModel):
    """Base class for all brain events."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BrainRegionActivated(BrainEvent):
    """Emitted when a brain region becomes active."""

    region: str
    metadata: dict[str, Any] | None = None


class SessionStart(BrainEvent):
    """Emitted at the beginning of a session."""

    session_id: str


class SessionEnd(BrainEvent):
    """Emitted at the end of a session."""

    session_id: str
    reason: str = "normal"


class PreToolUse(BrainEvent):
    """Emitted before a tool is invoked."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class PostToolUse(BrainEvent):
    """Emitted after a tool invocation completes."""

    tool_name: str
    success: bool
    duration_ms: float = 0.0


class RPEUpdated(BrainEvent):
    """Reward Prediction Error update event."""

    expected: float
    actual: float
    rpe: float | None = None
    region: str = "reflex"

    @model_validator(mode="after")
    def compute_rpe(self) -> "RPEUpdated":
        if self.rpe is None:
            self.rpe = self.actual - self.expected
        return self


class ContextWindowChanged(BrainEvent):
    """Emitted when context window utilization changes."""

    total_tokens: int = Field(ge=0)
    max_tokens: int = Field(gt=0)

    @property
    def utilization(self) -> float:
        return self.total_tokens / self.max_tokens


class PermissionRequested(BrainEvent):
    """Emitted when a capability permission is requested."""

    capability: str
    action: str
    granted: bool = False


class MCPToolCalled(BrainEvent):
    """Emitted when an MCP tool is called."""

    server: str
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
