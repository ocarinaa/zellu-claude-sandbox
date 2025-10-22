"""
Schemas para gerenciamento de conversação.
"""

from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Type alias para tom de voz
ToneType = Literal["conciliador", "formal", "tecnico"]


class Message(BaseModel):
    """Representa uma mensagem na conversa."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, str]:
        """Converte para formato esperado pela API LLM."""
        return {
            "role": self.role,
            "content": self.content
        }


class UserInfo(BaseModel):
    """Informações do usuário."""

    name: str = "Não informado"
    cpf: str = "Não informado"
    email: str = "Não informado"
    phone: str = "Não informado"
    address: str = "Não informado"


class OpposingParty(BaseModel):
    """Informações da parte contrária (empresa/pessoa)."""

    type: Literal["pj", "pf"] = "pj"
    name: str = "Não informado"
    document: str = "Não informado"  # CNPJ ou CPF
    email: str = "Não informado"
    phone: str = "Não informado"
    address: str = "Não informado"


class CaseDetails(BaseModel):
    """Detalhes do caso jurídico."""

    title: str = "Não informado"
    description: str = "Não informado"
    expectedSolution: str = "Não informado"
    documents: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Recomendação de solução."""

    type: Literal["amigavel", "extrajudicial", "judicial"]
    score: float = Field(ge=0, le=10)
    reason: str


class AnalysisData(BaseModel):
    """
    Dados da análise final do caso.
    Gerado quando a conversa é finalizada.
    """

    problem: str
    rights: list[str] = Field(min_length=1)
    estimatedValue: float = Field(gt=0)
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)
    userInfo: UserInfo
    opposingParty: OpposingParty
    caseDetails: CaseDetails


class ConversationState(BaseModel):
    """
    Estado atual da conversa.
    """

    conversation_id: str
    messages: list[Message] = Field(default_factory=list)
    tone: Literal["conciliador", "formal", "tecnico"] = "conciliador"
    is_finalized: bool = False
    analysis_data: Optional[AnalysisData] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def message_count(self) -> int:
        """Retorna número de mensagens (excluindo system)."""
        return len([m for m in self.messages if m.role != "system"])

    @property
    def user_message_count(self) -> int:
        """Retorna número de mensagens do usuário."""
        return len([m for m in self.messages if m.role == "user"])

    def add_message(self, role: str, content: str) -> None:
        """Adiciona uma mensagem ao histórico."""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.now()

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """Retorna mensagens no formato esperado pela API LLM."""
        return [
            m.to_dict()
            for m in self.messages
            if m.role != "system"
        ]
