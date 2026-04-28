"""Another-Intelligence — A persistent neuroscience-grounded digital brain."""

from another_intelligence.brain import DigitalBrain
from another_intelligence.context import ContextWindow
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
from another_intelligence.executor import Evaluation, Executor
from another_intelligence.permissions.engine import (
    AuditLogEntry,
    Grant,
    PermissionConfig,
    PermissionDecision,
    PermissionEngine,
)
from another_intelligence.reflex import Reflex, Selection
from another_intelligence.state import ActivityPhase, StateMachine
from another_intelligence.strategist import Proposal, Strategist

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "ActivityPhase",
    "AuditLogEntry",
    "BrainEvent",
    "BrainRegionActivated",
    "ContextWindow",
    "ContextWindowChanged",
    "DigitalBrain",
    "Evaluation",
    "Executor",
    "Grant",
    "MCPToolCalled",
    "PermissionConfig",
    "PermissionDecision",
    "PermissionEngine",
    "PermissionRequested",
    "PostToolUse",
    "PreToolUse",
    "Proposal",
    "RPEUpdated",
    "Reflex",
    "Selection",
    "SessionEnd",
    "SessionStart",
    "StateMachine",
    "Strategist",
]
