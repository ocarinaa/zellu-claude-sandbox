"""
Testes para CheckpointService.
"""

import pytest
from src.core.checkpoint import CheckpointService, get_checkpoint_service
from src.core.state import ConversationGraphState, ExtractedInfo


@pytest.fixture
def sample_state() -> ConversationGraphState:
    """Cria estado de exemplo para testes."""
    return {
        "messages": [
            {"role": "user", "content": "Oi, preciso de ajuda"},
            {"role": "assistant", "content": "Olá! Como posso ajudar?"},
        ],
        "extracted_info": ExtractedInfo(
            problem_description="Cobrança indevida",
            company_name="Empresa X",
            monetary_value=100.0,
            user_full_name="João Silva",
            confidence_score=0.75,
        ),
        "current_step": "collect",
        "should_finish": False,
        "tone": "conciliador",
        "chat_id": "test-chat-123",
        "user_name": "João",
        "turn_count": 2,
        "relevant_cdc_articles": [
            {
                "number": "42",
                "title": "Cobrança indevida",
                "content": "...",
                "similarity_score": 0.95,
            }
        ],
    }


@pytest.mark.asyncio
async def test_save_and_load_checkpoint(sample_state):
    """Testa salvamento e carregamento de checkpoint."""
    checkpoint = CheckpointService()

    # Salva checkpoint
    result = await checkpoint.save("test-chat-123", sample_state, auto=True)
    assert result is True

    # Carrega checkpoint
    loaded_state = await checkpoint.load("test-chat-123")
    assert loaded_state is not None
    assert loaded_state["chat_id"] == "test-chat-123"
    assert loaded_state["turn_count"] == 2
    assert loaded_state["current_step"] == "collect"
    assert len(loaded_state["messages"]) == 2

    # Verifica ExtractedInfo
    extracted = loaded_state["extracted_info"]
    assert extracted.problem_description == "Cobrança indevida"
    assert extracted.company_name == "Empresa X"
    assert extracted.monetary_value == 100.0
    assert extracted.confidence_score == 0.75

    # Cleanup
    await checkpoint.delete("test-chat-123")


@pytest.mark.asyncio
async def test_load_nonexistent_checkpoint():
    """Testa carregamento de checkpoint inexistente."""
    checkpoint = CheckpointService()

    loaded = await checkpoint.load("nonexistent-chat-id")
    assert loaded is None


@pytest.mark.asyncio
async def test_delete_checkpoint(sample_state):
    """Testa remoção de checkpoint."""
    checkpoint = CheckpointService()

    # Cria checkpoint
    await checkpoint.save("test-chat-delete", sample_state)

    # Verifica que existe
    exists = await checkpoint.exists("test-chat-delete")
    assert exists is True

    # Remove
    result = await checkpoint.delete("test-chat-delete")
    assert result is True

    # Verifica que não existe mais
    exists = await checkpoint.exists("test-chat-delete")
    assert exists is False


@pytest.mark.asyncio
async def test_checkpoint_exists(sample_state):
    """Testa verificação de existência."""
    checkpoint = CheckpointService()

    # Não existe
    exists = await checkpoint.exists("test-chat-exists")
    assert exists is False

    # Cria
    await checkpoint.save("test-chat-exists", sample_state)

    # Agora existe
    exists = await checkpoint.exists("test-chat-exists")
    assert exists is True

    # Cleanup
    await checkpoint.delete("test-chat-exists")


@pytest.mark.asyncio
async def test_checkpoint_with_analysis_data(sample_state):
    """Testa checkpoint com analysis_data completo."""
    checkpoint = CheckpointService()

    # Adiciona analysis_data ao state
    sample_state["analysis_data"] = {
        "problem": "Cobrança indevida",
        "rights": ["CDC Art. 42"],
        "estimatedValue": 200.0,
        "recommendations": [
            {"type": "amigavel", "score": 8.5, "reason": "Alta chance de sucesso"}
        ],
    }

    sample_state["current_step"] = "done"

    # Salva
    await checkpoint.save("test-chat-analysis", sample_state)

    # Carrega
    loaded = await checkpoint.load("test-chat-analysis")
    assert loaded is not None
    assert "analysis_data" in loaded
    assert loaded["analysis_data"]["estimatedValue"] == 200.0
    assert len(loaded["analysis_data"]["recommendations"]) == 1

    # Cleanup
    await checkpoint.delete("test-chat-analysis")


