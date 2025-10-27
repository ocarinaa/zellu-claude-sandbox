"""
Nó Analyzer: Análise jurídica com CDC usando RAG.
"""

from typing import Any
from ..state import ConversationGraphState
from ...rag import initialize_cdc_retriever, CDCRetriever

import logging

logger = logging.getLogger(__name__)

# Singleton do retriever (para não recarregar toda vez)
_retriever: CDCRetriever | None = None


async def analyzer_node(state: ConversationGraphState) -> dict[str, Any]:
    """
    Analisa caso juridicamente usando RAG com CDC.

    Args:
        state: Estado atual

    Returns:
        Estado atualizado com artigos CDC relevantes
    """
    logger.info("[ANALYZER] Analisando caso com RAG")

    global _retriever

    # Inicializa retriever se necessário
    if _retriever is None:
        logger.info("[ANALYZER] Inicializando CDC retriever")
        try:
            _retriever = await initialize_cdc_retriever()
        except Exception as e:
            logger.error(f"[ANALYZER] Erro ao inicializar retriever: {e}")
            logger.warning("[ANALYZER] Continuando sem RAG")
            state["relevant_cdc_articles"] = []
            state["current_step"] = "finish"
            return state

    # Monta query rica para busca
    extracted = state["extracted_info"]

    query_parts = []
    if extracted.problem_description:
        query_parts.append(extracted.problem_description)
    if extracted.problem_category:
        query_parts.append(extracted.problem_category)
    if extracted.previous_attempts:
        query_parts.extend(extracted.previous_attempts)

    query = " ".join(query_parts)

    # Se não há informações suficientes, usa fallback
    if not query.strip():
        logger.warning("[ANALYZER] Query vazia, usando fallback por keywords")
        query = "direitos básicos consumidor"

    # Busca artigos CDC relevantes
    try:
        results = await _retriever.retrieve(query, top_k=5)

        # Extrai artigos e scores
        relevant_articles = [
            {
                "number": article.number,
                "title": article.title,
                "content": article.content,
                "similarity_score": score,
            }
            for article, score in results
        ]

        state["relevant_cdc_articles"] = relevant_articles

        logger.info(f"[ANALYZER] {len(relevant_articles)} artigos CDC identificados")

    except Exception as e:
        logger.error(f"[ANALYZER] Erro ao buscar artigos CDC: {e}")
        state["relevant_cdc_articles"] = []

    state["current_step"] = "finish"

    return state
