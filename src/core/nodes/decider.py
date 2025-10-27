"""
Nó Decider: Decide próxima ação (continuar coletando ou finalizar).
"""

from typing import Any
from ..state import ConversationGraphState

import logging

logger = logging.getLogger(__name__)


# Configurações de decisão
MIN_TURNS = 3  # Mínimo de trocas antes de finalizar
MIN_CONFIDENCE = 0.7  # Confidence mínimo para finalizar
MAX_TURNS = 10  # Máximo de tentativas (evitar loop infinito)


def decider_node(state: ConversationGraphState) -> dict[str, Any]:
    """
    Decide se deve continuar coletando ou finalizar conversa.

    Critérios para continuar coletando:
    1. Menos de MIN_TURNS trocas
    2. Campos obrigatórios faltando
    3. Confidence < MIN_CONFIDENCE
    4. Não atingiu MAX_TURNS

    Args:
        state: Estado atual

    Returns:
        Estado atualizado com should_finish e current_step
    """
    logger.info(f"[DECIDER] Decidindo próximo passo (turn {state['turn_count']})")

    extracted = state["extracted_info"]
    turn_count = state["turn_count"]
    missing_fields = extracted.missing_fields
    confidence = extracted.confidence_score

    # Log status atual
    logger.info(f"[DECIDER] Missing fields: {missing_fields}")
    logger.info(f"[DECIDER] Confidence: {confidence:.2f}")
    logger.info(f"[DECIDER] Turn count: {turn_count}")

    # Decisão: Deve continuar coletando?
    should_continue = False

    # Critério 1: Mínimo de trocas ainda não atingido
    if turn_count < MIN_TURNS:
        logger.info(f"[DECIDER] Continuar: turn_count ({turn_count}) < MIN_TURNS ({MIN_TURNS})")
        should_continue = True

    # Critério 2: Campos obrigatórios faltando
    if missing_fields:
        logger.info(f"[DECIDER] Continuar: campos obrigatórios faltando {missing_fields}")
        should_continue = True

    # Critério 3: Confidence baixo
    if confidence < MIN_CONFIDENCE:
        logger.info(f"[DECIDER] Continuar: confidence ({confidence:.2f}) < MIN_CONFIDENCE ({MIN_CONFIDENCE})")
        should_continue = True

    # Critério 4: Máximo de tentativas (evitar loop)
    if turn_count >= MAX_TURNS:
        logger.warning(f"[DECIDER] Forçar finalização: MAX_TURNS ({MAX_TURNS}) atingido")
        should_continue = False

    # Atualiza state
    if should_continue:
        state["should_finish"] = False
        state["current_step"] = "collect"
        logger.info("[DECIDER] Decisão: CONTINUAR COLETANDO")
    else:
        state["should_finish"] = True
        state["current_step"] = "analyze"
        logger.info("[DECIDER] Decisão: FINALIZAR E ANALISAR")

    return state
