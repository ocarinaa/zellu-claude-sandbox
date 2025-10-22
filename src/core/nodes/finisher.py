"""
Nó Finisher: Gera analysis_data com RAG + Heurísticas.
"""

from typing import Any
from ...llm import LLMClient
from ...prompts import get_finalization_prompt
from ...conversation.extractor import extract_analysis_data
from ...calculators import ValueEstimator, RecommendationScorer
from ..state import ConversationGraphState

import logging

logger = logging.getLogger(__name__)


async def finisher_node(
    state: ConversationGraphState,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """
    Gera analysis_data final com RAG + Heurísticas.

    Args:
        state: Estado atual
        llm_client: Cliente LLM

    Returns:
        Estado atualizado com analysis_data completo
    """
    logger.info("[FINISHER] Gerando analysis_data com RAG + Heurísticas")

    extracted = state["extracted_info"]
    relevant_articles = state.get("relevant_cdc_articles", [])

    # === 1. CALCULA VALOR ESTIMADO ===
    estimator = ValueEstimator()
    estimated_value = estimator.calculate(
        monetary_value=extracted.monetary_value,
        relevant_articles=relevant_articles,
        has_documents=extracted.has_documents,
    )

    # === 2. RANKEIA RECOMENDAÇÕES ===
    scorer = RecommendationScorer()
    recommendations = scorer.calculate_scores(
        relevant_articles=relevant_articles,
        monetary_value=extracted.monetary_value,
        has_documents=extracted.has_documents,
        has_previous_attempts=len(extracted.previous_attempts) > 0,
    )

    # === 3. MONTA CONTEXTO RICO PARA LLM ===
    # Inclui artigos CDC encontrados
    cdc_context = "\n\nARTIGOS CDC APLICÁVEIS:\n"
    for article in relevant_articles:
        cdc_context += f"\n• CDC Art. {article['number']} - {article['title']}\n"
        cdc_context += f"  {article['content'][:200]}...\n"
        cdc_context += f"  Similaridade: {article['similarity_score']:.2f}\n"

    context = f"""Informações coletadas:

PROBLEMA:
- Descrição: {extracted.problem_description}
- Categoria: {extracted.problem_category or 'não especificada'}

PARTE CONTRÁRIA:
- Nome: {extracted.company_name}
- Tipo: {'Pessoa Jurídica' if extracted.is_company else 'Pessoa Física'}

VALORES:
- Valor envolvido: {f'R$ {extracted.monetary_value:.2f}' if extracted.monetary_value else 'não especificado'}
- **VALOR ESTIMADO (calculado): R$ {estimated_value:.2f}**

TENTATIVAS ANTERIORES:
{chr(10).join(f'- {attempt}' for attempt in extracted.previous_attempts) or '- Nenhuma'}

DOCUMENTOS:
- Possui: {'Sim' if extracted.has_documents else 'Não'}

USUÁRIO:
- Nome: {extracted.user_full_name}
- CPF: {extracted.user_cpf or 'não informado'}
- Email: {extracted.user_email or 'não informado'}
- Telefone: {extracted.user_phone or 'não informado'}

{cdc_context}

RECOMENDAÇÕES (calculadas):
{chr(10).join(f'- {rec["type"].upper()}: {rec["score"]}/10 - {rec["reason"]}' for rec in recommendations)}
"""

    # === 4. GERA ANÁLISE COMPLETA COM LLM ===
    messages_with_context = state["messages"].copy()
    messages_with_context.append({
        "role": "user",
        "content": f"Gere a análise completa usando as informações e cálculos abaixo.\n\n{context}",
    })

    finalization_prompt = get_finalization_prompt()
    finalization_prompt += f"""

IMPORTANTE:
- Use estimatedValue: {estimated_value}
- Use exatamente as 3 recommendations fornecidas acima
- Em 'rights', cite os artigos CDC encontrados (use CDC Art. X - descrição)
"""

    try:
        response = llm_client.chat(
            messages=messages_with_context,
            system=finalization_prompt,
        )

        # === 5. EXTRAI JSON ===
        analysis_data = extract_analysis_data(response)

        # === 6. FORÇA VALORES CALCULADOS (garantia) ===
        analysis_dict = analysis_data.model_dump()
        analysis_dict["estimatedValue"] = estimated_value
        analysis_dict["recommendations"] = recommendations

        # Adiciona artigos CDC aos rights se LLM não incluiu
        rights_text = " ".join(analysis_dict.get("rights", []))
        for article in relevant_articles[:3]:  # Top 3
            article_ref = f"CDC Art. {article['number']}"
            if article_ref not in rights_text:
                analysis_dict["rights"].append(
                    f"{article_ref} - {article['title']}"
                )

        logger.info(f"[FINISHER] ✅ analysis_data gerado")
        logger.info(f"[FINISHER]   - estimatedValue: R$ {estimated_value:.2f}")
        logger.info(f"[FINISHER]   - {len(analysis_dict['rights'])} direitos identificados")

        state["analysis_data"] = analysis_dict
        state["current_step"] = "done"

        return state

    except Exception as e:
        logger.error(f"[FINISHER] Erro ao gerar análise: {e}")

        # Fallback: usa valores calculados diretamente
        from ...conversation.schemas import AnalysisData, Recommendation, UserInfo, OpposingParty, CaseDetails

        fallback_analysis = AnalysisData(
            problem=extracted.problem_description or "Problema não especificado",
            rights=[f"CDC Art. {a['number']} - {a['title']}" for a in relevant_articles[:3]] or ["Análise não disponível"],
            estimatedValue=estimated_value,
            recommendations=[
                Recommendation(
                    type=rec["type"],
                    score=rec["score"],
                    reason=rec["reason"],
                )
                for rec in recommendations
            ],
            userInfo=UserInfo(
                name=extracted.user_full_name or "Não informado",
                cpf=extracted.user_cpf or "Não informado",
                email=extracted.user_email or "Não informado",
                phone=extracted.user_phone or "Não informado",
            ),
            opposingParty=OpposingParty(
                type="pj" if extracted.is_company else "pf",
                name=extracted.company_name or "Não informado",
            ),
            caseDetails=CaseDetails(
                title=f"Caso de {extracted.problem_category or 'consumidor'}",
                description=extracted.problem_description or "Não informado",
            ),
        )

        state["analysis_data"] = fallback_analysis.model_dump()
        state["current_step"] = "done"

        return state


async def finisher_node_with_context(state: ConversationGraphState) -> dict[str, Any]:
    """Wrapper para LangGraph."""
    from ...llm import LLMClient
    llm_client = LLMClient(primary_provider="anthropic")
    return await finisher_node(state, llm_client)
