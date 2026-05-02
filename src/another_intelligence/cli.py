"""CLI entry point for Another-Intelligence.

Provides the ``ai`` command with sub-commands for brain decisions,
hooks, status, knowledge pipeline operations, and permissions.
"""

from __future__ import annotations

import json
import uuid
from collections import deque
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from another_intelligence.brain import DigitalBrain
from another_intelligence.events import (
    BrainEvent,
    SessionEnd,
    SessionStart,
)
from another_intelligence.knowledge.compiler import KnowledgeCompiler
from another_intelligence.knowledge.query import KnowledgeQuery
from another_intelligence.mcp.client import MCPRegistry
from another_intelligence.memory.pairs import PreferencePairExporter
from another_intelligence.permissions.engine import PermissionEngine
from another_intelligence.rpe.telemetry import TelemetryAnalyzer, TelemetryRecorder
from another_intelligence.state import ActivityPhase
from another_intelligence.strategist import Strategist


class BrainStore:
    """Persistent store for brain state and the append-only event log."""

    _STATE_FILE = "brain_state.json"
    _EVENT_LOG = "brain_activity.jsonl"

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path.home() / ".brainxio" / "state"
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)
        self._state_path = self._base / self._STATE_FILE
        self._event_path = self._base / self._EVENT_LOG

    def load_state(self) -> dict[str, Any]:
        """Load persisted brain state or return defaults."""
        if self._state_path.exists():
            with self._state_path.open("r", encoding="utf-8") as f:
                result: dict[str, Any] = json.load(f)
                return result
        return {
            "session_id": None,
            "memory": {},
            "context_messages": [],
            "current_phase": ActivityPhase.IDLE.value,
        }

    def save_state(self, state: dict[str, Any]) -> None:
        """Persist brain state atomically."""
        tmp = self._state_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp.replace(self._state_path)

    def append_event(self, event: BrainEvent) -> None:
        """Append a single event to the JSONL log."""
        record = event.model_dump(mode="json")
        record["_event_type"] = type(event).__name__
        with self._event_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def read_events(self, event_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Read events from the log, newest first, optionally filtered."""
        if not self._event_path.exists():
            return []
        recent_lines: deque[str] = deque(maxlen=limit)
        with self._event_path.open("r", encoding="utf-8") as f:
            for line in f:
                recent_lines.append(line)
        records: list[dict[str, Any]] = []
        for line in reversed(recent_lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event_type is None or rec.get("_event_type") == event_type:
                records.append(rec)
            if len(records) >= limit:
                break
        return records

    def clear(self) -> None:
        """Remove state and event log files."""
        if self._state_path.exists():
            self._state_path.unlink()
        if self._event_path.exists():
            self._event_path.unlink()


def _get_console() -> Console:
    return Console()


@click.group()
@click.version_option(version=click.style("0.1.0", fg="cyan"), prog_name="ai")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Another-Intelligence CLI -- neuroscience-grounded digital brain."""
    ctx.ensure_object(dict)
    if "store" not in ctx.obj:
        ctx.obj["store"] = BrainStore()


# ---------------------------------------------------------------------------
# ai brain
# ---------------------------------------------------------------------------


@main.group()
def brain() -> None:
    """Interact with the DigitalBrain PPAC loop."""


@brain.command(name="decide")
@click.argument("query")
@click.option(
    "--option",
    "-o",
    multiple=True,
    help="Candidate option (repeatable).",
)
@click.pass_context
def brain_decide(ctx: click.Context, query: str, option: tuple[str, ...]) -> None:
    """Run the PPAC decision loop for QUERY."""
    store: BrainStore = ctx.obj["store"]
    state = store.load_state()

    digital_brain = DigitalBrain(telemetry=TelemetryRecorder())
    # Hydrate memory from store
    for key, value in state.get("memory", {}).items():
        digital_brain.memory_index[key] = value

    options = list(option) if option else None
    result = digital_brain.decide(query, options=options)

    # Persist memory and events
    state["memory"] = digital_brain.memory
    state["current_phase"] = digital_brain.state.current.value
    store.save_state(state)
    for event in digital_brain.events:
        store.append_event(event)

    console = _get_console()
    console.print(
        Panel(
            f"[bold green]Chosen:[/bold green] {result['chosen_action']}\n"
            f"[dim]Options:[/dim] {', '.join(result['options'])}\n"
            f"[dim]Decision ID:[/dim] {result['decision_id']}",
            title="PPAC Decision",
            border_style="green",
        )
    )


@brain.command(name="regions")
@click.option("--limit", "-n", default=10, help="Number of events to show.")
@click.pass_context
def brain_regions(ctx: click.Context, limit: int) -> None:
    """Show recent BrainRegionActivated events."""
    store: BrainStore = ctx.obj["store"]
    events = store.read_events("BrainRegionActivated", limit=limit)
    console = _get_console()
    if not events:
        console.print("[dim]No region activations recorded yet.[/dim]")
        return

    table = Table(title="Recent Brain Region Activations")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Region", style="magenta")
    table.add_column("Metadata", style="green")

    for event in events:
        meta = event.get("metadata", {})
        meta_str = json.dumps(meta, indent=None)[:120]
        table.add_row(event.get("timestamp", "?"), event.get("region", "?"), meta_str)
    console.print(table)


# ---------------------------------------------------------------------------
# ai hook
# ---------------------------------------------------------------------------


@main.group()
def hook() -> None:
    """Emit lifecycle hooks."""


@hook.command(name="session-start")
@click.pass_context
def hook_session_start(ctx: click.Context) -> None:
    """Emit a SessionStart event and initialize session state."""
    store: BrainStore = ctx.obj["store"]
    session_id = str(uuid.uuid4())
    event = SessionStart(session_id=session_id)
    store.append_event(event)

    state = store.load_state()
    state["session_id"] = session_id
    state["current_phase"] = ActivityPhase.IDLE.value
    store.save_state(state)

    console = _get_console()
    console.print(f"[bold green]Session started:[/bold green] {session_id}")


@hook.command(name="session-end")
@click.option("--reason", default="normal", help="Reason for session end.")
@click.pass_context
def hook_session_end(ctx: click.Context, reason: str) -> None:
    """Emit a SessionEnd event and clear session state."""
    store: BrainStore = ctx.obj["store"]
    state = store.load_state()
    session_id = state.get("session_id")
    if session_id is None:
        ctx.fail("No active session.")

    event = SessionEnd(session_id=session_id, reason=reason)
    store.append_event(event)
    state["session_id"] = None
    state["current_phase"] = ActivityPhase.IDLE.value
    store.save_state(state)

    console = _get_console()
    console.print(f"[bold yellow]Session ended:[/bold yellow] {session_id} ({reason})")


# ---------------------------------------------------------------------------
# ai flush
# ---------------------------------------------------------------------------


@main.command()
@click.confirmation_option(prompt="Are you sure you want to clear all brain state and event logs?")
@click.pass_context
def flush(ctx: click.Context) -> None:
    """Clear persisted brain state and the event log."""
    store: BrainStore = ctx.obj["store"]
    store.clear()
    console = _get_console()
    console.print("[bold green]Brain state and event log cleared.[/bold green]")


# ---------------------------------------------------------------------------
# ai compile
# ---------------------------------------------------------------------------


@main.command(name="compile")
@click.option(
    "--source-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing daily markdown logs.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory to write compiled knowledge articles.",
)
@click.pass_context
def compile_(ctx: click.Context, source_dir: Path | None, output_dir: Path | None) -> None:
    """Parse daily logs and produce structured knowledge articles."""
    compiler = KnowledgeCompiler(
        source_dir=source_dir,
        output_dir=output_dir,
    )
    summary = compiler.compile()
    console = _get_console()
    console.print(
        f"[bold green]Compiled {summary['articles']} articles from {summary['files_parsed']} files.[/bold green]"
    )
    console.print(f"Output: {summary['output_dir']}")


# ---------------------------------------------------------------------------
# ai query
# ---------------------------------------------------------------------------


@main.command()
@click.argument("query", default="")
@click.option(
    "--type",
    "article_type",
    type=click.Choice(["concept", "mechanism", "outcome", "connection"]),
    help="Filter by article type.",
)
@click.option(
    "--tag",
    type=str,
    help="Filter by tag.",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of results.",
)
@click.option(
    "--knowledge-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing compiled knowledge articles.",
)
@click.pass_context
def query(
    ctx: click.Context,
    query: str,
    article_type: str | None,
    tag: str | None,
    limit: int,
    knowledge_dir: Path | None,
) -> None:
    """Search the compiled knowledge base."""
    kq = KnowledgeQuery(knowledge_dir=knowledge_dir)
    results = kq.search(query, type=article_type, tag=tag, limit=limit)
    console = _get_console()
    if not results:
        console.print("[dim]No results found.[/dim]")
        return
    for r in results:
        console.print(f"[{r['type']}] {r['title']} ({r['id']})")
        if r.get("description"):
            console.print(f"  {r['description']}")


# ---------------------------------------------------------------------------
# ai status
# ---------------------------------------------------------------------------


@main.command()
@click.option("--extended", is_flag=True, help="Show full event history and audit log.")
@click.pass_context
def status(ctx: click.Context, extended: bool) -> None:
    """Show current brain state, context usage, and recent activity."""
    store: BrainStore = ctx.obj["store"]
    state = store.load_state()
    console = _get_console()

    session_id = state.get("session_id")
    phase = state.get("current_phase", "idle")
    memory = state.get("memory", {})
    messages = state.get("context_messages", [])

    # Context estimation
    total_tokens = sum(len(m.get("content", "").split()) + 2 for m in messages)
    max_tokens = 8192
    util = total_tokens / max_tokens if max_tokens else 0.0

    panel_lines = [
        f"[bold]Session:[/bold]       {session_id or '[dim]none[/dim]'}",
        f"[bold]Phase:[/bold]         {phase}",
        f"[bold]Memory keys:[/bold]   {len(memory)}",
        f"[bold]Context:[/bold]       {total_tokens} / {max_tokens} tokens ({util:.1%})",
    ]
    console.print(Panel("\n".join(panel_lines), title="Brain Status", border_style="blue"))

    if memory:
        mem_table = Table(title="Memory Value Index")
        mem_table.add_column("Key", style="cyan")
        mem_table.add_column("Value", style="green")
        for key, value in memory.items():
            mem_table.add_row(key, f"{value:.3f}")
        console.print(mem_table)

    if extended:
        events = store.read_events(limit=20)
        if events:
            evt_table = Table(title="Recent Events")
            evt_table.add_column("Type", style="magenta")
            evt_table.add_column("Timestamp", style="cyan")
            evt_table.add_column("Payload", style="green")
            for event in events:
                payload = {k: v for k, v in event.items() if k not in ("_event_type", "timestamp")}
                payload_str = json.dumps(payload, indent=None)[:100]
                evt_table.add_row(
                    event.get("_event_type", "?"),
                    event.get("timestamp", "?"),
                    payload_str,
                )
            console.print(evt_table)
        else:
            console.print("[dim]No events in log.[/dim]")


# ---------------------------------------------------------------------------
# ai permissions
# ---------------------------------------------------------------------------


@main.group()
def permissions() -> None:
    """Inspect and test the permissions engine."""


@permissions.command(name="check")
@click.argument("capability")
@click.option("--config", type=click.Path(exists=True), help="Path to settings.json.")
@click.pass_context
def permissions_check(ctx: click.Context, capability: str, config: str | None) -> None:
    """Evaluate a capability against the current policy."""
    engine = PermissionEngine(config_path=config)
    decision = engine.check(capability)
    console = _get_console()
    color = (
        "green"
        if decision.decision == "allow"
        else "red"
        if decision.decision == "deny"
        else "yellow"
    )
    console.print(
        Panel(
            f"[bold]Capability:[/bold] {decision.capability}\n"
            f"[bold]Decision:[/bold]   [{color}]{decision.decision}[/{color}]\n"
            f"[bold]Reason:[/bold]     {decision.reason}",
            title="Permission Decision",
            border_style=color,
        )
    )


# ---------------------------------------------------------------------------
# ai rpe
# ---------------------------------------------------------------------------


@main.group()
def rpe() -> None:
    """Reward Prediction Error analysis and learning tools."""


@rpe.command(name="analyze")
@click.option(
    "--since",
    type=str,
    help="Earliest date to include (YYYY-MM-DD).",
)
@click.option(
    "--region",
    type=str,
    help="Filter decisions containing this option string.",
)
@click.option(
    "--telemetry-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("telemetry"),
    help="Directory containing telemetry JSONL files.",
)
@click.pass_context
def rpe_analyze(
    ctx: click.Context,
    since: str | None,
    region: str | None,
    telemetry_dir: Path,
) -> None:
    """Analyze telemetry logs and show RPE metrics."""
    recorder = TelemetryRecorder(directory=telemetry_dir)
    analyzer = TelemetryAnalyzer(recorder)
    results = analyzer.analyze(since=since, region=region)

    console = _get_console()

    if results["count"] == 0:
        console.print("[dim]No telemetry records found.[/dim]")
        return

    console.print(
        Panel(
            f"[bold]Records:[/bold]       {results['count']}\n"
            f"[bold]Mean RPE:[/bold]      {results['mean_rpe']}\n"
            f"[bold]Max |RPE|:[/bold]     {results['abs_max_rpe']}\n"
            f"[bold]Trend:[/bold]         {results['trend']}\n"
            f"[bold]Threshold suggestion:[/bold] {results['threshold_suggestion']}",
            title="RPE Analysis",
            border_style="cyan",
        )
    )

    top_events = cast("list[dict[str, object]]", results["top_events"])
    if top_events:
        table = Table(title="Top |RPE| Events")
        table.add_column("Decision ID", style="cyan")
        table.add_column("Query", style="white")
        table.add_column("Action", style="magenta")
        table.add_column("RPE", style="green")
        for evt in top_events:
            table.add_row(
                str(evt["decision_id"])[:8],
                str(evt["query"]),
                str(evt["chosen_action"]),
                str(evt["rpe"]),
            )
        console.print(table)

    # Learning insights
    mean_rpe = float(str(results["mean_rpe"]))
    if mean_rpe > 0.05:
        console.print("[green]System is consistently overperforming expectations.[/green]")
    elif mean_rpe < -0.05:
        console.print("[yellow]System is consistently underperforming expectations.[/yellow]")
    else:
        console.print("[dim]RPE is well-calibrated (near zero).[/dim]")


@rpe.command(name="export-pairs")
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("memory/qlora-pairs"),
    help="Directory for exported preference pairs.",
)
@click.option(
    "--min-abs-rpe",
    type=float,
    default=0.1,
    help="Minimum absolute RPE to include a pair (default: 0.1).",
)
@click.option(
    "--since",
    type=str,
    help="Earliest date to include (YYYY-MM-DD).",
)
@click.option(
    "--telemetry-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("telemetry"),
    help="Directory containing telemetry JSONL files.",
)
@click.option(
    "--limit",
    type=int,
    default=10_000,
    help="Maximum number of pairs to export.",
)
@click.pass_context
def rpe_export_pairs(
    ctx: click.Context,
    output_dir: Path,
    min_abs_rpe: float,
    since: str | None,
    telemetry_dir: Path,
    limit: int,
) -> None:
    """Export QLoRA-compatible preference pairs from telemetry."""
    recorder = TelemetryRecorder(directory=telemetry_dir)
    exporter = PreferencePairExporter(recorder)
    result = exporter.export(
        output_dir=output_dir,
        min_abs_rpe=min_abs_rpe,
        since=since,
        limit=limit,
    )

    console = _get_console()
    console.print(
        Panel(
            f"[bold]Exported:[/bold]  {result['exported']}\n"
            f"[bold]Skipped:[/bold]   {result['skipped']}\n"
            f"[bold]Output:[/bold]    {result['output_dir']}",
            title="Preference Pair Export",
            border_style="green",
        )
    )


