"""Pydantic models for the hook system."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class HookType(StrEnum):
    """Supported hook implementation types."""

    SHELL = "shell"
    PYTHON = "python"
    MCP = "mcp"


class HookConfig(BaseModel):
    """Configuration for a single hook handler."""

    event_type: str
    type: HookType
    command: str | None = None
    entry_point: str | None = None
    server: str | None = None
    tool: str | None = None
    critical: bool = False

    @model_validator(mode="after")
    def _validate_fields(self) -> HookConfig:
        if self.type == HookType.SHELL and not self.command:
            raise ValueError("shell hooks require 'command'")
        if self.type == HookType.PYTHON and not self.entry_point:
            raise ValueError("python hooks require 'entry_point'")
        if self.type == HookType.MCP and (not self.server or not self.tool):
            raise ValueError("mcp hooks require 'server' and 'tool'")
        return self


class HookResult(BaseModel):
    """Result of executing a single hook."""

    success: bool
    output: Any | None = None
    error: str | None = None
    duration_ms: float = 0.0
    config: HookConfig | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
