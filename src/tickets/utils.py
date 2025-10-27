"""
Utilitários para o sistema de tickets.
"""

from datetime import datetime
import uuid


def generate_ticket_number(last_number: int = 0) -> str:
    """
    Gera número único de ticket no formato ZLU-YYYY-NNNNNN.

    Args:
        last_number: Último número sequencial usado no ano atual.
                     Se 0, começa do 1.

    Returns:
        String no formato "ZLU-2025-000001"

    Examples:
        >>> generate_ticket_number(0)
        'ZLU-2025-000001'
        >>> generate_ticket_number(123)
        'ZLU-2025-000124'
    """
    year = datetime.now().year
    next_number = last_number + 1

    return f"ZLU-{year}-{next_number:06d}"


def generate_uuid() -> str:
    """
    Gera UUID v4 como string.

    Returns:
        String UUID no formato "550e8400-e29b-41d4-a716-446655440000"
    """
    return str(uuid.uuid4())


def format_ticket_status(status: str) -> str:
    """
    Formata status do ticket para exibição.

    Args:
        status: Status raw do ticket (ex: "em_andamento")

    Returns:
        Status formatado (ex: "Em Andamento")

    Examples:
        >>> format_ticket_status("em_andamento")
        'Em Andamento'
        >>> format_ticket_status("aberto")
        'Aberto'
    """
    status_map = {
        "aberto": "Aberto",
        "em_andamento": "Em Andamento",
        "resolvido": "Resolvido",
        "encerrado": "Encerrado"
    }

    return status_map.get(status, status.title())


def format_solution_type(solution_type: str) -> str:
    """
    Formata tipo de solução para exibição.

    Args:
        solution_type: Tipo raw (ex: "amigavel")

    Returns:
        Tipo formatado (ex: "Solução Amigável")

    Examples:
        >>> format_solution_type("amigavel")
        'Solução Amigável'
        >>> format_solution_type("judicial")
        'Solução Judicial'
    """
    type_map = {
        "amigavel": "Solução Amigável",
        "extrajudicial": "Solução Extrajudicial",
        "judicial": "Solução Judicial"
    }

    return type_map.get(solution_type, solution_type.title())
