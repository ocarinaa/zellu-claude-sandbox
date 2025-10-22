"""
Dependências para injeção no FastAPI.
"""

from functools import lru_cache
from ..conversation import ConversationManager


@lru_cache()
def get_conversation_manager() -> ConversationManager:
    """
    Retorna instância singleton do ConversationManager.

    Usa lru_cache para garantir que seja criada apenas uma instância
    durante todo o ciclo de vida da aplicação.

    Returns:
        ConversationManager singleton
    """
    return ConversationManager()
