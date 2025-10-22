"""
Testes de integração: Persistência (PostgreSQL + Redis).
"""

import pytest
from src.conversation import ConversationManager


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer PostgreSQL e Redis rodando")
async def test_conversation_manager_save_and_load():
    """Testa salvamento e carregamento de conversa."""
    # TODO: Implementar quando tiver DB de teste configurado
    pass


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer Redis rodando")
async def test_redis_cache():
    """Testa cache Redis."""
    # TODO: Implementar quando tiver Redis de teste configurado
    pass
