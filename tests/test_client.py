"""Tests for the OllamaClient wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from another_intelligence.models.client import (
    ChatMessage,
    ChatRequest,
    GenerateRequest,
    ModelInfo,
    OllamaClient,
)


class DummySchema(BaseModel):
    """Dummy schema for structured output tests."""

    answer: str
    confidence: float


@pytest.fixture
def mock_ollama_client():
    """Return a mocked underlying ollama.Client instance."""
    return MagicMock()


@pytest.fixture
def client(mock_ollama_client):
    """Return an OllamaClient with a mocked backend."""
    with patch("another_intelligence.models.client.ollama.Client", return_value=mock_ollama_client):
        return OllamaClient()


def test_chat_plain_text(client, mock_ollama_client):
    """chat() delegates to the underlying client with plain messages."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content="hi"),
        model="llama3.1",
        done=True,
    )

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="hello")],
    )
    response = client.chat(request)

    mock_ollama_client.chat.assert_called_once()
    call_kwargs = mock_ollama_client.chat.call_args.kwargs
    assert call_kwargs["model"] == "llama3.1"
    assert len(call_kwargs["messages"]) == 1
    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"] == "hello"
    assert response.message.content == "hi"


def test_chat_structured_output_with_pydantic_model(client, mock_ollama_client):
    """chat() converts a Pydantic model to JSON schema for the format param."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content='{"answer": "42", "confidence": 0.99}'),
        model="llama3.1",
        done=True,
    )

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="what is the answer?")],
        format=DummySchema,
    )
    client.chat(request)

    call_kwargs = mock_ollama_client.chat.call_args.kwargs
    schema = call_kwargs["format"]
    assert isinstance(schema, dict)
    assert schema.get("title") == "DummySchema"
    assert "answer" in schema.get("properties", {})


def test_chat_structured_output_with_dict_schema(client, mock_ollama_client):
    """chat() passes through a dict schema unchanged."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content='{}'),
        model="llama3.1",
        done=True,
    )

    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="give me x")],
        format=schema,
    )
    client.chat(request)

    assert mock_ollama_client.chat.call_args.kwargs["format"] == schema


def test_chat_with_tools(client, mock_ollama_client):
    """chat() forwards tool definitions to the underlying client."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(
            role="assistant",
            content="",
            tool_calls=[
                MagicMock(
                    function=MagicMock(arguments={"city": "Berlin"}),
                ),
            ],
        ),
        model="llama3.1",
        done=True,
    )

    def get_weather(city: str) -> str:
        """Get the weather for a city."""
        return f"Weather in {city}"

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="weather in Berlin")],
        tools=[get_weather],
    )
    response = client.chat(request)

    call_kwargs = mock_ollama_client.chat.call_args.kwargs
    assert "tools" in call_kwargs
    assert len(call_kwargs["tools"]) == 1
    tool = call_kwargs["tools"][0]
    assert tool["function"]["name"] == "get_weather"
    assert tool["function"]["description"] == "Get the weather for a city."
    assert "city" in tool["function"]["parameters"]["properties"]

    assert response.message.tool_calls[0].function.arguments == {"city": "Berlin"}


def test_chat_with_tool_dicts(client, mock_ollama_client):
    """chat() passes through pre-built tool dicts unchanged."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content="ok"),
        model="llama3.1",
        done=True,
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "integer"}},
                    "required": ["a"],
                },
            },
        },
    ]
    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="add 1")],
        tools=tools,
    )
    client.chat(request)

    assert mock_ollama_client.chat.call_args.kwargs["tools"] == tools


def test_generate_plain(client, mock_ollama_client):
    """generate() delegates to the underlying client."""
    mock_ollama_client.generate.return_value = MagicMock(
        response="hello world",
        model="llama3.1",
        done=True,
    )

    request = GenerateRequest(model="llama3.1", prompt="say hello")
    response = client.generate(request)

    mock_ollama_client.generate.assert_called_once()
    call_kwargs = mock_ollama_client.generate.call_args.kwargs
    assert call_kwargs["model"] == "llama3.1"
    assert call_kwargs["prompt"] == "say hello"
    assert response.response == "hello world"


def test_generate_with_system_and_images(client, mock_ollama_client):
    """generate() forwards system prompt and images."""
    mock_ollama_client.generate.return_value = MagicMock(
        response="an image description",
        model="llava",
        done=True,
    )

    request = GenerateRequest(
        model="llava",
        prompt="describe this",
        system="You are a helpful assistant.",
        images=[b"fake_image_data"],
    )
    client.generate(request)

    call_kwargs = mock_ollama_client.generate.call_args.kwargs
    assert call_kwargs["system"] == "You are a helpful assistant."
    assert call_kwargs["images"] == [b"fake_image_data"]


