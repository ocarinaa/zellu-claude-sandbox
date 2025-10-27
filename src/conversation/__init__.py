"""Módulo de gerenciamento de conversação."""

from .manager import ConversationManager
from .extractor import extract_analysis_data
from .schemas import (
    ToneType,
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
    # Extractor
    "extract_analysis_data",
    # Schemas
    "ToneType",
    "Message",
    "ConversationState",
    "AnalysisData",
    "UserInfo",
    "OpposingParty",
    "CaseDetails",
    "Recommendation",
]
