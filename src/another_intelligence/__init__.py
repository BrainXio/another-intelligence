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
from another_intelligence.executor import (
    Evaluation,
    Executor,
)
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
from another_intelligence.mcp import (
    MCPClient,
    MCPConnection,
    MCPRegistry,
    MCPServerConfig,
    StdioConnection,
)
from another_intelligence.memory import (
    MemoryValueIndex,
    PreferencePair,
)
from another_intelligence.metrics import MetricsCollector
from another_intelligence.models import (
    ChatMessage,
    ChatRequest,
    GenerateRequest,
    ModelInfo,
    ModelResolver,
    OllamaClient,
    ResolvedModel,
)
from another_intelligence.permissions import (
    AuditLogEntry,
    Grant,
    PermissionConfig,
    PermissionDecision,
    PermissionEngine,
)
from another_intelligence.plugins import (
    Plugin,
    PluginLoader,
)
from another_intelligence.reflex import (
    Reflex,
    Selection,
)
from another_intelligence.rpe import (
    RPEEngine,
    RPEEntry,
)
from another_intelligence.state import (
    ActivityPhase,
    StateMachine,
)
from another_intelligence.statusline import StatuslineRenderer
from another_intelligence.strategist import (
    Proposal,
    Strategist,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "DigitalBrain",
    "ContextWindow",
    "BrainEvent",
    "BrainRegionActivated",
    "ContextWindowChanged",
    "MCPToolCalled",
    "PermissionRequested",
    "PostToolUse",
    "PreToolUse",
    "RPEUpdated",
    "SessionEnd",
    "SessionStart",
    "Evaluation",
    "Executor",
    "HookConfig",
    "HookRegistry",
    "HookResult",
    "HookRunner",
    "HookType",
    "Article",
    "KnowledgeCompiler",
    "KnowledgeQuery",
    "MCPClient",
    "MCPConnection",
    "MCPRegistry",
    "MCPServerConfig",
    "StdioConnection",
    "MemoryValueIndex",
    "PreferencePair",
    "MetricsCollector",
    "ChatMessage",
    "ChatRequest",
    "GenerateRequest",
    "ModelInfo",
    "OllamaClient",
    "ModelResolver",
    "ResolvedModel",
    "AuditLogEntry",
    "Grant",
    "PermissionConfig",
    "PermissionDecision",
    "PermissionEngine",
    "Plugin",
    "PluginLoader",
    "Reflex",
    "Selection",
    "RPEEntry",
    "RPEEngine",
    "ActivityPhase",
    "StateMachine",
    "StatuslineRenderer",
    "Proposal",
    "Strategist",
]
