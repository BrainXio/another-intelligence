"""Hook runner for executing registered hooks with permissions and logging."""

from __future__ import annotations

import asyncio
import importlib
import json
import time
from collections.abc import Callable
from typing import Any

from another_intelligence.events import BrainEvent
from another_intelligence.hooks.models import HookConfig, HookResult, HookType
from another_intelligence.hooks.registry import HookRegistry


class HookRunner:
    """Executes hooks from a registry, optionally gating via a permissions engine.

    Supports shell, Python callable, and MCP tool hooks. Every execution is
    timed and logged in a ``HookResult``.
    """

    def __init__(
        self,
        registry: HookRegistry,
        permission_engine: Any | None = None,
    ) -> None:
        self._registry = registry
        self._permission_engine = permission_engine
        self._log: list[HookResult] = []
        self._python_cache: dict[str, Callable[..., Any]] = {}

    @property
    def log(self) -> list[HookResult]:
        """Return a copy of the execution log."""
        return list(self._log)

    def clear_log(self) -> None:
        """Clear the execution log."""
        self._log.clear()

    async def run_hooks(self, event: BrainEvent) -> list[HookResult]:
        """Execute all hooks registered for the event's type.

        Hooks run sequentially in registration order. If a hook is marked
        ``critical`` and raises an exception, the error is re-raised after
        logging. Non-critical errors are swallowed and logged.
        """
        event_type = type(event).__name__
        configs = self._registry.get_hooks(event_type)
        results: list[HookResult] = []
        for config in configs:
            result = await self._run_single(event, config)
            results.append(result)
            if not result.success and config.critical:
                raise RuntimeError(f"Critical hook failed for {event_type}: {result.error}")
        return results

    async def _run_single(self, event: BrainEvent, config: HookConfig) -> HookResult:
        start = time.perf_counter()

        # Permission check
        if self._permission_engine is not None:
            try:
                decision = self._permission_engine.check(f"hook.execute.{config.event_type}")
                if not decision.allowed:
                    duration_ms = (time.perf_counter() - start) * 1000
                    return HookResult(
                        success=False,
                        error=f"Permission denied: {decision.reason}",
                        duration_ms=duration_ms,
                        config=config,
                    )
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                return HookResult(
                    success=False,
                    error=f"Permission check error: {exc}",
                    duration_ms=duration_ms,
                    config=config,
                )

        try:
            if config.type == HookType.SHELL:
                output = await self._run_shell(event, config)
            elif config.type == HookType.PYTHON:
                output = await self._run_python(event, config)
            elif config.type == HookType.MCP:
                output = await self._run_mcp(event, config)
            else:
                raise ValueError(f"Unsupported hook type: {config.type}")

            duration_ms = (time.perf_counter() - start) * 1000
            result = HookResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                config=config,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            result = HookResult(
                success=False,
                error=str(exc),
                duration_ms=duration_ms,
                config=config,
            )

        self._log.append(result)
        return result

    async def _run_shell(self, event: BrainEvent, config: HookConfig) -> Any:
        assert config.command is not None
        payload = event.model_dump_json()
        proc = await asyncio.create_subprocess_shell(
            config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(payload.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(
                f"Shell hook exited {proc.returncode}: {stderr.decode('utf-8').strip()}"
            )
        text = stdout.decode("utf-8").strip()
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    async def _run_python(self, event: BrainEvent, config: HookConfig) -> Any:
        assert config.entry_point is not None
        if config.entry_point not in self._python_cache:
            module_path, callable_name = config.entry_point.rsplit(".", 1)
            module = importlib.import_module(module_path)
            self._python_cache[config.entry_point] = getattr(module, callable_name)
        fn = self._python_cache[config.entry_point]
        if asyncio.iscoroutinefunction(fn):
            return await fn(event)
        return fn(event)

    async def _run_mcp(self, event: BrainEvent, config: HookConfig) -> Any:
        assert config.server is not None
        assert config.tool is not None
        raise NotImplementedError("MCP hooks require the MCP client (section 4.6)")