@rpe.command(name="record")
@click.option(
    "--outcome",
    "-o",
    type=float,
    required=True,
    help="Actual outcome value (0.0–1.0).",
)
@click.option(
    "--decision-id",
    "-d",
    type=str,
    help="Decision ID to attach the outcome to.",
)
@click.option(
    "--expected",
    "-e",
    type=float,
    default=0.5,
    help="Expected value at decision time (default: 0.5).",
)
@click.option(
    "--context",
    "-c",
    type=str,
    help="Free-text description of what happened.",
)
@click.option(
    "--telemetry-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("telemetry"),
    help="Directory containing telemetry JSONL files.",
)
@click.pass_context
def rpe_record(
    ctx: click.Context,
    outcome: float,
    decision_id: str | None,
    expected: float,
    context: str | None,
    telemetry_dir: Path,
) -> None:
    """Record an external outcome to close the RPE learning loop."""
    if decision_id is None:
        decision_id = str(uuid.uuid4())

    metadata: dict[str, Any] = {}
    if context is not None:
        metadata["context"] = context

    recorder = TelemetryRecorder(directory=telemetry_dir)
    brain = DigitalBrain(telemetry=recorder)
    brain.record_outcome(
        decision_id=decision_id,
        expected=expected,
        actual=outcome,
        metadata=metadata if metadata else None,
    )

    console = _get_console()
    rpe_value = outcome - expected
    color = "green" if rpe_value > 0 else "red" if rpe_value < 0 else "white"
    console.print(
        Panel(
            f"[bold]Decision ID:[/bold] {decision_id}\n"
            f"[bold]Expected:[/bold]    {expected}\n"
            f"[bold]Actual:[/bold]      {outcome}\n"
            f"[bold]RPE:[/bold]         [{color}]{rpe_value:+.4f}[/{color}]",
            title="Outcome Recorded",
            border_style=color,
        )
    )


