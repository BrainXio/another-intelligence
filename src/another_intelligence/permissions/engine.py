"""Capability-based permissions engine for Another-Intelligence."""

from __future__ import annotations

import fnmatch
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Grant(BaseModel):
    """A single permission grant."""

    capability: str
    scope: str | None = None
    allowed_by: str = "project"
    require_confirmation: bool = False


class Escalation(BaseModel):
    """Escalation rules for high-impact capabilities."""

    high_impact: list[str] = Field(default_factory=list)
    require_user_approval: bool = True


class PermissionConfig(BaseModel):
    """Root permissions configuration loaded from settings.json."""

    default_policy: str = "deny"
    grants: list[Grant] = Field(default_factory=list)
    deny_rules: list[str] = Field(default_factory=list)
    escalation: Escalation = Field(default_factory=Escalation)

    @field_validator("default_policy")
    @classmethod
    def _validate_policy(cls, value: str) -> str:
        if value not in {"deny", "allow"}:
            raise ValueError("default_policy must be 'deny' or 'allow'")
        return value


class PermissionDecision(BaseModel):
    """Result of a permission check."""

    capability: str
    allowed: bool
    decision: str
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("decision")
    @classmethod
    def _validate_decision(cls, value: str) -> str:
        if value not in {"allow", "deny", "ask"}:
            raise ValueError("decision must be 'allow', 'deny', or 'ask'")
        return value


class AuditLogEntry(BaseModel):
    """A single audit log entry for a permission decision."""

    timestamp: str
    capability: str
    decision: str
    reason: str
    context: dict[str, Any]


