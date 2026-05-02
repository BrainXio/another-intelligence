"""Knowledge compiler — daily logs → structured articles."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from another_intelligence.paths import DAILY_LOGS_DIR, KNOWLEDGE_DIR


class Article:
    """A compiled knowledge article."""

    def __init__(
        self,
        *,
        id: str,
        type: str,
        title: str,
        description: str = "",
        sources: list[str] | None = None,
        first_seen: str | None = None,
        last_updated: str | None = None,
        tags: list[str] | None = None,
        content: str = "",
    ) -> None:
        self.id = id
        self.type = type
        self.title = title
        self.description = description
        self.sources = sources or []
        self.first_seen = first_seen or datetime.now(UTC).isoformat()
        self.last_updated = last_updated or datetime.now(UTC).isoformat()
        self.tags = tags or []
        self.content = content

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "sources": self.sources,
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
            "tags": self.tags,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Article:
        return cls(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            description=data.get("description", ""),
            sources=data.get("sources"),
            first_seen=data.get("first_seen"),
            last_updated=data.get("last_updated"),
            tags=data.get("tags"),
            content=data.get("content", ""),
        )


class KnowledgeCompiler:
    """Parse daily markdown logs and produce structured articles.

    Articles are categorized by type: concept, mechanism, outcome, connection.
    Output is written as JSONL to ``articles.jsonl`` in the target directory.
    """

    _SECTION_MAP: dict[str, str] = {
        "concepts": "concept",
        "concept": "concept",
        "mechanisms": "mechanism",
        "mechanism": "mechanism",
        "outcomes": "outcome",
        "outcome": "outcome",
        "connections": "connection",
        "connection": "connection",
    }

    def __init__(
        self,
        source_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> None:
        self.source_dir = Path(source_dir or self._default_source_dir())
        self.output_dir = Path(output_dir or self._default_output_dir())
        self._articles: dict[str, Article] = {}

    @staticmethod
    def _default_source_dir() -> Path:
        return DAILY_LOGS_DIR

    @staticmethod
    def _default_output_dir() -> Path:
        return KNOWLEDGE_DIR

    def compile(self) -> dict[str, Any]:
        """Run the full compile pipeline.

        Returns a summary dict with counts and output path.
        """
        self._articles.clear()
        self._load_existing()

        files = sorted(self.source_dir.glob("*.md"))
        for path in files:
            self._parse_file(path)

        self._write_articles()
        return {
            "articles": len(self._articles),
            "files_parsed": len(files),
            "output_dir": str(self.output_dir),
        }

    def _load_existing(self) -> None:
        articles_path = self.output_dir / "articles.jsonl"
        if not articles_path.exists():
            return
        with articles_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    article = Article.from_dict(data)
                    self._articles[article.id] = article
                except (json.JSONDecodeError, KeyError):
                    continue

    def _parse_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        frontmatter = self._extract_frontmatter(text)
        file_date = frontmatter.get("date", path.stem)
        if isinstance(file_date, datetime):
            file_date = file_date.date().isoformat()

        sections = self._extract_sections(text)
        for header, lines in sections.items():
            article_type = self._SECTION_MAP.get(header.lower(), "concept")
            for line in lines:
                self._parse_line(line, article_type, str(path), file_date)

    def _extract_frontmatter(self, text: str) -> dict[str, Any]:
        """Parse YAML frontmatter if present."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not match:
            return {}
        raw = match.group(1)
        data: dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
        return data

    def _extract_sections(self, text: str) -> dict[str, list[str]]:
        """Split markdown body into sections by ``##`` headers."""
        # Remove frontmatter
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)
        sections: dict[str, list[str]] = defaultdict(list)
        current_header = ""
        for line in body.splitlines():
            header_match = re.match(r"^##\s+(.+)$", line)
            if header_match:
                current_header = header_match.group(1).strip().lower()
                continue
            if line.strip():
                sections[current_header].append(line.strip())
        return sections

    def _parse_line(self, line: str, article_type: str, source: str, date: str) -> None:
        """Parse a single bullet line for wiki-style links or plain text entries."""
        wiki_match = re.search(r"\[\[(?P<type>[a-z]+)\s*/\s*(?P<slug>[^\]]+)\]\]", line)
        if wiki_match:
            slug = wiki_match.group("slug").strip()
            description = self._extract_description(line)
        else:
            # Fallback: use first words as slug
            slug = re.sub(r"[^\w\s-]", "", line).strip().lower().replace(" ", "-")[:64]
            if not slug:
                return
            description = line.lstrip("- *").strip()

        if slug in self._articles:
            article = self._articles[slug]
            if source not in article.sources:
                article.sources.append(source)
            article.last_updated = date
            if description and not article.description:
                article.description = description
        else:
            self._articles[slug] = Article(
                id=slug,
                type=article_type,
                title=slug.replace("-", " ").title(),
                description=description,
                sources=[source],
                first_seen=date,
                last_updated=date,
            )

    def _extract_description(self, line: str) -> str:
        """Extract description after the wiki link or dash."""
        # Remove wiki link
        cleaned = re.sub(r"\[\[[^\]]+\]\]", "", line).strip()
        # Remove leading bullet markers
        cleaned = re.sub(r"^[\s]*[-*][\s]*", "", cleaned).strip()
        # Remove leading em-dash or en-dash
        cleaned = re.sub(r"^[–—\-]+\s*", "", cleaned).strip()
        return cleaned

    def _write_articles(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        articles_path = self.output_dir / "articles.jsonl"
        with articles_path.open("w", encoding="utf-8") as fh:
            for article in self._articles.values():
                fh.write(json.dumps(article.to_dict(), ensure_ascii=False) + "\n")
