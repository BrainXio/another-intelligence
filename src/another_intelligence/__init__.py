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
from another_intelligence.hooks import (
    HookConfig,
    HookRegistry,
    HookResult,
    HookRunner,
    HookType,
)
from another_intelligence.knowledge import (
    Article,
    KnowledgeCompiler,
    KnowledgeQuery,
)
from another_intelligence.mcp.client import (
    MCPClient,
    MCPConnection,
    MCPRegistry,
    MCPServerConfig,
    StdioConnection,
)
from another_intelligence.memory.value_index import MemoryValueIndex
from another_intelligence.metrics import MetricsCollector
from another_intelligence.permissions.engine import (
    AuditLogEntry,
    Grant,
    PermissionConfig,
    PermissionDecision,
    PermissionEngine,
)
from another_intelligence.reflex import Reflex, Selection
from another_intelligence.rpe import RPEEngine
from another_intelligence.state import ActivityPhase, StateMachine
from another_intelligence.statusline import StatuslineRenderer
from another_intelligence.strategist import Proposal, Strategist

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "ActivityPhase",
    "Article",
    "AuditLogEntry",
    "BrainEvent",
    "BrainRegionActivated",
    "ContextWindow",
    "ContextWindowChanged",
    "DigitalBrain",
    "Evaluation",
    "Executor",
    "Grant",
    "HookConfig",
    "HookRegistry",
    "HookResult",
    "HookRunner",
    "HookType",
    "KnowledgeCompiler",
    "KnowledgeQuery",
    "MCPClient",
    "MCPConnection",
    "MCPRegistry",
    "MCPServerConfig",
    "MCPToolCalled",
    "MemoryValueIndex",
    "MetricsCollector",
    "PermissionConfig",
    "PermissionDecision",
    "PermissionEngine",
    "PermissionRequested",
    "PostToolUse",
    "PreToolUse",
    "Proposal",
    "RPEEngine",
    "RPEUpdated",
    "Reflex",
    "Selection",
    "SessionEnd",
    "SessionStart",
    "StateMachine",
    "StatuslineRenderer",
    "StdioConnection",
    "Strategist",
]
