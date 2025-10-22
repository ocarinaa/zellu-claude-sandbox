"""
Testes unitários: ExtractedInfo.
"""

import pytest
from src.core import ExtractedInfo


def test_extracted_info_creation():
    """Testa criação de ExtractedInfo."""
    info = ExtractedInfo(
        problem_description="Cobrança indevida",
        company_name="NET Claro",
        monetary_value=89.90,
    )

    assert info.problem_description == "Cobrança indevida"
    assert info.company_name == "NET Claro"
    assert info.monetary_value == 89.90
    assert info.has_documents is False


def test_extracted_info_defaults():
    """Testa valores padrão de ExtractedInfo."""
    info = ExtractedInfo()

    assert info.problem_description is None or info.problem_description == ""
    assert info.company_name is None
    assert info.monetary_value is None
    assert info.has_documents is False
    # has_previous_attempts não existe, mas previous_attempts é lista
    assert info.previous_attempts == []


def test_extracted_info_with_documents():
    """Testa ExtractedInfo com documentos."""
    info = ExtractedInfo(
        problem_description="Problema",
        has_documents=True,
    )

    assert info.has_documents is True