def test_get_model_info_extracts_context_length(client, mock_ollama_client):
    """get_model_info() parses context_length from model_info."""
    mock_ollama_client.show.return_value = MagicMock(
        modelinfo={
            "context_length": 131072,
            "parameter_count": 8_000_000_000,
        },
        details=MagicMock(
            family="llama",
            parameter_size="8B",
            quantization_level="Q4_K_M",
        ),
    )

    info = client.get_model_info("llama3.1:8b")
    assert isinstance(info, ModelInfo)
    assert info.name == "llama3.1:8b"
    assert info.context_length == 131072
    assert info.parameter_size == "8B"
    assert info.family == "llama"
    assert info.quantization == "Q4_K_M"


def test_get_model_info_caches_result(client, mock_ollama_client):
    """get_model_info() caches show() results per model."""
    mock_ollama_client.show.return_value = MagicMock(
        modelinfo={"context_length": 4096},
        details=MagicMock(family="test", parameter_size="1B", quantization_level="Q4_0"),
    )

    client.get_model_info("cached-model")
    client.get_model_info("cached-model")

    assert mock_ollama_client.show.call_count == 1


def test_context_length_auto_injected_into_options(client, mock_ollama_client):
    """chat() automatically injects num_ctx when options omit it."""
    mock_ollama_client.show.return_value = MagicMock(
        modelinfo={"context_length": 8192},
        details=MagicMock(family="llama", parameter_size="3B", quantization_level="Q4_0"),
    )
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content="ok"),
        model="llama3.1",
        done=True,
    )

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="hi")],
        options={"temperature": 0.5},
    )
    client.chat(request)

    call_kwargs = mock_ollama_client.chat.call_args.kwargs
    assert call_kwargs["options"]["num_ctx"] == 8192
    assert call_kwargs["options"]["temperature"] == 0.5


def test_context_length_not_overridden_when_explicit(client, mock_ollama_client):
    """chat() does not override num_ctx when the user already set it."""
    mock_ollama_client.show.return_value = MagicMock(
        modelinfo={"context_length": 8192},
        details=MagicMock(family="llama", parameter_size="3B", quantization_level="Q4_0"),
    )
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content="ok"),
        model="llama3.1",
        done=True,
    )

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="hi")],
        options={"num_ctx": 4096, "temperature": 0.5},
    )
    client.chat(request)

    call_kwargs = mock_ollama_client.chat.call_args.kwargs
    assert call_kwargs["options"]["num_ctx"] == 4096


def test_chat_missing_model_raises(client, mock_ollama_client):
    """chat() raises RuntimeError when the underlying client reports a missing model."""
    from ollama import ResponseError

    mock_ollama_client.chat.side_effect = ResponseError("model not found", status_code=404)

    request = ChatRequest(
        model="missing-model",
        messages=[ChatMessage(role="user", content="hi")],
    )
    with pytest.raises(RuntimeError, match="model not found"):
        client.chat(request)


def test_generate_missing_model_raises(client, mock_ollama_client):
    """generate() raises RuntimeError when the underlying client reports a missing model."""
    from ollama import ResponseError

    mock_ollama_client.generate.side_effect = ResponseError("model not found", status_code=404)

    request = GenerateRequest(model="missing-model", prompt="hi")
    with pytest.raises(RuntimeError, match="model not found"):
        client.generate(request)


def test_chat_returns_raw_chat_response(client, mock_ollama_client):
    """chat() returns the raw ollama ChatResponse object."""
    raw = MagicMock(message=MagicMock(role="assistant", content="raw"), done=True)
    mock_ollama_client.chat.return_value = raw

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="hi")],
    )
    response = client.chat(request)

    assert response is raw


def test_format_json_literal(client, mock_ollama_client):
    """chat() passes the literal 'json' format through unchanged."""
    mock_ollama_client.chat.return_value = MagicMock(
        message=MagicMock(role="assistant", content='{"x":1}'),
        done=True,
    )

    request = ChatRequest(
        model="llama3.1",
        messages=[ChatMessage(role="user", content="json pls")],
        format="json",
    )
    client.chat(request)

    assert mock_ollama_client.chat.call_args.kwargs["format"] == "json"


def test_generate_structured_output(client, mock_ollama_client):
    """generate() converts Pydantic models to JSON schema for format."""
    mock_ollama_client.generate.return_value = MagicMock(
        response='{"answer": "42", "confidence": 0.99}',
        done=True,
    )

    request = GenerateRequest(
        model="llama3.1",
        prompt="what is the answer?",
        format=DummySchema,
    )
    client.generate(request)

    schema = mock_ollama_client.generate.call_args.kwargs["format"]
    assert isinstance(schema, dict)
    assert schema.get("title") == "DummySchema"
