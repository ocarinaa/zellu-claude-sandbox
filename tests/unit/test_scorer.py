"""
Testes unitários: Recommendation Scorer.
"""

import pytest
from src.calculators import RecommendationScorer


def test_calculate_scores_basic(recommendation_scorer, sample_cdc_articles):
    """Testa cálculo básico de scores."""
    recommendations = recommendation_scorer.calculate_scores(
        relevant_articles=sample_cdc_articles,
        monetary_value=100.0,
        has_documents=False,
        has_previous_attempts=False,
    )

    assert len(recommendations) == 3
    assert recommendations[0]["type"] == "amigavel"
    assert recommendations[1]["type"] == "extrajudicial"
    assert recommendations[2]["type"] == "judicial"

    # Todos têm scores
    for rec in recommendations:
        assert 0 <= rec["score"] <= 10
        assert isinstance(rec["reason"], str)


def test_clear_violation_bonus(recommendation_scorer):
    """Testa bonus de violação clara (Art. 42)."""
    articles_with_42 = [
        {
            "number": "42",
            "title": "Cobrança Indevida",
            "content": "...",
            "similarity_score": 0.95,
        }
    ]

    recommendations = recommendation_scorer.calculate_scores(
        relevant_articles=articles_with_42,
        monetary_value=100.0,
        has_documents=False,
        has_previous_attempts=False,
    )

    # Amigável deve ter score alto (Art. 42 é violação clara)
    amigavel = recommendations[0]
    assert amigavel["score"] >= 8.0


def test_previous_attempts_modifier(recommendation_scorer, sample_cdc_articles):
    """Testa modificador de tentativas anteriores."""
    without_attempts = recommendation_scorer.calculate_scores(
        relevant_articles=sample_cdc_articles,
        monetary_value=100.0,
        has_documents=False,
        has_previous_attempts=False,
    )

    with_attempts = recommendation_scorer.calculate_scores(
        relevant_articles=sample_cdc_articles,
        monetary_value=100.0,
        has_documents=False,
        has_previous_attempts=True,
    )

    # Amigável deve diminuir, extrajudicial deve aumentar
    assert with_attempts[0]["score"] < without_attempts[0]["score"]  # amigavel
    assert with_attempts[1]["score"] > without_attempts[1]["score"]  # extrajudicial
