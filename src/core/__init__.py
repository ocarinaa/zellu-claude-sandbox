"""
LangGraph State Machine Core.

Este módulo implementa o state machine inteligente para conversa jurídica:
- State schema para rastrear informações coletadas
- 5 nós especializados (collector, validator, decider, analyzer, finisher)
- Edges condicionais baseados em completude de informações
- Extração incremental de dados estruturados
"""

from .state import ConversationGraphState, ExtractedInfo, NodeName
from .graph import create_conversation_graph, compile_conversation_graph
from .nodes import (
    collector_node,
    validator_node,
    decider_node,
    analyzer_node,
    finisher_node,
)
from .checkpoint import CheckpointService, get_checkpoint_service

__all__ = [
    # State
    "ConversationGraphState",
    "ExtractedInfo",
    "NodeName",
    # Graph
    "create_conversation_graph",
    "compile_conversation_graph",
    # Nodes
    "collector_node",
    "validator_node",
    "decider_node",
    "analyzer_node",
    "finisher_node",
    # Checkpoint
    "CheckpointService",
    "get_checkpoint_service",
]
