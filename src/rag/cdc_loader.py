"""
Carregador da base CDC.
"""

import json
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)


class CDCArticle(BaseModel):
    """Artigo do CDC estruturado."""
    number: str
    title: str
    content: str
    keywords: List[str]
    category: str


class CDCKnowledgeBase:
    """Base de conhecimento do CDC."""

    def __init__(self, json_path: str | None = None):
        """
        Carrega base CDC do JSON.

        Args:
            json_path: Caminho para cdc.json (padrão: kb/cdc.json)
        """
        if json_path is None:
            # Padrão: mesmo diretório
            current_dir = Path(__file__).parent
            json_path = current_dir / "kb" / "cdc.json"

        self.articles: List[CDCArticle] = []
        self._load_from_json(json_path)

    def _load_from_json(self, path: Path | str) -> None:
        """Carrega artigos do JSON."""
        path = Path(path)

        if not path.exists():
            logger.error(f"[CDC] Arquivo não encontrado: {path}")
            raise FileNotFoundError(f"CDC JSON não encontrado em {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for article_data in data["articles"]:
            self.articles.append(CDCArticle(**article_data))

        logger.info(f"[CDC] {len(self.articles)} artigos carregados")

    def get_article_by_number(self, number: str) -> CDCArticle | None:
        """Busca artigo por número."""
        for article in self.articles:
            if article.number == number:
                return article
        return None

    def get_articles_by_category(self, category: str) -> List[CDCArticle]:
        """Busca artigos por categoria."""
        return [a for a in self.articles if a.category == category]

    def search_by_keyword(self, keyword: str) -> List[CDCArticle]:
        """Busca artigos que contenham keyword."""
        keyword_lower = keyword.lower()
        results = []

        for article in self.articles:
            if any(keyword_lower in kw.lower() for kw in article.keywords):
                results.append(article)
            elif keyword_lower in article.content.lower():
                results.append(article)

        return results
