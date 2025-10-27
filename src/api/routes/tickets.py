"""
API Routes: Endpoints para gerenciamento de Tickets.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
import logging
import os
from sqlalchemy.orm import Session

from ...database import get_db_session
from ...tickets.service import TicketService
from ..schemas.tickets import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketFilter,
    TicketResponse,
    TicketSummary,
    TicketListResponse,
    TicketStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


# ═══════════════════════════════════════════════════════════════
# DEPENDENCY - Ticket Service
# ═══════════════════════════════════════════════════════════════

def get_ticket_service(db: Session = Depends(get_db_session)) -> TicketService:
    """Dependency para obter o serviço de tickets."""
    return TicketService(db)


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - CREATE
# ═══════════════════════════════════════════════════════════════

@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Cria ticket manualmente.

    Normalmente os tickets são criados automaticamente quando a análise
    é finalizada, mas este endpoint permite criação manual se necessário.
    """
    try:
        ticket = service.create_ticket(data)
        return TicketResponse.model_validate(ticket)
    except Exception as e:
        logger.error(f"[API] Erro ao criar ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar ticket: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - READ
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=TicketListResponse)
async def list_tickets(
    # Filtros
    status: Optional[str] = Query(None, description="Filtrar por status"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridade"),
    assigned_to: Optional[str] = Query(None, description="Filtrar por advogado atribuído"),
    company_name: Optional[str] = Query(None, description="Filtrar por empresa"),
    user_cpf: Optional[str] = Query(None, description="Filtrar por CPF do usuário"),
    date_from: Optional[datetime] = Query(None, description="Data inicial"),
    date_to: Optional[datetime] = Query(None, description="Data final"),
    search: Optional[str] = Query(None, description="Busca textual"),

    # Paginação
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),

    # Ordenação
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_direction: Literal["asc", "desc"] = Query("desc", description="Direção da ordenação"),

    # Service
    service: TicketService = Depends(get_ticket_service)
):
    """
    Lista tickets com filtros e paginação.

    **Filtros disponíveis:**
    - status: novo, em_analise, aguardando_cliente, resolvido, arquivado
    - priority: baixa, media, alta, urgente
    - assigned_to: Email/ID do advogado
    - company_name: Nome da empresa (busca parcial)
    - user_cpf: CPF do usuário (busca exata)
    - date_from, date_to: Intervalo de datas
    - search: Busca textual em nome, empresa e descrição

    **Ordenação:**
    - order_by: created_at, updated_at, estimated_value, priority
    - order_direction: asc ou desc

    **Paginação:**
    - page: Número da página (começa em 1)
    - page_size: Itens por página (máximo 100)
    """
    try:
        filters = TicketFilter(
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            company_name=company_name,
            user_cpf=user_cpf,
            date_from=date_from,
            date_to=date_to,
            search=search
        )

        tickets, total = service.list_tickets(
            filters=filters,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction
        )

        return TicketListResponse(
            tickets=[TicketSummary.model_validate(t) for t in tickets],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    except Exception as e:
        logger.error(f"[API] Erro ao listar tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar tickets: {str(e)}")


@router.get("/stats", response_model=TicketStats)
async def get_stats(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    service: TicketService = Depends(get_ticket_service)
):
    """
    Retorna estatísticas dos tickets.

    **Métricas:**
    - Total de tickets
    - Distribuição por status
    - Distribuição por prioridade
    - Distribuição por tipo de recomendação
    - Valor médio estimado
    - Valor total estimado
    """
    try:
        filters = TicketFilter(status=status, priority=priority)
        return service.get_stats(filters)
    except Exception as e:
        logger.error(f"[API] Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Busca ticket por ID (UUID).
    """
    ticket = service.get_ticket(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    return TicketResponse.model_validate(ticket)


@router.get("/number/{ticket_number}", response_model=TicketResponse)
async def get_ticket_by_number(
    ticket_number: int,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Busca ticket por número (ex: #1234).
    """
    ticket = service.get_ticket_by_number(ticket_number)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_number} não encontrado")

    return TicketResponse.model_validate(ticket)


@router.get("/chat/{chat_id}", response_model=TicketResponse)
async def get_ticket_by_chat(
    chat_id: str,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Busca ticket por chat_id.
    """
    ticket = service.get_ticket_by_chat_id(chat_id)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket para chat {chat_id} não encontrado")

    return TicketResponse.model_validate(ticket)


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - UPDATE
# ═══════════════════════════════════════════════════════════════

@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Atualiza ticket.

    Campos atualizáveis:
    - status: novo, em_analise, aguardando_cliente, resolvido, arquivado
    - priority: baixa, media, alta, urgente
    - assigned_to: Email/ID do advogado
    - notes: Observações
    - tags: Lista de tags
    """
    ticket = service.update_ticket(ticket_id, data)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: UUID,
    data: TicketAssign,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Atribui ticket a um advogado.

    Automaticamente:
    - Define assigned_to
    - Registra assigned_at
    - Muda status de "novo" para "em_analise" (se necessário)
    """
    ticket = service.assign_ticket(ticket_id, data.assigned_to)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    return TicketResponse.model_validate(ticket)


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - DELETE
# ═══════════════════════════════════════════════════════════════

@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service)
):
    """
    Deleta ticket (soft delete - marca como arquivado).
    """
    success = service.delete_ticket(ticket_id)

    if not success:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    return None
