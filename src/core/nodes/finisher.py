"""
Nó Finisher: Gera análise final estruturada.
"""

from typing import Any
from ...llm import LLMClient
from ...prompts import get_finalization_prompt
from ...conversation.extractor import extract_analysis_data
from ..state import ConversationGraphState

import logging

logger = logging.getLogger(__name__)


async def finisher_node(
    state: ConversationGraphState,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """
    Gera análise final estruturada a partir das informações coletadas.

    Args:
        state: Estado atual do grafo
        llm_client: Cliente LLM

    Returns:
        Estado atualizado com analysis_data
    """
    logger.info("[FINISHER] Gerando análise final")

    extracted = state["extracted_info"]

    # Monta contexto para análise
    context = f"""
INFORMAÇÕES COLETADAS:

Problema: {extracted.problem_description or 'Não informado'}
Empresa/Parte: {extracted.company_name or 'Não informado'}
Valor monetário: {f'R$ {extracted.monetary_value:.2f}' if extracted.monetary_value else 'Não informado'}
Tentativas anteriores: {', '.join(extracted.previous_attempts) if extracted.previous_attempts else 'Nenhuma'}
Documentos disponíveis: {'Sim' if extracted.has_documents else 'Não'}

Dados do usuário:
- Nome: {extracted.user_full_name or 'Não informado'}
- CPF: {extracted.user_cpf or 'Não informado'}
- Email: {extracted.user_email or 'Não informado'}
- Telefone: {extracted.user_phone or 'Não informado'}
"""

    # Gera análise com LLM
    logger.info("[FINISHER] Solicitando análise ao LLM")

    try:
        analysis_response = llm_client.chat(
            messages=[
                {"role": "user", "content": context}
            ],
            system=get_finalization_prompt(),
        )

        logger.debug(f"[FINISHER] LLM response: {analysis_response[:200]}...")

        # Extrai JSON estruturado
        analysis_data = extract_analysis_data(analysis_response)

        logger.info("[FINISHER] Análise extraída com sucesso")
        logger.info(f"[FINISHER] Direitos identificados: {len(analysis_data.rights)}")
        logger.info(f"[FINISHER] Valor estimado: R$ {analysis_data.estimatedValue:.2f}")

        # Atualiza state
        state["analysis_data"] = analysis_data
        state["should_finish"] = True
        state["current_step"] = "finished"

        return state

    except Exception as e:
        logger.error(f"[FINISHER] Erro ao gerar análise: {e}")

        # Fallback: retorna análise vazia
        from ...conversation.schemas import AnalysisData, Recommendation

        fallback_analysis = AnalysisData(
            problem=extracted.problem_description or "Problema não especificado",
            rights=["Análise não disponível devido a erro técnico"],
            estimatedValue=extracted.monetary_value or 0.0,
            recommendations=[
                Recommendation(
                    option="extrajudicial",
                    score=5.0,
                    reason="Recomendação genérica devido a erro na análise",
                )
            ],
        )

        state["analysis_data"] = fallback_analysis
        state["should_finish"] = True
        state["current_step"] = "finished"

        return state


async def finisher_node_with_context(state: ConversationGraphState) -> dict[str, Any]:
    """Wrapper para usar no LangGraph (sem precisar passar llm_client)."""
    from ...llm import LLMClient
    llm_client = LLMClient(primary_provider="anthropic")
    return await finisher_node(state, llm_client)
