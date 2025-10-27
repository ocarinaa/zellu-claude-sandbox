"""
Serviço de gerenciamento de Tickets.
Responsável por todas as operações CRUD e lógica de negócio.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, func

from ..database.models import Ticket
from ..api.schemas.tickets import (
    TicketCreate,
    TicketUpdate,
    TicketFilter,
    TicketResponse,
    TicketSummary,
    TicketStats
)

import logging

logger = logging.getLogger(__name__)


class TicketService:
    """Serviço de gerenciamento de tickets."""

    def __init__(self, db_session: Session):
        """
        Inicializa o serviço com uma sessão do banco.

        Args:
            db_session: Sessão do SQLAlchemy
        """
        self.db = db_session

    # ═══════════════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════════════

    def create_ticket_from_analysis(
        self,
        chat_id: str,
        analysis_data: dict,
        conversation_id: Optional[UUID] = None
    ) -> Ticket:
        """
        Cria ticket automaticamente a partir da análise finalizada.

        Args:
            chat_id: ID do chat
            analysis_data: Dados completos da análise
            conversation_id: ID da conversa no banco (opcional)

        Returns:
            Ticket criado
        """
        logger.info(f"[TICKET] Criando ticket para chat_id: {chat_id}")

        # Extrai informações da análise
        recommendations = analysis_data.get("recommendations", [])
        user_info = analysis_data.get("userInfo", {})
        opposing_party = analysis_data.get("opposingParty", {})
        case_details = analysis_data.get("caseDetails", {})

        # Determina melhor recomendação (maior score)
        best_recommendation = max(recommendations, key=lambda x: x["score"]) if recommendations else None

        # Determina prioridade baseada em:
        # 1. Valor estimado
        # 2. Artigos CDC graves (42, 71)
        # 3. Score judicial alto
        priority = self._calculate_priority(analysis_data)

        # Cria ticket
        ticket = Ticket(
            chat_id=chat_id,
            conversation_id=conversation_id,
            status="novo",
            priority=priority,

            # Dados do usuário
            user_name=user_info.get("name"),
            user_cpf=user_info.get("cpf"),
            user_email=user_info.get("email"),
            user_phone=user_info.get("phone"),

            # Dados do caso
            company_name=opposing_party.get("name"),
            problem_description=analysis_data.get("problem"),
            monetary_value=0.0,  # Pode ser extraído se disponível
            estimated_value=analysis_data.get("estimatedValue", 0.0),

            # Análise
            analysis_data=analysis_data,
            recommended_approach=best_recommendation["type"] if best_recommendation else None,
            recommended_score=best_recommendation["score"] if best_recommendation else 0.0,
            cdc_articles=analysis_data.get("rights", []),

            # Documentos
            has_documents=len(case_details.get("documents", [])) > 0,
            documents=case_details.get("documents", []),
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        logger.info(f"[TICKET] ✅ Ticket #{ticket.ticket_number} criado com prioridade {priority}")

        return ticket

    def create_ticket(self, data: TicketCreate) -> Ticket:
        """
        Cria ticket manualmente.

        Args:
            data: Dados para criação

        Returns:
            Ticket criado
        """
        ticket = Ticket(
            chat_id=data.chat_id,
            analysis_data=data.analysis_data,
            notes=data.notes,
            tags=data.tags
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    # ═══════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════

    def get_ticket(self, ticket_id: UUID) -> Optional[Ticket]:
        """
        Busca ticket por ID.

        Args:
            ticket_id: UUID do ticket

        Returns:
            Ticket ou None
        """
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def get_ticket_by_number(self, ticket_number: int) -> Optional[Ticket]:
        """
        Busca ticket por número.

        Args:
            ticket_number: Número do ticket

        Returns:
            Ticket ou None
        """
        return self.db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()

    def get_ticket_by_chat_id(self, chat_id: str) -> Optional[Ticket]:
        """
        Busca ticket por chat_id.

        Args:
            chat_id: ID do chat

        Returns:
            Ticket ou None
        """
        return self.db.query(Ticket).filter(Ticket.chat_id == chat_id).first()

    def list_tickets(
        self,
        filters: Optional[TicketFilter] = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> tuple[list[Ticket], int]:
        """
        Lista tickets com filtros e paginação.

        Args:
            filters: Filtros a aplicar
            page: Número da página (começa em 1)
            page_size: Tamanho da página
            order_by: Campo para ordenação
            order_direction: asc ou desc

        Returns:
            Tupla (tickets, total)
        """
        query = self.db.query(Ticket)

        # Aplica filtros
        if filters:
            if filters.status:
                query = query.filter(Ticket.status == filters.status)

            if filters.priority:
                query = query.filter(Ticket.priority == filters.priority)

            if filters.assigned_to:
                query = query.filter(Ticket.assigned_to == filters.assigned_to)

            if filters.company_name:
                query = query.filter(Ticket.company_name.ilike(f"%{filters.company_name}%"))

            if filters.user_cpf:
                query = query.filter(Ticket.user_cpf == filters.user_cpf)

            if filters.date_from:
                query = query.filter(Ticket.created_at >= filters.date_from)

            if filters.date_to:
                query = query.filter(Ticket.created_at <= filters.date_to)

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Ticket.user_name.ilike(search_term),
                        Ticket.company_name.ilike(search_term),
                        Ticket.problem_description.ilike(search_term)
                    )
                )

        # Conta total
        total = query.count()

        # Ordenação
        order_column = getattr(Ticket, order_by, Ticket.created_at)
        if order_direction == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))

        # Paginação
        offset = (page - 1) * page_size
        tickets = query.offset(offset).limit(page_size).all()

        return tickets, total

    def get_stats(self, filters: Optional[TicketFilter] = None) -> TicketStats:
        """
        Retorna estatísticas dos tickets.

        Args:
            filters: Filtros opcionais

        Returns:
            Estatísticas
        """
        query = self.db.query(Ticket)

        # Aplica filtros (mesma lógica de list_tickets)
        if filters:
            if filters.status:
                query = query.filter(Ticket.status == filters.status)
            if filters.priority:
                query = query.filter(Ticket.priority == filters.priority)
            # ... outros filtros

        total = query.count()

        # Agrupa por status
        by_status = {}
        status_counts = self.db.query(
            Ticket.status,
            func.count(Ticket.id)
        ).group_by(Ticket.status).all()
        for status, count in status_counts:
            by_status[status] = count

        # Agrupa por prioridade
        by_priority = {}
        priority_counts = self.db.query(
            Ticket.priority,
            func.count(Ticket.id)
        ).group_by(Ticket.priority).all()
        for priority, count in priority_counts:
            by_priority[priority] = count

        # Agrupa por recomendação
        by_approach = {}
        approach_counts = self.db.query(
            Ticket.recommended_approach,
            func.count(Ticket.id)
        ).group_by(Ticket.recommended_approach).all()
        for approach, count in approach_counts:
            if approach:
                by_approach[approach] = count

        # Valores
        avg_value = self.db.query(func.avg(Ticket.estimated_value)).scalar() or 0.0
        total_value = self.db.query(func.sum(Ticket.estimated_value)).scalar() or 0.0

        return TicketStats(
            total=total,
            by_status=by_status,
            by_priority=by_priority,
            by_approach=by_approach,
            avg_estimated_value=float(avg_value),
            total_estimated_value=float(total_value)
        )

    # ═══════════════════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════════════════

    def update_ticket(self, ticket_id: UUID, data: TicketUpdate) -> Optional[Ticket]:
        """
        Atualiza ticket.

        Args:
            ticket_id: UUID do ticket
            data: Dados para atualização

        Returns:
            Ticket atualizado ou None
        """
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        # Atualiza campos fornecidos
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(ticket, field, value)

        # Atualiza timestamps especiais
        if data.status == "resolvido" and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()

        if data.status == "arquivado" and not ticket.archived_at:
            ticket.archived_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(ticket)

        logger.info(f"[TICKET] Ticket #{ticket.ticket_number} atualizado")

        return ticket

    def assign_ticket(self, ticket_id: UUID, assigned_to: str) -> Optional[Ticket]:
        """
        Atribui ticket a um advogado.

        Args:
            ticket_id: UUID do ticket
            assigned_to: Email/ID do advogado

        Returns:
            Ticket atualizado ou None
        """
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        ticket.assigned_to = assigned_to
        ticket.assigned_at = datetime.utcnow()

        # Se estava como "novo", muda para "em_analise"
        if ticket.status == "novo":
            ticket.status = "em_analise"

        self.db.commit()
        self.db.refresh(ticket)

        logger.info(f"[TICKET] Ticket #{ticket.ticket_number} atribuído a {assigned_to}")

        return ticket

    # ═══════════════════════════════════════════════════════════════
    # DELETE
    # ═══════════════════════════════════════════════════════════════

    def delete_ticket(self, ticket_id: UUID) -> bool:
        """
        Deleta ticket (soft delete - marca como arquivado).

        Args:
            ticket_id: UUID do ticket

        Returns:
            True se deletado, False se não encontrado
        """
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False

        ticket.status = "arquivado"
        ticket.archived_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"[TICKET] Ticket #{ticket.ticket_number} arquivado")

        return True

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _calculate_priority(self, analysis_data: dict) -> str:
        """
        Calcula prioridade do ticket baseado na análise.

        Regras:
        - URGENTE: Valor > R$ 50.000 OU Artigos graves (42, 71) com valor > R$ 10.000
        - ALTA: Valor > R$ 10.000 OU Score judicial > 7.0
        - MÉDIA: Valor > R$ 1.000 OU Múltiplas violações
        - BAIXA: Demais casos

        Args:
            analysis_data: Dados da análise

        Returns:
            Prioridade (baixa, media, alta, urgente)
        """
        estimated_value = analysis_data.get("estimatedValue", 0.0)
        recommendations = analysis_data.get("recommendations", [])
        rights = analysis_data.get("rights", [])

        # Verifica artigos graves
        has_grave_violation = any(
            "42" in str(right) or "71" in str(right)
            for right in rights
        )

        # Score judicial
        judicial_rec = next(
            (r for r in recommendations if r.get("type") == "judicial"),
            None
        )
        judicial_score = judicial_rec.get("score", 0.0) if judicial_rec else 0.0

        # Aplica regras
        if estimated_value > 50000:
            return "urgente"

        if has_grave_violation and estimated_value > 10000:
            return "urgente"

        if estimated_value > 10000 or judicial_score > 7.0:
            return "alta"

        if estimated_value > 1000 or len(rights) >= 3:
            return "media"

        return "baixa"
