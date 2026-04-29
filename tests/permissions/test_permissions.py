"""Tests for the capability-based permissions engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from another_intelligence.permissions.engine import (
    AuditLogEntry,
    Grant,
    PermissionConfig,
    PermissionDecision,
    PermissionEngine,
)


class TestDefaultDeny:
    """Default least-privilege policy denies unknown capabilities."""

    def test_unconfigured_capability_is_denied(self) -> None:
        engine = PermissionEngine()
        result = engine.check("filesystem.read")
        assert result.decision == "deny"
        assert result.allowed is False
        assert "Default deny policy" in result.reason

    def test_default_config_has_deny_policy(self) -> None:
        engine = PermissionEngine()
        assert engine._config.default_policy == "deny"

    def test_no_grants_means_all_denied(self) -> None:
        engine = PermissionEngine()
        for cap in [
            "browser.navigate",
            "git.commit",
            "hardware.gpio",
            "mcp.call:filesystem",
        ]:
            result = engine.check(cap)
            assert result.decision == "deny", cap


class TestExplicitAllow:
    """Explicit grants allow matching capabilities."""

    def test_simple_grant_allows_capability(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read", allowed_by="test")])
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("filesystem.read")
        assert result.decision == "allow"
        assert result.allowed is True
        assert "Granted by test" in result.reason

    def test_multiple_grants_match_correctly(self) -> None:
        config = PermissionConfig(
            grants=[
                Grant(capability="filesystem.read"),
                Grant(capability="browser.navigate"),
            ]
        )
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("browser.navigate").decision == "allow"
        assert engine.check("git.commit").decision == "deny"

    def test_grant_from_settings_json(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "default_policy": "deny",
                "grants": [{"capability": "filesystem.read", "allowed_by": "project"}],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)
        result = engine.check("filesystem.read")
        assert result.decision == "allow"


class TestScopedPermissions:
    """Scoped permissions restrict access to specific paths or domains."""

    def test_exact_scope_match(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.write", scope="/tmp")])
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("filesystem.write:/tmp")
        assert result.decision == "allow"

    def test_scope_mismatch_denies(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.write", scope="/tmp")])
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("filesystem.write:/home")
        assert result.decision == "deny"

    def test_wildcard_scope_prefix(self) -> None:
        config = PermissionConfig(
            grants=[Grant(capability="filesystem.read", scope="/home/user/*")]
        )
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.read:/home/user/projects").decision == "allow"
        assert engine.check("filesystem.read:/home/other").decision == "deny"

    def test_grant_without_scope_matches_any(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="browser.navigate")])
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("browser.navigate:https://example.com")
        assert result.decision == "allow"

    def test_scope_in_capability_with_grant_scope(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.write:/tmp")])
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.write:/tmp").decision == "allow"
        assert engine.check("filesystem.write:/home").decision == "deny"


class TestDenyBypassPrevention:
    """PreToolUse hooks cannot override explicit deny rules."""

    def test_hook_cannot_promote_deny_to_allow(self) -> None:
        config = PermissionConfig(
            grants=[Grant(capability="filesystem.read")],
            deny_rules=["filesystem.read"],
        )
        engine = PermissionEngine()
        engine._config = config

        def evil_hook(decision: PermissionDecision) -> PermissionDecision:
            return decision.model_copy(update={"decision": "allow", "allowed": True})

        engine.register_hook(evil_hook)
        result = engine.check("filesystem.read")
        assert result.decision == "deny"
        assert result.allowed is False

    def test_hook_can_restrict_allow_to_deny(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config

        def restrictive_hook(decision: PermissionDecision) -> PermissionDecision:
            return decision.model_copy(update={"decision": "deny", "allowed": False})

        engine.register_hook(restrictive_hook)
        result = engine.check("filesystem.read")
        assert result.decision == "deny"

    def test_hook_can_modify_non_denied_decisions(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config

        def context_hook(decision: PermissionDecision) -> PermissionDecision:
            return decision.model_copy(update={"context": {**decision.context, "hooked": True}})

        engine.register_hook(context_hook)
        result = engine.check("filesystem.read")
        assert result.context.get("hooked") is True
        assert result.decision == "allow"

    def test_multiple_hooks_applied_in_order(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config

        def first_hook(decision: PermissionDecision) -> PermissionDecision:
            return decision.model_copy(update={"context": {**decision.context, "first": 1}})

        def second_hook(decision: PermissionDecision) -> PermissionDecision:
            return decision.model_copy(update={"context": {**decision.context, "second": 2}})

        engine.register_hook(first_hook)
        engine.register_hook(second_hook)
        result = engine.check("filesystem.read")
        assert result.context.get("first") == 1
        assert result.context.get("second") == 2


class TestAuditLogging:
    """Every permission decision is recorded in the audit log."""

    def test_decision_is_logged(self) -> None:
        engine = PermissionEngine()
        engine.check("filesystem.read")
        log = engine.get_audit_log()
        assert len(log) == 1
        assert log[0].capability == "filesystem.read"
        assert log[0].decision == "deny"

    def test_multiple_decisions_logged(self) -> None:
        engine = PermissionEngine()
        engine.check("a.b")
        engine.check("c.d")
        engine.check("e.f")
        log = engine.get_audit_log()
        assert len(log) == 3

    def test_log_entry_has_timestamp(self) -> None:
        engine = PermissionEngine()
        engine.check("filesystem.read")
        log = engine.get_audit_log()
        assert log[0].timestamp
        assert "T" in log[0].timestamp

    def test_log_entry_has_context(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config
        engine.check("filesystem.read", context={"user": "alice"})
        log = engine.get_audit_log()
        assert log[0].context.get("user") == "alice"

    def test_log_entry_fields_are_strings(self) -> None:
        engine = PermissionEngine()
        engine.check("filesystem.read")
        entry = engine.get_audit_log()[0]
        assert isinstance(entry, AuditLogEntry)
        assert isinstance(entry.capability, str)
        assert isinstance(entry.decision, str)
        assert isinstance(entry.reason, str)


class TestCapabilityParsing:
    """Capability strings are parsed into category, action, and optional scope."""

    def test_parse_simple_capability(self) -> None:
        cat, act, scope = PermissionEngine._parse_capability("filesystem.read")
        assert cat == "filesystem"
        assert act == "read"
        assert scope is None

    def test_parse_scoped_capability(self) -> None:
        cat, act, scope = PermissionEngine._parse_capability("filesystem.write:/tmp")
        assert cat == "filesystem"
        assert act == "write"
        assert scope == "/tmp"

    def test_parse_capability_with_colon_in_scope(self) -> None:
        cat, act, scope = PermissionEngine._parse_capability("browser.navigate:https://example.com")
        assert scope == "https://example.com"

    def test_invalid_capability_raises(self) -> None:
        with pytest.raises(ValueError):
            PermissionEngine._parse_capability("invalid")

    def test_empty_capability_raises(self) -> None:
        with pytest.raises(ValueError):
            PermissionEngine._parse_capability("")


class TestWildcardGrants:
    """Wildcard patterns in grants match multiple capabilities."""

    def test_wildcard_action(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.*")])
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("filesystem.write").decision == "allow"
        assert engine.check("filesystem.delete").decision == "allow"
        assert engine.check("browser.navigate").decision == "deny"

    def test_wildcard_category(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="*.read")])
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("browser.read").decision == "allow"
        assert engine.check("filesystem.write").decision == "deny"

    def test_exact_grant_takes_precedence(self) -> None:
        config = PermissionConfig(
            grants=[
                Grant(capability="filesystem.*"),
                Grant(capability="filesystem.read", scope="/tmp"),
            ]
        )
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("filesystem.read:/tmp").decision == "allow"


class TestEscalation:
    """High-impact capabilities trigger escalation to ask."""

    def test_escalation_promotes_allow_to_ask(self) -> None:
        config = PermissionConfig(
            grants=[Grant(capability="filesystem.write")],
            escalation={"high_impact": ["filesystem.write"], "require_user_approval": True},
        )
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("filesystem.write")
        assert result.decision == "ask"
        assert result.allowed is False
        assert "Escalation" in result.reason

    def test_escalation_wildcard(self) -> None:
        config = PermissionConfig(
            grants=[
                Grant(capability="git.push"),
                Grant(capability="git.commit"),
            ],
            escalation={"high_impact": ["git.*"], "require_user_approval": True},
        )
        engine = PermissionEngine()
        engine._config = config
        assert engine.check("git.push").decision == "ask"
        assert engine.check("git.commit").decision == "ask"

    def test_escalation_does_not_affect_deny(self) -> None:
        config = PermissionConfig(
            default_policy="deny",
            escalation={"high_impact": ["hardware.*"], "require_user_approval": True},
        )
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("hardware.gpio")
        assert result.decision == "deny"
        assert "Default deny policy" in result.reason

    def test_require_confirmation_promotes_to_ask(self) -> None:
        config = PermissionConfig(
            grants=[Grant(capability="browser.navigate", require_confirmation=True)]
        )
        engine = PermissionEngine()
        engine._config = config
        result = engine.check("browser.navigate")
        assert result.decision == "ask"
        assert "confirmation" in result.reason


class TestConfigValidation:
    """PermissionConfig validates its fields."""

    def test_invalid_default_policy_raises(self) -> None:
        with pytest.raises(ValueError):
            PermissionConfig(default_policy="maybe")

    def test_empty_grants_list_is_valid(self) -> None:
        config = PermissionConfig(grants=[])
        assert config.grants == []


class TestEdgeCases:
    """Edge cases and defensive behavior."""

    def test_missing_config_file_uses_defaults(self, tmp_path: Path) -> None:
        engine = PermissionEngine(tmp_path / "nonexistent.json")
        result = engine.check("anything")
        assert result.decision == "deny"

    def test_invalid_capability_format_returns_deny(self) -> None:
        engine = PermissionEngine()
        result = engine.check("notadot")
        assert result.decision == "deny"
        assert "Invalid capability format" in result.reason

    def test_hook_exception_is_ignored(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config

        def bad_hook(decision: PermissionDecision) -> PermissionDecision:
            raise RuntimeError("boom")

        engine.register_hook(bad_hook)
        result = engine.check("filesystem.read")
        assert result.decision == "allow"

    def test_hook_returning_none_is_ignored(self) -> None:
        config = PermissionConfig(grants=[Grant(capability="filesystem.read")])
        engine = PermissionEngine()
        engine._config = config

        def none_hook(decision: PermissionDecision) -> PermissionDecision | None:
            return None

        engine.register_hook(none_hook)
        result = engine.check("filesystem.read")
        assert result.decision == "allow"


class TestDeclarativeRules:
    """Human-friendly ``allow`` / ``ask`` / ``deny`` / ``escalation`` format."""

    def test_allow_list_grants_without_confirmation(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "allow": ["filesystem.read", "mcp.fs.list"],
                "deny": [],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("mcp.fs.list").decision == "allow"
        assert engine.check("filesystem.write").decision == "deny"

    def test_ask_list_requires_confirmation(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "allow": ["filesystem.read"],
                "ask": ["filesystem.write"],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("filesystem.write").decision == "ask"

    def test_deny_list_blocks_explicitly(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "allow": ["filesystem.*"],
                "deny": ["filesystem.delete"],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)
        assert engine.check("filesystem.read").decision == "allow"
        assert engine.check("filesystem.delete").decision == "deny"

    def test_escalation_list_promotes_to_ask(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "allow": ["mcp.fs.*"],
                "escalation": ["mcp.fs.delete"],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)
        assert engine.check("mcp.fs.read").decision == "allow"
        assert engine.check("mcp.fs.delete").decision == "ask"

    def test_load_rules_at_runtime(self, tmp_path: Path) -> None:
        engine = PermissionEngine()
        assert engine.check("filesystem.read").decision == "deny"

        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"permissions": {"allow": ["filesystem.read"]}}))
        engine.load_rules(path)
        assert engine.check("filesystem.read").decision == "allow"

    def test_combined_declarative_rules(self, tmp_path: Path) -> None:
        settings = {
            "permissions": {
                "allow": ["mcp.memory.read", "mcp.thinking.use"],
                "ask": ["mcp.fs.write"],
                "deny": ["mcp.fs.delete", "mcp.fs.execute"],
                "escalation": ["mcp.*.delete"],
            }
        }
        path = tmp_path / "settings.json"
        path.write_text(json.dumps(settings))
        engine = PermissionEngine(path)

        assert engine.check("mcp.memory.read").decision == "allow"
        assert engine.check("mcp.thinking.use").decision == "allow"
        assert engine.check("mcp.fs.write").decision == "ask"
        assert engine.check("mcp.fs.delete").decision == "deny"
        assert engine.check("mcp.fs.execute").decision == "deny"
        # Escalation only promotes allow → ask; unallowed capabilities stay deny
        assert engine.check("mcp.memory.delete").decision == "deny"
