"""
Analisador de documentos com IA.
"""

from typing import Dict, Any
from ..llm import LLMClient

import logging

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analisa texto extraído de documentos usando IA.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def analyze(self, document_text: str, context: str = "") -> Dict[str, Any]:
        """
        Analisa documento e extrai informações relevantes.

        Args:
            document_text: Texto extraído do documento
            context: Contexto da conversa

        Returns:
            Informações extraídas
        """
        logger.info(f"[DOC ANALYZER] Analisando documento ({len(document_text)} chars)")

        analysis_prompt = f"""Analise o documento abaixo e extraia informações relevantes.

CONTEXTO DA CONVERSA:
{context}

DOCUMENTO:
{document_text[:5000]}

Extraia e retorne em JSON:
{{
  "document_type": "comprovante | protocolo | fatura | contrato | email | outro",
  "key_information": [
    "informação relevante 1",
    "informação relevante 2"
  ],
  "monetary_values": [123.45],
  "dates": ["2024-01-15"],
  "companies_mentioned": ["Nome da Empresa"],
  "protocols": ["12345"],
  "summary": "Resumo breve do documento"
}}

Retorne APENAS o JSON válido, sem markdown."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": document_text[:3000]}],
                system=analysis_prompt,
            )

            # Parse JSON
            import json
            import re

            json_str = response.strip()
            json_str = re.sub(r'^```json\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)

            analysis = json.loads(json_str)

            logger.info(f"[DOC ANALYZER] ✅ Documento analisado: {analysis['document_type']}")

            return analysis

        except Exception as e:
            logger.error(f"[DOC ANALYZER] Erro ao analisar: {e}")
            return {
                "document_type": "unknown",
                "key_information": [],
                "summary": "Erro ao processar documento",
            }
