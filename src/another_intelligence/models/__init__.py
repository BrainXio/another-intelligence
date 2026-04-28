"""Model layer: Ollama client wrapper and tiered resolver."""

from another_intelligence.models.client import (
    ChatMessage,
    ChatRequest,
    GenerateRequest,
    ModelInfo,
    OllamaClient,
)
from another_intelligence.models.resolver import ModelResolver, ResolvedModel

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "GenerateRequest",
    "ModelInfo",
    "OllamaClient",
    "ModelResolver",
    "ResolvedModel",
]
