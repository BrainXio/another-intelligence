"""Context window tracker for the DigitalBrain."""

from another_intelligence.events import ContextWindowChanged


class ContextWindow:
    """Tracks token utilization and emits change events."""

    def __init__(self, max_tokens: int = 8192) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        self._max_tokens = max_tokens
        self._total_tokens = 0
        self._messages: list[dict[str, str]] = []

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def utilization(self) -> float:
        return self._total_tokens / self._max_tokens

    def add_message(self, role: str, content: str, token_estimate: int = 0) -> ContextWindowChanged:
        """Add a message and return a change event."""
        self._messages.append({"role": role, "content": content})
        if token_estimate > 0:
            self._total_tokens += token_estimate
        else:
            self._total_tokens += len(content.split()) + 2
        return ContextWindowChanged(total_tokens=self._total_tokens, max_tokens=self._max_tokens)

    def reset(self) -> None:
        self._total_tokens = 0
        self._messages.clear()
