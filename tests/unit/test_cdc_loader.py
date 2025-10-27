"""
Testes unitários: CDC Knowledge Base.
"""

import pytest
from src.rag import CDCKnowledgeBase


def test_load_cdc_articles(cdc_kb):
    """Testa carregamento de artigos CDC."""
    assert len(cdc_kb.articles) == 60
    assert cdc_kb.articles[0].number == "4"


def test_get_article_by_number(cdc_kb):
    """Testa busca por número."""
    article = cdc_kb.get_article_by_number("42")

    assert article is not None
    assert article.number == "42"
    assert "cobrança" in article.title.lower()


def test_get_articles_by_category(cdc_kb):
    """Testa busca por categoria."""
    articles = cdc_kb.get_articles_by_category("cobranca")

    assert len(articles) >= 1
    assert any(a.number == "42" for a in articles)


def test_search_by_keyword(cdc_kb):
    """Testa busca por keyword."""
    articles = cdc_kb.search_by_keyword("cobrança indevida")

    assert len(articles) >= 1
    assert any(a.number == "42" for a in articles)
