"""
Schemas Pydantic para API de Tickets.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from uuid import UUID


# ═══════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════

class TicketCreate(BaseModel):
    """Schema para criar ticket manualmente (opcional)."""
    chat_id: str
    analysis_data: dict
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class TicketUpdate(BaseModel):
    """Schema para atualizar ticket."""
    status: Optional[Literal["novo", "em_analise", "aguardando_cliente", "resolvido", "arquivado"]] = None
    priority: Optional[Literal["baixa", "media", "alta", "urgente"]] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None


class TicketAssign(BaseModel):
    """Schema para atribuir ticket a advogado."""
    assigned_to: str = Field(..., description="Email ou ID do advogado")


class TicketFilter(BaseModel):
    """Schema para filtros de listagem."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    company_name: Optional[str] = None
    user_cpf: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None  # Busca em user_name, company_name, problem_description


# ═══════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class TicketResponse(BaseModel):
    """Schema de resposta completa do ticket."""
    # Identificação
    id: UUID
    ticket_number: int
    chat_id: str
    conversation_id: Optional[UUID] = None

    # Status
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Dados do usuário
    user_name: Optional[str] = None
    user_cpf: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    # Dados do caso
    company_name: Optional[str] = None
    problem_description: Optional[str] = None
    monetary_value: float
    estimated_value: float

    # Análise
    analysis_data: dict
    recommended_approach: Optional[str] = None
    recommended_score: float
    cdc_articles: list[dict] = Field(default_factory=list)

    # Documentos
    has_documents: bool
    documents: list[str] = Field(default_factory=list)

    # Notas
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketSummary(BaseModel):
    """Schema de resposta resumida (para listagens)."""
    id: UUID
    ticket_number: int
    status: str
    priority: str
    user_name: Optional[str] = None
    company_name: Optional[str] = None
    estimated_value: float
    recommended_approach: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Schema de resposta para lista paginada."""
    tickets: list[TicketSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class TicketStats(BaseModel):
    """Estatísticas dos tickets."""
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_approach: dict[str, int]
    avg_estimated_value: float
    total_estimated_value: float
