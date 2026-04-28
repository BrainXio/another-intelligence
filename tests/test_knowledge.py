"""Tests for the knowledge pipeline (compiler + query)."""

from pathlib import Path

from another_intelligence.knowledge.compiler import Article, KnowledgeCompiler
from another_intelligence.knowledge.query import KnowledgeQuery


class TestKnowledgeCompiler:
    """Daily log parsing and article compilation."""

    def test_compile_empty_source(self, tmp_path: Path):
        source = tmp_path / "daily"
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        result = compiler.compile()
        assert result["articles"] == 0
        assert result["files_parsed"] == 0

    def test_compile_single_file(self, tmp_path: Path):
        source = tmp_path / "daily"
        source.mkdir()
        md = source / "2026-04-18.md"
        md.write_text(
            "---\n"
            "date: 2026-04-18\n"
            "---\n"
            "\n"
            "## Concepts\n"
            "- [[concepts/ambiguous-command-resolution]] — Pattern for clarifying unclear user instructions\n"
            "\n"
            "## Mechanisms\n"
            "- [[mechanisms/eye-rendering-state-sync]] — Synchronize eye rendering with brain state changes\n"
        )
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        result = compiler.compile()
        assert result["articles"] == 2
        assert result["files_parsed"] == 1
        assert (output / "articles.jsonl").exists()

    def test_article_fields(self, tmp_path: Path):
        source = tmp_path / "daily"
        source.mkdir()
        md = source / "2026-04-18.md"
        md.write_text(
            "## Concepts\n"
            "- [[concepts/ambiguous-command-resolution]] — Pattern for clarifying unclear user instructions before action\n"
        )
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        compiler.compile()
        article = compiler._articles["ambiguous-command-resolution"]
        assert article.type == "concept"
        assert article.title == "Ambiguous Command Resolution"
        assert "clarifying unclear user instructions" in article.description
        assert str(md) in article.sources

    def test_deduplicate_across_files(self, tmp_path: Path):
        source = tmp_path / "daily"
        source.mkdir()
        (source / "2026-04-18.md").write_text(
            "## Concepts\n- [[concepts/ambiguous-command-resolution]] — First description\n"
        )
        (source / "2026-04-19.md").write_text(
            "## Concepts\n- [[concepts/ambiguous-command-resolution]] — Updated description\n"
        )
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        result = compiler.compile()
        assert result["articles"] == 1
        article = compiler._articles["ambiguous-command-resolution"]
        assert len(article.sources) == 2

    def test_section_type_mapping(self, tmp_path: Path):
        source = tmp_path / "daily"
        source.mkdir()
        (source / "2026-04-18.md").write_text(
            "## Concepts\n"
            "- [[concepts/foo]] — Foo desc\n"
            "## Mechanisms\n"
            "- [[mechanisms/bar]] — Bar desc\n"
            "## Outcomes\n"
            "- [[outcomes/baz]] — Baz desc\n"
            "## Connections\n"
            "- [[connections/qux]] — Qux desc\n"
        )
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        compiler.compile()
        assert compiler._articles["foo"].type == "concept"
        assert compiler._articles["bar"].type == "mechanism"
        assert compiler._articles["baz"].type == "outcome"
        assert compiler._articles["qux"].type == "connection"

    def test_fallback_plain_text_entry(self, tmp_path: Path):
        source = tmp_path / "daily"
        source.mkdir()
        (source / "2026-04-18.md").write_text(
            "## Concepts\nSome plain text entry without a wiki link\n"
        )
        output = tmp_path / "knowledge"
        compiler = KnowledgeCompiler(source_dir=source, output_dir=output)
        compiler.compile()
        # Should create an article from the plain text line
        assert len(compiler._articles) == 1
        article = next(iter(compiler._articles.values()))
        assert "plain text entry" in article.description.lower()


class TestKnowledgeQuery:
    """Search and retrieval from compiled knowledge base."""

    def test_search_empty_knowledge_dir(self, tmp_path: Path):
        kq = KnowledgeQuery(knowledge_dir=tmp_path / "knowledge")
        results = kq.search("foo")
        assert results == []

    def test_search_by_keyword(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo", description="Foo is great"),
                Article(id="bar", type="concept", title="Bar", description="Bar is nice"),
            ],
        )
        results = kq.search("foo")
        assert len(results) == 1
        assert results[0]["id"] == "foo"

    def test_search_no_match(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo", description="Foo is great"),
            ],
        )
        results = kq.search("zzzz")
        assert results == []

    def test_search_empty_query_returns_all(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo", description="Foo is great"),
                Article(id="bar", type="mechanism", title="Bar", description="Bar is nice"),
            ],
        )
        results = kq.search("")
        assert len(results) == 2

    def test_filter_by_type(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo"),
                Article(id="bar", type="mechanism", title="Bar"),
            ],
        )
        results = kq.search("", type="mechanism")
        assert len(results) == 1
        assert results[0]["id"] == "bar"

    def test_filter_by_tag(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo", tags=["security"]),
                Article(id="bar", type="concept", title="Bar", tags=["performance"]),
            ],
        )
        results = kq.search("", tag="security")
        assert len(results) == 1
        assert results[0]["id"] == "foo"

    def test_get_by_id(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path,
            [
                Article(id="foo", type="concept", title="Foo"),
            ],
        )
        article = kq.get("foo")
        assert article is not None
        assert article["id"] == "foo"

    def test_get_missing_returns_none(self, tmp_path: Path):
        kq = self._build_query(tmp_path, [])
        assert kq.get("missing") is None

    def test_limit(self, tmp_path: Path):
        kq = self._build_query(
            tmp_path, [Article(id=f"a{i}", type="concept", title=f"A{i}") for i in range(25)]
        )
        results = kq.search("")
        assert len(results) == 20

    @staticmethod
    def _build_query(tmp_path: Path, articles: list[Article]) -> KnowledgeQuery:
        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        articles_path = knowledge_dir / "articles.jsonl"
        with articles_path.open("w", encoding="utf-8") as fh:
            for article in articles:
                import json

                fh.write(json.dumps(article.to_dict()) + "\n")
        return KnowledgeQuery(knowledge_dir=knowledge_dir)
