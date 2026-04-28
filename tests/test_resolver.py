"""Tests for the tiered model resolver."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from another_intelligence.models.resolver import ModelResolver, ResolvedModel


@pytest.fixture
def mock_ollama_client():
    """Return a mocked OllamaClient instance."""
    mock = MagicMock()
    mock.host = "http://localhost:11434"
    return mock


@pytest.fixture
def resolver(mock_ollama_client):
    """Return a ModelResolver using a mocked client."""
    with patch(
        "another_intelligence.models.resolver.OllamaClient",
        return_value=mock_ollama_client,
    ):
        return ModelResolver()


def test_default_tier_cloud_max(resolver, mock_ollama_client):
    """resolve(':cloud-max') maps to the first available model in the fallback chain."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[
            MagicMock(model="qwen2.5:32b"),
            MagicMock(model="llama3.1:8b"),
        ],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=32768,
        parameter_size="32B",
        family="qwen2",
        quantization="Q4_K_M",
    )

    result = resolver.resolve(":cloud-max")
    assert isinstance(result, ResolvedModel)
    assert result.name == "qwen2.5:32b"
    assert result.tier == ":cloud-max"
    assert result.context_length == 32768


def test_default_tier_cloud_pro_fallback(resolver, mock_ollama_client):
    """resolve(':cloud-pro') falls back through the chain until it finds an available model."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[
            MagicMock(model="llama3.1:8b"),
        ],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=8192,
        parameter_size="8B",
        family="llama",
        quantization="Q4_K_M",
    )

    result = resolver.resolve(":cloud-pro")
    assert result.name == "llama3.1:8b"
    assert result.tier == ":cloud-pro"


def test_resolve_exact_model_name(resolver, mock_ollama_client):
    """resolve() with an exact model name returns it directly."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[MagicMock(model="my-custom-model")],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=4096,
        parameter_size="1B",
        family="custom",
        quantization="Q4_0",
    )

    result = resolver.resolve("my-custom-model")
    assert result.name == "my-custom-model"
    assert result.tier == "local"


def test_resolve_raises_when_no_model_available(resolver, mock_ollama_client):
    """resolve() raises RuntimeError when no model in the fallback chain is available."""
    mock_ollama_client.list.return_value = MagicMock(models=[])

    with pytest.raises(RuntimeError, match="No available model"):
        resolver.resolve(":cloud-max")


def test_register_tier(resolver, mock_ollama_client):
    """register_tier() adds a new tier alias dynamically."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[MagicMock(model="tinyllama")],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=2048,
        parameter_size="1B",
        family="llama",
        quantization="Q4_0",
    )

    resolver.register_tier(":experimental", ["not-found", "tinyllama"])
    result = resolver.resolve(":experimental")
    assert result.name == "tinyllama"
    assert result.tier == ":experimental"


def test_list_available(resolver, mock_ollama_client):
    """list_available() returns names of locally installed models."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[
            MagicMock(model="llama3.1:8b"),
            MagicMock(model="qwen2.5:14b"),
        ],
    )

    available = resolver.list_available()
    assert available == ["llama3.1:8b", "qwen2.5:14b"]


def test_gguf_detection_by_suffix(resolver, mock_ollama_client):
    """A model name ending in .gguf is detected as local GGUF."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[MagicMock(model="my-model.gguf")],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=4096,
        parameter_size="7B",
        family="llama",
        quantization="Q4_K_M",
    )

    result = resolver.resolve("my-model.gguf")
    assert result.name == "my-model.gguf"
    assert result.tier == "local"


def test_user_overrides_at_init(mock_ollama_client):
    """User overrides at __init__ replace default tier mappings."""
    with patch(
        "another_intelligence.models.resolver.OllamaClient",
        return_value=mock_ollama_client,
    ):
        overrides = {":cloud-max": ["custom-model:70b"]}
        resolver = ModelResolver(overrides=overrides)

    mock_ollama_client.list.return_value = MagicMock(
        models=[MagicMock(model="custom-model:70b")],
    )
    mock_ollama_client.get_model_info.return_value = MagicMock(
        context_length=128000,
        parameter_size="70B",
        family="custom",
        quantization="Q4_K_M",
    )

    result = resolver.resolve(":cloud-max")
    assert result.name == "custom-model:70b"


def test_context_length_from_hint_when_show_fails(resolver, mock_ollama_client):
    """If get_model_info fails, resolver falls back to the tier's context_length_hint."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[MagicMock(model="qwen2.5:32b")],
    )
    mock_ollama_client.get_model_info.side_effect = RuntimeError("show failed")

    result = resolver.resolve(":cloud-max")
    assert result.context_length == 32768


def test_resolve_local_with_no_alias_prefers_largest(resolver, mock_ollama_client):
    """resolve('local') without alias picks the largest available model by parameter size."""
    mock_ollama_client.list.return_value = MagicMock(
        models=[
            MagicMock(model="tinyllama"),
            MagicMock(model="llama3.3:70b"),
            MagicMock(model="qwen2.5:14b"),
        ],
    )
    mock_ollama_client.get_model_info.side_effect = [
        MagicMock(context_length=2048, parameter_size="1.1B", family="llama", quantization="Q4_0"),
        MagicMock(context_length=131072, parameter_size="70B", family="llama", quantization="Q4_K_M"),
        MagicMock(context_length=32768, parameter_size="14B", family="qwen2", quantization="Q4_K_M"),
        MagicMock(context_length=131072, parameter_size="70B", family="llama", quantization="Q4_K_M"),
    ]

    result = resolver.resolve("local")
    assert result.name == "llama3.3:70b"
    assert result.tier == "local"
