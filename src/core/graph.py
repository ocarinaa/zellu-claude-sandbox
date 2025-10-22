"""
LangGraph State Machine - Orchestrates conversation flow.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from .state import ConversationGraphState
from .nodes import (
    collector_node_with_context,
    validator_node,
    decider_node,
    analyzer_node,
    finisher_node_with_context,
)

import logging

logger = logging.getLogger(__name__)


def should_finish_route(state: ConversationGraphState) -> Literal["analyze", "collect"]:
    """
    Roteamento condicional após decider.

    Returns:
        "analyze": Se deve finalizar e analisar
        "collect": Se deve continuar coletando informações
    """
    if state["should_finish"]:
        logger.info("[ROUTER] should_finish=True → analyze")
        return "analyze"
    else:
        logger.info("[ROUTER] should_finish=False → collect")
        return "collect"


def create_conversation_graph() -> StateGraph:
    """
    Cria grafo de conversa com LangGraph.

    Fluxo:
    1. collector: Coleta informações através de conversa natural
    2. validator: Valida completude das informações
    3. decider: Decide se continua ou finaliza
       - Se should_finish=False: volta para collector
       - Se should_finish=True: vai para analyzer
    4. analyzer: Análise jurídica (placeholder por enquanto)
    5. finisher: Gera análise final estruturada
    6. END

    Returns:
        StateGraph configurado
    """
    logger.info("[GRAPH] Criando grafo de conversa")

    # Cria grafo
    workflow = StateGraph(ConversationGraphState)

    # Adiciona nós
    workflow.add_node("collector", collector_node_with_context)
    workflow.add_node("validator", validator_node)
    workflow.add_node("decider", decider_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("finisher", finisher_node_with_context)

    # Define entry point
    workflow.set_entry_point("collector")

    # Edges sequenciais
    workflow.add_edge("collector", "validator")
    workflow.add_edge("validator", "decider")

    # Edge condicional: decider → analyze OU collect
    workflow.add_conditional_edges(
        "decider",
        should_finish_route,
        {
            "analyze": "analyzer",
            "collect": "collector",
        },
    )

    # Edges finais
    workflow.add_edge("analyzer", "finisher")
    workflow.add_edge("finisher", END)

    logger.info("[GRAPH] Grafo criado com sucesso")
    logger.info("[GRAPH] Nós: collector, validator, decider, analyzer, finisher")
    logger.info("[GRAPH] Entry point: collector")

    return workflow


def compile_conversation_graph():
    """
    Compila grafo para execução.

    Returns:
        Grafo compilado pronto para uso
    """
    workflow = create_conversation_graph()
    compiled = workflow.compile()

    logger.info("[GRAPH] Grafo compilado e pronto para uso")

    return compiled