class PermissionEngine:
    """Capability-based permissions engine with audit logging."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize the engine with optional config path.

        Args:
            config_path: Path to a JSON settings file. If None, uses default
                least-privilege config.
        """
        self._hooks: list[Callable[[PermissionDecision], PermissionDecision]] = []
        self._audit_log: list[AuditLogEntry] = []
        self._audit_log_path = Path.home() / ".brainxio" / "state" / "permission_audit.jsonl"
        self._config = self._load_config(config_path)

    def _load_config(self, config_path: Path | str | None) -> PermissionConfig:
        if config_path is None:
            return PermissionConfig()
        path = Path(config_path)
        if not path.exists():
            return PermissionConfig()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        permissions = data.get("permissions", {})
        return self._normalize_declarative_rules(permissions)

    @staticmethod
    def _normalize_declarative_rules(raw: dict[str, Any]) -> PermissionConfig:
        """Support both internal format and human-friendly declarative format.

        Declarative format::

            {
                "allow": ["mcp.fs.read", "mcp.memory.*"],
                "ask": ["mcp.fs.write"],
                "deny": ["mcp.fs.delete"],
                "escalation": ["mcp.*.delete"]
            }

        Internal format (pass-through)::

            {
                "default_policy": "deny",
                "grants": [...],
                "deny_rules": [...],
                "escalation": {...}
            }
        """
        # Detect declarative format by presence of allow/ask/deny keys
        if any(k in raw for k in ("allow", "ask", "deny")):
            grants: list[Grant] = []
            for cap in raw.get("allow", []):
                grants.append(Grant(capability=cap, require_confirmation=False))
            for cap in raw.get("ask", []):
                grants.append(Grant(capability=cap, require_confirmation=True))
            return PermissionConfig(
                default_policy="deny",
                grants=grants,
                deny_rules=raw.get("deny", []),
                escalation=Escalation(
                    high_impact=raw.get("escalation", []),
                    require_user_approval=True,
                ),
            )
        return PermissionConfig(**raw)

    def load_rules(self, path: Path | str) -> None:
        """Reload rules from a declarative settings.json file at runtime."""
        self._config = self._load_config(path)

    @staticmethod
    def _parse_capability(capability: str) -> tuple[str, str, str | None]:
        """Parse a capability string into (category, action, scope).

        Args:
            capability: Capability in the format ``category.action[:scope]``.

        Returns:
            Tuple of (category, action, scope_or_none).

        Raises:
            ValueError: If the capability format is invalid.
        """
        if ":" in capability:
            main, scope = capability.split(":", 1)
        else:
            main = capability
            scope = None
        if "." not in main:
            raise ValueError(f"Invalid capability format: {capability}")
        category, action = main.split(".", 1)
        return category, action, scope

    def _match_grant(self, category: str, action: str, scope: str | None) -> Grant | None:
        """Find the first matching grant for the given capability parts."""
        for grant in self._config.grants:
            try:
                g_cat, g_act, g_scope = self._parse_capability(grant.capability)
            except ValueError:
                continue
            if not self._match_pattern(category, g_cat):
                continue
            if not self._match_pattern(action, g_act):
                continue
            effective_scope = g_scope if g_scope is not None else grant.scope
            if (
                scope is not None
                and effective_scope is not None
                and not self._scope_matches(scope, effective_scope)
            ):
                continue
            return grant
        return None

    @staticmethod
    def _match_pattern(value: str, pattern: str) -> bool:
        """Check if a value matches a pattern, supporting wildcards."""
        return fnmatch.fnmatch(value, pattern)

    @staticmethod
    def _scope_matches(requested: str, granted: str) -> bool:
        """Check if the requested scope is covered by the granted scope."""
        if granted.endswith("*"):
            prefix = granted[:-1]
            return requested.startswith(prefix)
        return requested == granted

    def _is_denied(self, category: str, action: str, scope: str | None) -> bool:
        """Check if there is an explicit deny rule matching the capability."""
        for rule in self._config.deny_rules:
            try:
                r_cat, r_act, r_scope = self._parse_capability(rule)
            except ValueError:
                continue
            if not self._match_pattern(category, r_cat):
                continue
            if not self._match_pattern(action, r_act):
                continue
            if (
                r_scope is not None
                and scope is not None
                and not self._scope_matches(scope, r_scope)
            ):
                continue
            return True
        return False

    def _is_escalation_required(self, category: str, action: str) -> bool:
        """Check if the capability matches any escalation rule."""
        for pattern in self._config.escalation.high_impact:
            try:
                p_cat, p_act, _ = self._parse_capability(pattern)
            except ValueError:
                continue
            if self._match_pattern(category, p_cat) and self._match_pattern(action, p_act):
                return True
        return False

    def register_hook(self, hook: Callable[[PermissionDecision], PermissionDecision]) -> None:
        """Register a PreToolUse hook that can influence decisions.

        Hooks receive the current decision and may return a modified one.
        Explicit deny decisions cannot be overridden to allow.
        """
        self._hooks.append(hook)

    def _apply_hooks(self, decision: PermissionDecision) -> PermissionDecision:
        """Apply all registered hooks to a decision."""
        current = decision
        for hook in self._hooks:
            try:
                result = hook(current)
            except (RuntimeError, TypeError, ValueError):
                continue
            if result is None:
                continue
            # Hooks cannot promote an explicit deny to allow
            if decision.decision == "deny" and result.decision == "allow":
                continue
            current = result
        return current

    def _log_decision(self, decision: PermissionDecision) -> None:
        """Record a decision in the audit log (in-memory and on disk)."""
        entry = AuditLogEntry(
            timestamp=datetime.now(UTC).isoformat(),
            capability=decision.capability,
            decision=decision.decision,
            reason=decision.reason,
            context=decision.context,
        )
        self._audit_log.append(entry)
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_log_path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def check(self, capability: str, context: dict[str, Any] | None = None) -> PermissionDecision:
        """Evaluate a capability request against the policy.

        Args:
            capability: The capability string in ``category.action[:scope]`` format.
            context: Optional additional context for the decision.

        Returns:
            A ``PermissionDecision`` with the outcome.
        """
        ctx = context or {}
        try:
            category, action, scope = self._parse_capability(capability)
        except ValueError as exc:
            decision = PermissionDecision(
                capability=capability,
                allowed=False,
                decision="deny",
                reason=f"Invalid capability format: {exc}",
                context=ctx,
            )
            self._log_decision(decision)
            return decision

        # Explicit deny rules are checked first and are absolute
        if self._is_denied(category, action, scope):
            decision = PermissionDecision(
                capability=capability,
                allowed=False,
                decision="deny",
                reason="Explicit deny rule matched",
                context=ctx,
            )
            self._log_decision(decision)
            return decision

        # Look for a matching grant
        grant = self._match_grant(category, action, scope)

        if grant is not None:
            if grant.require_confirmation:
                decision = PermissionDecision(
                    capability=capability,
                    allowed=False,
                    decision="ask",
                    reason="Grant requires confirmation",
                    context={"grant": grant.model_dump(), **ctx},
                )
            else:
                decision = PermissionDecision(
                    capability=capability,
                    allowed=True,
                    decision="allow",
                    reason=f"Granted by {grant.allowed_by}",
                    context={"grant": grant.model_dump(), **ctx},
                )
        elif self._config.default_policy == "deny":
            decision = PermissionDecision(
                capability=capability,
                allowed=False,
                decision="deny",
                reason="Default deny policy",
                context=ctx,
            )
        else:
            decision = PermissionDecision(
                capability=capability,
                allowed=True,
                decision="allow",
                reason="Default allow policy",
                context=ctx,
            )

        # Escalation rules can promote allow -> ask but not deny -> anything
        if decision.decision == "allow" and self._is_escalation_required(category, action):
            decision = PermissionDecision(
                capability=capability,
                allowed=False,
                decision="ask",
                reason="Escalation rule matched",
                context=decision.context,
            )

        # Apply PreToolUse hooks
        decision = self._apply_hooks(decision)

        self._log_decision(decision)
        return decision

    def get_audit_log(self) -> list[AuditLogEntry]:
        """Return a copy of the audit log."""
        return list(self._audit_log)
