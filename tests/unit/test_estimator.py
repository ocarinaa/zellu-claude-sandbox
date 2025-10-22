"""
Testes unitários: Value Estimator.
"""

import pytest
from src.calculators import ValueEstimator


def test_calculate_with_monetary_value(value_estimator, sample_cdc_articles):
    """Testa cálculo com valor monetário."""
    result = value_estimator.calculate(
        monetary_value=100.0,
        relevant_articles=sample_cdc_articles,
        has_documents=False,
    )

    # Art. 42 tem multiplier 2.0 → 100 * 2 = 200 (material)
    # Art. 42 tem moral_damage_base 2000
    # Art. 6 tem moral_damage_base 3000
    # Total esperado: 200 + 2000 + 3000 = 5200

    assert result > 5000
    assert result < 6000


def test_calculate_without_monetary_value(value_estimator, sample_cdc_articles):
    """Testa cálculo sem valor monetário (só dano moral)."""
    result = value_estimator.calculate(
        monetary_value=None,
        relevant_articles=sample_cdc_articles,
        has_documents=False,
    )

    # Só danos morais: 2000 + 3000 = 5000
    assert result >= 5000


def test_calculate_with_documents_bonus(value_estimator, sample_cdc_articles):
    """Testa bonus de documentação (+20% moral)."""
    without_docs = value_estimator.calculate(
        monetary_value=None,
        relevant_articles=sample_cdc_articles,
        has_documents=False,
    )

    with_docs = value_estimator.calculate(
        monetary_value=None,
        relevant_articles=sample_cdc_articles,
        has_documents=True,
    )

    assert with_docs > without_docs


def test_minimum_value(value_estimator):
    """Testa valor mínimo de R$ 500."""
    result = value_estimator.calculate(
        monetary_value=1.0,
        relevant_articles=[],
        has_documents=False,
    )

    assert result >= 500.0