@pytest.mark.asyncio
async def test_list_all_checkpoints(sample_state):
    """Testa listagem de checkpoints."""
    checkpoint = CheckpointService()

    # Cria múltiplos checkpoints
    await checkpoint.save("test-chat-list-1", sample_state)
    await checkpoint.save("test-chat-list-2", sample_state)
    await checkpoint.save("test-chat-list-3", sample_state)

    # Lista todos
    all_checkpoints = await checkpoint.list_all()

    # Deve conter os 3 criados (pode ter mais se houver outros testes rodando)
    assert "test-chat-list-1" in all_checkpoints
    assert "test-chat-list-2" in all_checkpoints
    assert "test-chat-list-3" in all_checkpoints

    # Cleanup
    await checkpoint.delete("test-chat-list-1")
    await checkpoint.delete("test-chat-list-2")
    await checkpoint.delete("test-chat-list-3")


@pytest.mark.asyncio
async def test_checkpoint_overwrite(sample_state):
    """Testa sobrescrita de checkpoint."""
    checkpoint = CheckpointService()

    # Salva versão 1
    sample_state["turn_count"] = 5
    await checkpoint.save("test-chat-overwrite", sample_state)

    # Carrega
    loaded = await checkpoint.load("test-chat-overwrite")
    assert loaded["turn_count"] == 5

    # Atualiza e sobrescreve
    sample_state["turn_count"] = 10
    await checkpoint.save("test-chat-overwrite", sample_state)

    # Carrega novamente
    loaded = await checkpoint.load("test-chat-overwrite")
    assert loaded["turn_count"] == 10

    # Cleanup
    await checkpoint.delete("test-chat-overwrite")


def test_singleton_get_checkpoint_service():
    """Testa que get_checkpoint_service() retorna singleton."""
    service1 = get_checkpoint_service()
    service2 = get_checkpoint_service()

    # Deve ser a mesma instância
    assert service1 is service2


@pytest.mark.asyncio
async def test_checkpoint_with_empty_extracted_info():
    """Testa checkpoint com ExtractedInfo vazio."""
    checkpoint = CheckpointService()

    state: ConversationGraphState = {
        "messages": [],
        "extracted_info": ExtractedInfo(),
        "current_step": "collect",
        "should_finish": False,
        "tone": "conciliador",
        "chat_id": "test-empty",
        "user_name": None,
        "turn_count": 0,
        "relevant_cdc_articles": [],
    }

    # Salva
    result = await checkpoint.save("test-empty", state)
    assert result is True

    # Carrega
    loaded = await checkpoint.load("test-empty")
    assert loaded is not None
    assert loaded["turn_count"] == 0
    assert loaded["extracted_info"].confidence_score == 0.0

    # Cleanup
    await checkpoint.delete("test-empty")


@pytest.mark.asyncio
async def test_checkpoint_ttl():
    """Testa configuração de TTL."""
    # Cria checkpoint com TTL curto (1 segundo)
    checkpoint = CheckpointService(ttl=1)

    state: ConversationGraphState = {
        "messages": [],
        "extracted_info": ExtractedInfo(),
        "current_step": "collect",
        "should_finish": False,
        "tone": "conciliador",
        "chat_id": "test-ttl",
        "user_name": None,
        "turn_count": 0,
        "relevant_cdc_articles": [],
    }

    # Salva
    await checkpoint.save("test-ttl", state)

    # Deve existir imediatamente
    exists = await checkpoint.exists("test-ttl")
    assert exists is True

    # Aguarda TTL expirar (1 segundo + margem)
    import asyncio
    await asyncio.sleep(1.5)

    # Não deve mais existir
    exists = await checkpoint.exists("test-ttl")
    assert exists is False
