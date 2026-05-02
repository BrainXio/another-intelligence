"""Tiered model resolver with fallback chains, context-length hints, and TTL caching."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

from another_intelligence.models.client import OllamaClient


class ResolvedModel(BaseModel):
    """A model alias resolved to a concrete local model."""

    name: str
    tier: str
    context_length: int | None = None
    host: str = "http://localhost:11434"


class ModelResolver:
    """Resolves tiered aliases like ``:cloud-max`` to locally installed Ollama models.

    Results are cached with a configurable TTL to avoid repeated Ollama
    API calls for model listings and metadata lookups.
    """

    _DEFAULT_TIERS: dict[str, list[str]] = {
        ":cloud-max": [
            "qwq:32b",
            "qwen2.5:32b",
            "llama3.3:70b",
        ],
        ":cloud-pro": [
            "qwen2.5:14b",
            "llama3.1:8b",
            "phi4:14b",
        ],
    }

    _DEFAULT_HINTS: dict[str, int] = {
        ":cloud-max": 32768,
        ":cloud-pro": 32768,
    }

    def __init__(
        self,
        host: str = "http://localhost:11434",
        overrides: dict[str, list[str]] | None = None,
        cache_ttl: float = 30.0,
    ) -> None:
        """Create a resolver.

        Args:
            host: URL of the Ollama server.
            overrides: Mapping from tier alias to fallback chain that
                replaces the default mapping for that alias.
            cache_ttl: Seconds before cached model listings and metadata
                expire. Set to 0 to disable caching.
        """
        self._client = OllamaClient(host=host)
        self._tiers = dict(self._DEFAULT_TIERS)
        if overrides:
            self._tiers.update(overrides)
        self._hints = dict(self._DEFAULT_HINTS)
        self._cache_ttl = cache_ttl
        self._list_cache: tuple[float, list[str]] | None = None
        self._available_cache: tuple[float, set[str]] | None = None
        self._model_info_cache: dict[str, tuple[float, Any]] = {}

    def register_tier(
        self,
        alias: str,
        fallback_chain: list[str],
        context_length_hint: int | None = None,
    ) -> None:
        """Dynamically register a new tier alias."""
        self._tiers[alias] = fallback_chain
        if context_length_hint is not None:
            self._hints[alias] = context_length_hint
        self.invalidate_cache()

    def list_available(self) -> list[str]:
        """Return names of all locally installed models (cached with TTL)."""
        if self._cache_ttl <= 0:
            return self._fetch_model_list()

        now = time.monotonic()
        if self._list_cache is not None:
            ts, data = self._list_cache
            if now - ts < self._cache_ttl:
                return data

        data = self._fetch_model_list()
        self._list_cache = (now, data)
        return data

    def _fetch_model_list(self) -> list[str]:
        raw = self._client.list()
        models = getattr(raw, "models", raw)
        return [str(getattr(m, "model", m)) for m in models]

    def _get_available(self) -> set[str]:
        """Return a cached set of available model names."""
        if self._cache_ttl <= 0:
            return set(self._fetch_model_list())

        now = time.monotonic()
        if self._available_cache is not None:
            ts, data = self._available_cache
            if now - ts < self._cache_ttl:
                return data

        data = set(self.list_available())
        self._available_cache = (now, data)
        return data

    def _resolve_name(self, alias: str) -> str:
        """Map an alias to the first available model in its fallback chain."""
        if alias not in self._tiers:
            return alias

        available = self._get_available()
        for name in self._tiers[alias]:
            if name in available:
                return name

        msg = f"No available model found for alias {alias!r}"
        raise RuntimeError(msg)

    def _extract_param_size(self, size_str: str | None) -> int:
        """Extract a numeric size from strings like ``70B`` or ``1.1B``."""
        if size_str is None:
            return 0
        size_str = size_str.strip().upper()
        if size_str.endswith("B"):
            size_str = size_str[:-1]
        try:
            return int(float(size_str))
        except ValueError:
            return 0

    def _pick_largest(self, names: list[str]) -> str:
        """Pick the largest model by parameter size."""
        largest_name = names[0]
        largest_size = 0
        for name in names:
            try:
                info = self._cached_model_info(name)
            except RuntimeError:
                continue
            size = self._extract_param_size(info.parameter_size)
            if size > largest_size:
                largest_size = size
                largest_name = name
        return largest_name

    def _cached_model_info(self, name: str) -> Any:
        """Return model info, caching the result with TTL."""
        if self._cache_ttl <= 0:
            return self._client.get_model_info(name)

        now = time.monotonic()
        cached = self._model_info_cache.get(name)
        if cached is not None:
            ts, info = cached
            if now - ts < self._cache_ttl:
                return info

        info = self._client.get_model_info(name)
        self._model_info_cache[name] = (now, info)
        return info

    def resolve(self, alias: str) -> ResolvedModel:
        """Resolve *alias* to a concrete locally installed model.

        Args:
            alias: Tier alias (e.g. ``:cloud-max``) or exact model name.

        Returns:
            A ``ResolvedModel`` with the concrete name and metadata.
        """
        if alias.endswith(".gguf"):
            return ResolvedModel(name=alias, tier="local")

        if alias == "local":
            available = self.list_available()
            if not available:
                raise RuntimeError("No available local models found")
            name = self._pick_largest(available)
            return self._resolve_and_enrich(name, tier="local")

        name = self._resolve_name(alias)
        tier = alias if alias in self._tiers else "local"
        return self._resolve_and_enrich(name, tier=tier)

    def _resolve_and_enrich(self, name: str, tier: str) -> ResolvedModel:
        """Fetch metadata and build a ``ResolvedModel``."""
        try:
            info = self._cached_model_info(name)
        except RuntimeError:
            hint = self._hints.get(tier)
            return ResolvedModel(
                name=name,
                tier=tier,
                context_length=hint,
                host=self._client.host,
            )

        return ResolvedModel(
            name=name,
            tier=tier,
            context_length=info.context_length,
            host=self._client.host,
        )

    def invalidate_cache(self) -> None:
        """Clear all cached model listings and metadata."""
        self._list_cache = None
        self._available_cache = None
        self._model_info_cache.clear()
