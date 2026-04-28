"""Tiered model resolver with fallback chains and context-length hints."""

from __future__ import annotations

from pydantic import BaseModel

from another_intelligence.models.client import ModelInfo, OllamaClient


class ResolvedModel(BaseModel):
    """A model alias resolved to a concrete local model."""

    name: str
    tier: str
    context_length: int | None = None
    host: str = "http://localhost:11434"


class ModelResolver:
    """Resolves tiered aliases like ``:cloud-max`` to locally installed Ollama models."""

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
    ) -> None:
        """Create a resolver.

        Args:
            host: URL of the Ollama server.
            overrides: Mapping from tier alias to fallback chain that
                replaces the default mapping for that alias.
        """
        self._client = OllamaClient(host=host)
        self._tiers = dict(self._DEFAULT_TIERS)
        if overrides:
            self._tiers.update(overrides)
        self._hints = dict(self._DEFAULT_HINTS)

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

    def list_available(self) -> list[str]:
        """Return names of all locally installed models."""
        raw = self._client.list()
        models = getattr(raw, "models", raw)
        return [str(getattr(m, "model", m)) for m in models]

    def _get_available(self) -> set[str]:
        """Return a set of available model names."""
        return set(self.list_available())

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
                info = self._client.get_model_info(name)
            except RuntimeError:
                continue
            size = self._extract_param_size(info.parameter_size)
            if size > largest_size:
                largest_size = size
                largest_name = name
        return largest_name

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
            info = self._client.get_model_info(name)
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
