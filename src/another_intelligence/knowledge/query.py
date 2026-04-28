"""Knowledge query — search compiled articles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from another_intelligence.knowledge.compiler import Article


class KnowledgeQuery:
    """Search the compiled knowledge base by keyword, type, or tag."""

    def __init__(self, knowledge_dir: Path | str | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir or self._default_knowledge_dir())
        self._articles: list[Article] = []

    @staticmethod
    def _default_knowledge_dir() -> Path:
        return Path.home() / ".brainxio" / "knowledge"

    def load(self) -> None:
        """Load articles from ``articles.jsonl``."""
        self._articles.clear()
        articles_path = self.knowledge_dir / "articles.jsonl"
        if not articles_path.exists():
            return
        with articles_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._articles.append(Article.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue

    def search(
        self,
        query: str = "",
        *,
        type: str | None = None,
        tag: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search articles and return ranked results.

        Args:
            query: Keyword string searched across id, title, description, and content.
            type: Filter by article type (concept, mechanism, outcome, connection).
            tag: Filter by tag.
            limit: Maximum number of results.
        """
        if not self._articles:
            self.load()

        keywords = [kw.lower() for kw in query.split() if kw]
        scored: list[tuple[float, Article]] = []

        for article in self._articles:
            if type is not None and article.type != type:
                continue
            if tag is not None and tag not in article.tags:
                continue

            score = self._score(article, keywords)
            if keywords and score == 0:
                continue

            scored.append((score, article))

        # Sort by score desc, then last_updated desc
        scored.sort(key=lambda x: (-x[0], x[1].last_updated), reverse=False)
        return [a.to_dict() for _, a in scored[:limit]]

    def _score(self, article: Article, keywords: list[str]) -> float:
        text = f"{article.id} {article.title} {article.description} {article.content}".lower()
        return sum(1.0 for kw in keywords if kw in text)

    def get(self, article_id: str) -> dict[str, Any] | None:
        """Retrieve a single article by id."""
        if not self._articles:
            self.load()
        for article in self._articles:
            if article.id == article_id:
                return article.to_dict()
        return None
