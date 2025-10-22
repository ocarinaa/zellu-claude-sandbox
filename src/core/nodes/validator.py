"""
Nó Validator: Valida se informações estão completas.
"""

from typing import Any
from ..state import ConversationGraphState, ExtractedInfo

import logging

logger = logging.getLogger(__name__)


REQUIRED_FIELDS = [
    "problem_description",
    "company_name",
    "user_full_name",
]

OPTIONAL_BUT_IMPORTANT = [
    "monetary_value",
    "user_cpf",
    "user_email",
    "user_phone",
]


def validator_node(state: ConversationGraphState) -> dict[str, Any]:
    """
    Valida se informações coletadas estão completas.

    Args:
        state: Estado atual

    Returns:
        Estado atualizado com missing_fields
    """
    logger.info("[VALIDATOR] Validando completude das informações")

    extracted = state["extracted_info"]
    missing = []

    # Valida campos obrigatórios
    for field in REQUIRED_FIELDS:
        value = getattr(extracted, field, None)
        if value is None or value == "":
            missing.append(field)

    # Atualiza missing_fields
    extracted.missing_fields = missing

    # Calcula confidence baseado em completude
    total_fields = len(REQUIRED_FIELDS) + len(OPTIONAL_BUT_IMPORTANT)
    filled_fields = 0

    for field in REQUIRED_FIELDS + OPTIONAL_BUT_IMPORTANT:
        value = getattr(extracted, field, None)
        if value is not None and value != "" and value != []:
            filled_fields += 1

    extracted.confidence_score = filled_fields / total_fields

    state["extracted_info"] = extracted
    state["current_step"] = "decide"

    logger.info(f"[VALIDATOR] Missing fields: {missing}")
    logger.info(f"[VALIDATOR] Confidence: {extracted.confidence_score:.2f}")

    return state
