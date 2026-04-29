"""Ollama client wrapper with structured output, tool calling, and context-length handling."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

import ollama
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str | None = None
    images: Sequence[str | bytes] | None = None
    tool_calls: Sequence[Mapping[str, Any]] | None = None
    tool_name: str | None = None


class ToolCallFunction(BaseModel):
    """Function inside a tool call."""

    name: str
    arguments: Mapping[str, Any]


class ToolCall(BaseModel):
    """A tool call emitted by the model."""

    function: ToolCallFunction


class ChatRequest(BaseModel):
    """Parameters for a chat request."""

    model: str
    messages: Sequence[ChatMessage]
    tools: Sequence[Callable[..., Any]] | Sequence[Mapping[str, Any]] | None = None
    format: type[BaseModel] | dict[str, Any] | Literal["json"] | None = None
    options: dict[str, Any] | None = None
    stream: bool = False


class GenerateRequest(BaseModel):
    """Parameters for a generate request."""

    model: str
    prompt: str
    system: str | None = None
    images: Sequence[str | bytes] | None = None
    format: type[BaseModel] | dict[str, Any] | Literal["json"] | None = None
    options: dict[str, Any] | None = None
    stream: bool = False


class ModelInfo(BaseModel):
    """Metadata about an Ollama model."""

    name: str
    context_length: int | None = None
    parameter_size: str | None = None
    family: str | None = None
    quantization: str | None = None


def _callable_to_tool(fn: Callable[..., Any]) -> dict[str, Any]:
    """Convert a Python callable to an Ollama tool dict."""
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        param_type = param.annotation if param.annotation is not inspect.Parameter.empty else str
        json_type: str = "string"
        if param_type in (int,):
            json_type = "integer"
        elif param_type in (float,):
            json_type = "number"
        elif param_type in (bool,):
            json_type = "boolean"
        elif param_type in (list,):
            json_type = "array"
        elif param_type in (dict,):
            json_type = "object"
        properties[param_name] = {"type": json_type}

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": (fn.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _prepare_tools(
    tools: Sequence[Callable[..., Any]] | Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    """Normalize tools to a list of dicts for ollama."""
    if tools is None:
        return None
    result: list[dict[str, Any]] = []
    for tool in tools:
        if callable(tool):
            result.append(_callable_to_tool(tool))
        else:
            result.append(dict(tool))
    return result


def _prepare_format(
    format: type[BaseModel] | dict[str, Any] | Literal["json"] | None,
) -> dict[str, Any] | Literal["json"] | None:
    """Normalize format to JSON schema dict, 'json', or None."""
    if format is None:
        return None
    if isinstance(format, str):
        return format
    if isinstance(format, dict):
        return format
    if isinstance(format, type) and issubclass(format, BaseModel):
        return format.model_json_schema()
    return None


class OllamaClient:
    """Wraps the official ``ollama`` Python client with convenience helpers."""

    def __init__(self, host: str = "http://localhost:11434", timeout: float | None = None) -> None:
        """Create a new client pointing at *host*.

        Args:
            host: URL of the Ollama server.
            timeout: Request timeout in seconds.
        """
        kwargs: dict[str, Any] = {"host": host}
        if timeout is not None:
            kwargs["timeout"] = timeout
        self._host = host
        self._client = ollama.Client(**kwargs)
        self._info_cache: dict[str, ModelInfo] = {}

    @property
    def host(self) -> str:
        """URL of the Ollama server this client talks to."""
        return self._host

    def list(self) -> ollama.ListResponse:
        """Return the list of locally available models."""
        return self._client.list()

    def get_model_info(self, model: str) -> ModelInfo:
        """Fetch metadata for *model*, caching results."""
        if model in self._info_cache:
            return self._info_cache[model]

        try:
            raw = self._client.show(model)
        except ollama.ResponseError as exc:
            raise RuntimeError(f"Failed to get info for model {model}: {exc}") from exc

        model_info: Mapping[str, Any] | None = None
        if hasattr(raw, "modelinfo"):
            model_info = raw.modelinfo
        elif hasattr(raw, "model_info"):
            model_info = raw.model_info

        context_length: int | None = None
        if model_info is not None:
            context_length = model_info.get("context_length") or model_info.get("num_ctx")
            if context_length is not None:
                context_length = int(context_length)

        details = getattr(raw, "details", None)
        param_size = getattr(details, "parameter_size", None) if details else None
        family = getattr(details, "family", None) if details else None
        quantization = getattr(details, "quantization_level", None) if details else None

        # Guard against MagicMock objects from unconfigured mocks in tests.
        param_size = param_size if isinstance(param_size, str) else None
        family = family if isinstance(family, str) else None
        quantization = quantization if isinstance(quantization, str) else None

        info = ModelInfo(
            name=model,
            context_length=context_length,
            parameter_size=param_size,
            family=family,
            quantization=quantization,
        )
        self._info_cache[model] = info
        return info

    def _prepare_options(self, model: str, options: dict[str, Any] | None) -> dict[str, Any]:
        """Merge user options with auto-detected ``num_ctx``."""
        opts = dict(options) if options else {}
        if "num_ctx" in opts:
            return opts

        info = self.get_model_info(model)
        if info.context_length is not None:
            opts["num_ctx"] = info.context_length
        return opts

    def chat(self, request: ChatRequest) -> ollama.ChatResponse:
        """Send a chat request and return the response."""
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"images": list(msg.images)} if msg.images else {}),
                **({"tool_calls": list(msg.tool_calls)} if msg.tool_calls else {}),
                **({"tool_name": msg.tool_name} if msg.tool_name else {}),
            }
            for msg in request.messages
        ]

        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "tools": _prepare_tools(request.tools),
            "format": _prepare_format(request.format),
            "options": self._prepare_options(request.model, request.options),
            "stream": request.stream,
        }
        # Remove None values so ollama uses defaults
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            return self._client.chat(**kwargs)  # type: ignore[no-any-return]
        except ollama.ResponseError as exc:
            raise RuntimeError(f"Chat request failed: {exc}") from exc

    def generate(self, request: GenerateRequest) -> ollama.GenerateResponse:
        """Send a generate request and return the response."""
        kwargs: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "system": request.system,
            "images": list(request.images) if request.images else None,
            "format": _prepare_format(request.format),
            "options": self._prepare_options(request.model, request.options),
            "stream": request.stream,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            return self._client.generate(**kwargs)  # type: ignore[no-any-return]
        except ollama.ResponseError as exc:
            raise RuntimeError(f"Generate request failed: {exc}") from exc
