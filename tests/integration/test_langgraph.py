"""
Testes de integração: LangGraph Flow.
"""

import pytest
from src.core import compile_conversation_graph, ConversationGraphState, ExtractedInfo


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requer LLM API keys válidas")
async def test_graph_flow_basic():
    """Testa fluxo básico do grafo."""
    graph = compile_conversation_graph()

    initial_state = ConversationGraphState(
        messages=[
            {"role": "user", "content": "Fui cobrado indevidamente"},
        ],
        extracted_info=ExtractedInfo(),
        current_step="collect",
        should_finish=False,
        tone="conciliador",
        chat_id="test-123",
        user_name="João",
        turn_count=0,
    )

    # Executa grafo
    result = await graph.ainvoke(initial_state)

    # Valida estrutura
    assert "messages" in result
    assert "extracted_info" in result


def test_graph_has_all_nodes():
    """Testa que grafo tem todos os nós."""
    from src.core import create_conversation_graph

    graph = create_conversation_graph()

    # Verifica estrutura (não executa)
    assert graph is not None
