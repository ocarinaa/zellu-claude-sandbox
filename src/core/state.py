"""
State schema para LangGraph.
Rastreia informações coletadas durante a conversa.
"""

from typing import TypedDict, Literal, Optional, List
from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    """
    Informações extraídas até o momento.
    """
    # Problema
    problem_description: Optional[str] = None
    problem_category: Optional[str] = None  # cobranca_indevida, cancelamento, etc

    # Parte contrária
    company_name: Optional[str] = None
    company_document: Optional[str] = None  # CNPJ
    is_company: bool = True  # True = PJ, False = PF

    # Valores
    monetary_value: Optional[float] = None
    currency: str = "BRL"

    # Tentativas anteriores
    previous_attempts: List[str] = Field(default_factory=list)
    has_protocol: bool = False
    protocol_number: Optional[str] = None

    # Documentos
    has_documents: bool = False
    document_types: List[str] = Field(default_factory=list)

    # Dados do usuário
    user_full_name: Optional[str] = None
    user_cpf: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_address: Optional[str] = None

    # Metadata
    confidence_score: float = 0.0  # 0-1, quão completas são as informações
    missing_fields: List[str] = Field(default_factory=list)


class ConversationGraphState(TypedDict):
    """
    State do grafo LangGraph.
    """
    # Mensagens da conversa
    messages: List[dict]  # [{"role": "user", "content": "..."}, ...]

    # Informações extraídas
    extracted_info: ExtractedInfo

    # Controle de fluxo
    current_step: str  # "collect", "validate", "decide", "analyze", "finish"
    should_finish: bool

    # Tom da conversa
    tone: str  # "conciliador", "formal", "tecnico"

    # Metadata
    chat_id: str
    user_name: Optional[str]
    turn_count: int  # Número de trocas de mensagens


# Tipos úteis
NodeName = Literal["collector", "validator", "decider", "analyzer", "finisher"]
