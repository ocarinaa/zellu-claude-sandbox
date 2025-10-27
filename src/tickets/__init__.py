"""
Sistema de Tickets/Chamados da Zellu IA.

Este módulo gerencia todo o ciclo de vida dos tickets:
- Criação a partir de conversações
- Gestão de estados (aberto, em_andamento, resolvido, encerrado)
- Timeline de eventos
- Escalação entre soluções (amigável → extrajudicial → judicial)
- Controle de prazos e SLAs
"""

from .service import TicketService

__version__ = "0.1.0"
__all__ = ["TicketService"]
