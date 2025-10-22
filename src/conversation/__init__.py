"""Módulo de gerenciamento de conversação."""

from .manager import ConversationManager
from .schemas import (
    Message,
    ConversationState,
    AnalysisData,
    UserInfo,
    OpposingParty,
    CaseDetails,
    Recommendation,
)

__all__ = [
    # Manager
    "ConversationManager",
    # Schemas
    "Message",
    "ConversationState",
    "AnalysisData",
    "UserInfo",
    "OpposingParty",
    "CaseDetails",
    "Recommendation",
]
