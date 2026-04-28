"""CLI entry point for Another-Intelligence."""

from pathlib import Path

import click

from another_intelligence.knowledge.compiler import KnowledgeCompiler
from another_intelligence.knowledge.query import KnowledgeQuery


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Another-Intelligence — A persistent neuroscience-grounded digital brain."""


@main.command()
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
def compile(source_dir: Path | None, output_dir: Path | None) -> None:
    """Parse daily logs and produce structured knowledge articles."""
    compiler = KnowledgeCompiler(
        source_dir=source_dir,
        output_dir=output_dir,
    )
    summary = compiler.compile()
    click.echo(f"Compiled {summary['articles']} articles from {summary['files_parsed']} files.")
    click.echo(f"Output: {summary['output_dir']}")


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
def query(
    query: str,
    article_type: str | None,
    tag: str | None,
    limit: int,
    knowledge_dir: Path | None,
) -> None:
    """Search the compiled knowledge base."""
    kq = KnowledgeQuery(knowledge_dir=knowledge_dir)
    results = kq.search(query, type=article_type, tag=tag, limit=limit)
    if not results:
        click.echo("No results found.")
        return
    for r in results:
        click.echo(f"[{r['type']}] {r['title']} ({r['id']})")
        if r.get("description"):
            click.echo(f"  {r['description']}")


if __name__ == "__main__":
    main()
