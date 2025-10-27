"""
Testes unitários para utilitários de tickets.
"""

import pytest
from datetime import datetime
from src.tickets.utils import (
    generate_ticket_number,
    generate_uuid,
    format_ticket_status,
    format_solution_type
)


def test_generate_ticket_number_first():
    """Testa geração do primeiro ticket do ano."""
    ticket_number = generate_ticket_number(0)
    year = datetime.now().year

    assert ticket_number == f"ZLU-{year}-000001"


def test_generate_ticket_number_sequential():
    """Testa geração sequencial de tickets."""
    ticket_number = generate_ticket_number(123)
    year = datetime.now().year

    assert ticket_number == f"ZLU-{year}-000124"


def test_generate_ticket_number_padding():
    """Testa padding de zeros no número."""
    ticket_number = generate_ticket_number(99999)
    year = datetime.now().year

    assert ticket_number == f"ZLU-{year}-100000"
    assert len(ticket_number.split('-')[-1]) == 6  # Sempre 6 dígitos


def test_generate_uuid():
    """Testa geração de UUID."""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()

    # UUIDs devem ser diferentes
    assert uuid1 != uuid2

    # UUIDs devem ter formato correto
    assert len(uuid1) == 36
    assert uuid1.count('-') == 4


def test_format_ticket_status():
    """Testa formatação de status."""
    assert format_ticket_status("aberto") == "Aberto"
    assert format_ticket_status("em_andamento") == "Em Andamento"
    assert format_ticket_status("resolvido") == "Resolvido"
    assert format_ticket_status("encerrado") == "Encerrado"


def test_format_ticket_status_unknown():
    """Testa formatação de status desconhecido."""
    assert format_ticket_status("desconhecido") == "Desconhecido"


def test_format_solution_type():
    """Testa formatação de tipo de solução."""
    assert format_solution_type("amigavel") == "Solução Amigável"
    assert format_solution_type("extrajudicial") == "Solução Extrajudicial"
    assert format_solution_type("judicial") == "Solução Judicial"


def test_format_solution_type_unknown():
    """Testa formatação de tipo desconhecido."""
    assert format_solution_type("desconhecido") == "Desconhecido"
