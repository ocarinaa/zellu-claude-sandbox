"""Módulo de API REST."""

from .dependencies import get_conversation_manager
from .schemas import (
    StartConversationRequest,
    StartConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetConversationResponse,
    GetAnalysisResponse,
)

__all__ = [
    # Dependencies
    "get_conversation_manager",
    # Schemas
    "StartConversationRequest",
    "StartConversationResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "GetConversationResponse",
    "GetAnalysisResponse",
]