@rpe.command(name="ingest")
@click.argument("shortlist", type=click.File("r"), default="-", required=False)
@click.option(
    "--top-n",
    type=int,
    default=5,
    help="Number of top candidates to return (default: 5).",
)
@click.option(
    "--base-value",
    type=float,
    default=0.5,
    help="Baseline expected value for unevaluated options.",
)
@click.option(
    "--from-mcp",
    is_flag=True,
    help="Query ASD scanner via MCP instead of reading a file.",
)
@click.option(
    "--scan-dir",
    type=str,
    default=None,
    help="Directory for ASD scanner to scan (only with --from-mcp).",
)
@click.option(
    "--post-to-bus",
    is_flag=True,
    help="Post the ranked result to the ADHD bus.",
)
@click.pass_context
def rpe_ingest(
    ctx: click.Context,
    shortlist: TextIOWrapper | None,
    top_n: int,
    base_value: float,
    from_mcp: bool,
    scan_dir: str | None,
    post_to_bus: bool,
) -> None:
    """Rank a prototype shortlist by expected value.

    Reads from SHORTLIST JSON file (or stdin with '-') containing an array of
    objects, each with at least 'name' and 'description' keys.

    With --from-mcp, queries the ASD scanner via MCP instead of reading a file.
    """
    store: BrainStore = ctx.obj["store"]
    state = store.load_state()
    memory: dict[str, Any] = state.get("memory", {})
    memory_float: dict[str, float] = {k: float(v) for k, v in memory.items()}

    if from_mcp:
        console = _get_console()
        console.print("[dim]Querying ASD scanner via MCP...[/dim]")

        from another_intelligence.brain import DigitalBrain
        from another_intelligence.mcp.client import MCPClient, MCPRegistry
        from another_intelligence.permissions.engine import PermissionEngine

        registry = MCPRegistry()
        engine = PermissionEngine()
        mcp_client = MCPClient(registry, engine)

        brain = DigitalBrain(telemetry=TelemetryRecorder())
        for key, value in memory_float.items():
            brain.memory_index[key] = value

        async def _run() -> dict[str, Any]:
            result = await brain.ingest_prototypes_from_mcp(
                mcp_client, top_n=top_n, scan_dir=scan_dir
            )
            await mcp_client.disconnect_all()
            return result

        import asyncio as _asyncio

        result = _asyncio.run(_run())

        if not result.get("success"):
            ctx.fail(f"MCP ingestion failed: {result.get('error', 'Unknown error')}")

        ranked = result["ranked"]
    else:
        if shortlist is None:
            ctx.fail("SHORTLIST argument is required when not using --from-mcp")
        try:
            data = json.loads(shortlist.read())
        except json.JSONDecodeError as exc:
            ctx.fail(f"Invalid JSON: {exc}")

        if not isinstance(data, list):
            ctx.fail("Shortlist must be a JSON array of objects.")

        strategist = Strategist(base_value=base_value)
        ranked = strategist.ingest_prototypes(
            shortlist=data,
            memory=memory_float,
            top_n=top_n,
        )

    console = _get_console()
    table = Table(title="Top Prototype Candidates")
    table.add_column("Rank", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Expected Value", style="green")
    table.add_column("Rationale", style="white")

    for i, item in enumerate(ranked, 1):
        table.add_row(
            str(i),
            str(item["name"]),
            f"{item['expected_value']:.4f}",
            str(item["rationale"]),
        )
    console.print(table)

    if post_to_bus:
        import subprocess as _sp

        bus_msg = json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "type": "dependency",
                "topic": "prototype-ingestion",
                "payload": {
                    "source": "ai-cognitive-core",
                    "ranked": [
                        {
                            "name": item["name"],
                            "expected_value": item["expected_value"],
                            "rationale": item["rationale"],
                            "dependencies": item.get("dependencies", []),
                        }
                        for item in ranked
                    ],
                },
            }
        )
        _sp.run(
            [
                "uv",
                "run",
                "adhd",
                "post",
                "--type",
                "dependency",
                "--topic",
                "prototype-ingestion",
                "--payload",
                bus_msg,
            ],
            check=False,
        )
        console.print(
            Panel(
                f"Top-{len(ranked)} candidates posted to ADHD bus.",
                title="Bus Post",
                border_style="green",
            )
        )


