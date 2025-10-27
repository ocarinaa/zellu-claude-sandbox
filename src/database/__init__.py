"""Módulo de database."""

from .connection import (
    engine,
    get_sync_engine,
    get_session_factory,
    AsyncSessionLocal,
    get_db,
    get_db_session,
    init_db
)
from .models import Base, Conversation, Message, AnalysisCache, Ticket
from .repositories import (
    ConversationRepository,
    MessageRepository,
    AnalysisCacheRepository,
)

__all__ = [
    # Connection
    "engine",
    "get_sync_engine",
    "get_session_factory",
    "AsyncSessionLocal",
    "get_db",
    "get_db_session",
    "init_db",
    # Models
    "Base",
    "Conversation",
    "Message",
    "AnalysisCache",
    "Ticket",
    # Repositories
    "ConversationRepository",
    "MessageRepository",
    "AnalysisCacheRepository",
]
