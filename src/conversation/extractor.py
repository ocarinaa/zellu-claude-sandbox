"""
Extrai AnalysisData de resposta JSON do LLM.
"""

import json
import re
from typing import Optional
from .schemas import AnalysisData
import logging

logger = logging.getLogger(__name__)


def extract_analysis_data(llm_response: str) -> AnalysisData:
    """
    Extrai AnalysisData estruturado de resposta do LLM.

    O LLM pode retornar:
    1. JSON puro
    2. JSON dentro de markdown code blocks
    3. Texto com JSON embutido

    Args:
        llm_response: Resposta bruta do LLM

    Returns:
        AnalysisData validado

    Raises:
        ValueError: Se não conseguir extrair JSON válido
    """
    try:
        # Remove espaços em branco
        response = llm_response.strip()

        # Remove markdown code blocks se existirem
        if response.startswith("```"):
            # Remove ```json ou ```
            lines = response.split("\n")
            # Remove primeira linha (```json) e última (```)
            if len(lines) >= 3:
                response = "\n".join(lines[1:-1])

        # Tenta encontrar JSON com regex (fallback)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group(0)

        # Parse JSON
        data = json.loads(response)

        # Valida com Pydantic
        analysis = AnalysisData(**data)

        logger.info(f"✅ AnalysisData extraído com sucesso")
        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao fazer parse do JSON: {e}")
        logger.error(f"Resposta recebida: {llm_response[:200]}...")

        # Retorna análise com valores padrão
        return _get_fallback_analysis()

    except Exception as e:
        logger.error(f"❌ Erro ao validar AnalysisData: {e}")
        logger.error(f"Data recebida: {data if 'data' in locals() else 'N/A'}")

        # Retorna análise com valores padrão
        return _get_fallback_analysis()


def _get_fallback_analysis() -> AnalysisData:
    """
    Retorna AnalysisData com valores padrão quando extração falha.
    """
    from .schemas import UserInfo, OpposingParty, CaseDetails, Recommendation

    logger.warning("⚠️ Usando análise fallback (valores padrão)")

    return AnalysisData(
        problem="Erro ao extrair análise. Revise o histórico manualmente.",
        rights=["Direitos do consumidor (CDC)"],
        estimatedValue=1000.0,
        recommendations=[
            Recommendation(
                type="amigavel",
                score=5.0,
                reason="Análise incompleta - revisar manualmente",
            ),
            Recommendation(
                type="extrajudicial",
                score=5.0,
                reason="Análise incompleta - revisar manualmente",
            ),
            Recommendation(
                type="judicial",
                score=5.0,
                reason="Análise incompleta - revisar manualmente",
            ),
        ],
        userInfo=UserInfo(),
        opposingParty=OpposingParty(),
        caseDetails=CaseDetails(),
    )