# ---------------------------------------------------------------------------
# ai mcp
# ---------------------------------------------------------------------------


@main.group()
def mcp() -> None:
    """Inspect and manage MCP server connections."""


@mcp.command(name="status")
@click.option("--extended", is_flag=True, help="Show detailed health information.")
@click.pass_context
def mcp_status(ctx: click.Context, extended: bool) -> None:
    """Show MCP server connection status and tool availability."""
    registry = MCPRegistry()
    console = _get_console()

    servers = registry.list_servers()
    if not servers:
        server_names: list[str] = []
        for path in (Path(".mcp.json"), Path.home() / ".brainxio" / "mcp.json"):
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                for srv in raw.get("servers", raw.get("mcpServers", [])):
                    if isinstance(srv, dict):
                        server_names.append(srv.get("name", "?"))
        if not server_names:
            console.print("[dim]No MCP servers configured.[/dim]")
            return
    else:
        server_names = servers

    table = Table(title="MCP Server Status")
    table.add_column("Server", style="cyan")
    table.add_column("Configured", style="green")
    table.add_column("Transport", style="magenta")
    table.add_column("Command", style="white")

    for name in server_names:
        config = registry.get(name)
        if config is not None:
            table.add_row(
                name,
                "[green]yes[/green]",
                config.type,
                config.command,
            )
        else:
            table.add_row(name, "[dim]unknown[/dim]", "?", "?")
    console.print(table)

    if extended and servers:
        import asyncio as _asyncio

        from another_intelligence.mcp.client import MCPClient
        from another_intelligence.permissions.engine import PermissionEngine

        engine = PermissionEngine()
        client = MCPClient(registry, engine)

        async def _probe() -> dict[str, Any]:
            await client.connect_all()
            health = await client.health_check()
            await client.disconnect_all()
            return health

        console.print("[dim]Running health checks...[/dim]")
        try:
            health = _asyncio.run(_probe())
        except Exception as exc:
            console.print(f"[red]Health check failed: {exc}[/red]")
            return

        health_table = Table(title="Extended Health Status")
        health_table.add_column("Server", style="cyan")
        health_table.add_column("Connected", style="green")
        health_table.add_column("Healthy", style="green")
        health_table.add_column("Tools", style="magenta")
        health_table.add_column("Version", style="white")
        health_table.add_column("Error", style="red")

        for name, h in sorted(health.items()):
            health_table.add_row(
                name,
                "[green]yes[/green]" if h.connected else "[red]no[/red]",
                "[green]yes[/green]" if h.healthy else "[red]no[/red]",
                str(h.tool_count) if h.healthy else "-",
                h.version or "?",
                h.error or "-",
            )
        console.print(health_table)


if __name__ == "__main__":
    main()
