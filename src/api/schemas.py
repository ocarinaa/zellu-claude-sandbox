"""
Schemas de Request/Response para API REST.
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..conversation.schemas import AnalysisData, Message


# === Request Schemas ===

class StartConversationRequest(BaseModel):
    """Request para iniciar uma nova conversa."""

    tone: Optional[Literal["conciliador", "formal", "tecnico"]] = "conciliador"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tone": "conciliador"
            }
        }
    )


class SendMessageRequest(BaseModel):
    """Request para enviar mensagem."""

    message: str = Field(min_length=1, max_length=2000)
    stream: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Fui cobrado indevidamente pela operadora",
                "stream": False
            }
        }
    )


# === Response Schemas ===

class StartConversationResponse(BaseModel):
    """Response ao iniciar conversa."""

    conversation_id: str
    tone: str
    created_at: datetime
    message: str = "Conversa iniciada com sucesso"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "tone": "conciliador",
                "created_at": "2024-01-15T10:30:00",
                "message": "Conversa iniciada com sucesso"
            }
        }
    )


class SendMessageResponse(BaseModel):
    """Response ao enviar mensagem (non-streaming)."""

    conversation_id: str
    message: str
    is_finalized: bool
    message_count: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Entendo sua frustração. Qual operadora te cobrou?",
                "is_finalized": False,
                "message_count": 2
            }
        }
    )


class MessageSchema(BaseModel):
    """Schema de mensagem para response."""

    role: str
    content: str
    timestamp: datetime


class GetConversationResponse(BaseModel):
    """Response ao obter conversa completa."""

    conversation_id: str
    tone: str
    is_finalized: bool
    message_count: int
    messages: list[MessageSchema]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "tone": "conciliador",
                "is_finalized": False,
                "message_count": 4,
                "messages": [
                    {
                        "role": "user",
                        "content": "Fui cobrado indevidamente",
                        "timestamp": "2024-01-15T10:30:00"
                    },
                    {
                        "role": "assistant",
                        "content": "Qual operadora?",
                        "timestamp": "2024-01-15T10:30:05"
                    }
                ],
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:35:00"
            }
        }
    )


class GetAnalysisResponse(BaseModel):
    """Response ao obter análise final."""

    conversation_id: str
    analysis: Optional[AnalysisData]
    is_finalized: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_finalized": True,
                "analysis": {
                    "problem": "Cobrança indevida de R$ 89,90 por 3 meses",
                    "rights": ["CDC Art. 42 - Repetição de indébito em dobro"],
                    "estimatedValue": 539.40,
                    "recommendations": [
                        {
                            "type": "amigavel",
                            "score": 7.5,
                            "reason": "Empresa aceita acordo direto"
                        }
                    ],
                    "userInfo": {},
                    "opposingParty": {},
                    "caseDetails": {}
                }
            }
        }
    )
