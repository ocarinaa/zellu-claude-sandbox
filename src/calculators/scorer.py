"""
Scorer: Rankeia recomendações (amigável/extrajudicial/judicial).
"""

from typing import List, Dict, Any
from .rules import RECOMMENDATION_BASE_SCORES, SCORE_MODIFIERS

import logging

logger = logging.getLogger(__name__)


class RecommendationScorer:
    """
    Rankeia soluções baseado no contexto do caso.
    """

    def calculate_scores(
        self,
        relevant_articles: List[Dict[str, Any]],
        monetary_value: float | None,
        has_documents: bool,
        has_previous_attempts: bool,
    ) -> List[Dict[str, Any]]:
        """
        Calcula scores para as 3 recomendações.

        Args:
            relevant_articles: Artigos CDC identificados
            monetary_value: Valor envolvido
            has_documents: Possui documentação
            has_previous_attempts: Já tentou resolver antes

        Returns:
            Lista de 3 recomendações com scores
        """
        logger.info(f"[SCORER] Calculando scores")

        # Scores base
        scores = {
            "amigavel": RECOMMENDATION_BASE_SCORES["amigavel"]["base"],
            "extrajudicial": RECOMMENDATION_BASE_SCORES["extrajudicial"]["base"],
            "judicial": RECOMMENDATION_BASE_SCORES["judicial"]["base"],
        }

        # === APLICAR MODIFICADORES ===

        # 1. Documentos
        if has_documents:
            for solution_type, modifier in SCORE_MODIFIERS["has_documents"].items():
                scores[solution_type] += modifier
            logger.info(f"[SCORER] Modificador: possui documentos")

        # 2. Violação clara (Art. 42 ou 71)
        article_numbers = [a["number"] for a in relevant_articles]
        if "42" in article_numbers or "71" in article_numbers:
            for solution_type, modifier in SCORE_MODIFIERS["clear_violation"].items():
                scores[solution_type] += modifier
            logger.info(f"[SCORER] Modificador: violação clara (Art. 42/71)")

        # 3. Valor envolvido
        if monetary_value:
            if monetary_value < 1000:
                for solution_type, modifier in SCORE_MODIFIERS["low_value"].items():
                    scores[solution_type] += modifier
                logger.info(f"[SCORER] Modificador: valor baixo (< R$ 1.000)")
            elif monetary_value > 10000:
                for solution_type, modifier in SCORE_MODIFIERS["high_value"].items():
                    scores[solution_type] += modifier
                logger.info(f"[SCORER] Modificador: valor alto (> R$ 10.000)")

        # 4. Tentativas anteriores
        if has_previous_attempts:
            for solution_type, modifier in SCORE_MODIFIERS["previous_attempts"].items():
                scores[solution_type] += modifier
            logger.info(f"[SCORER] Modificador: tentativas anteriores")

        # 5. Múltiplas violações
        if len(relevant_articles) >= 3:
            for solution_type, modifier in SCORE_MODIFIERS["multiple_violations"].items():
                scores[solution_type] += modifier
            logger.info(f"[SCORER] Modificador: múltiplas violações")

        # === LIMITA AO MÁXIMO ===
        for solution_type in scores:
            max_score = RECOMMENDATION_BASE_SCORES[solution_type]["max"]
            if scores[solution_type] > max_score:
                scores[solution_type] = max_score

        # === GERA REASONS ===
        reasons = self._generate_reasons(
            scores,
            relevant_articles,
            monetary_value,
            has_documents,
            has_previous_attempts,
        )

        # === FORMATA OUTPUT ===
        recommendations = [
            {
                "type": "amigavel",
                "score": round(scores["amigavel"], 1),
                "reason": reasons["amigavel"],
            },
            {
                "type": "extrajudicial",
                "score": round(scores["extrajudicial"], 1),
                "reason": reasons["extrajudicial"],
            },
            {
                "type": "judicial",
                "score": round(scores["judicial"], 1),
                "reason": reasons["judicial"],
            },
        ]

        logger.info(f"[SCORER] ✅ Scores calculados:")
        for rec in recommendations:
            logger.info(f"[SCORER]   - {rec['type']}: {rec['score']}")

        return recommendations

    def _generate_reasons(
        self,
        scores: Dict[str, float],
        relevant_articles: List[Dict[str, Any]],
        monetary_value: float | None,
        has_documents: bool,
        has_previous_attempts: bool,
    ) -> Dict[str, str]:
        """
        Gera justificativas para cada score.
        """
        reasons = {}

        # Amigável
        amigavel_factors = []
        if has_documents:
            amigavel_factors.append("documentação sólida")
        if scores["amigavel"] >= 8.0:
            amigavel_factors.append("alta probabilidade de acordo rápido")
        if not has_previous_attempts:
            amigavel_factors.append("primeira tentativa de resolução")

        reasons["amigavel"] = (
            f"Recomendado: {', '.join(amigavel_factors) if amigavel_factors else 'resolução rápida e econômica'}. "
            f"Prazo estimado: 7-15 dias."
        )

        # Extrajudicial
        extrajudicial_factors = []
        if len(relevant_articles) >= 2:
            extrajudicial_factors.append("múltiplas violações CDC")
        if has_previous_attempts:
            extrajudicial_factors.append("tentativas amigáveis já realizadas")

        reasons["extrajudicial"] = (
            f"{'Recomendado caso amigável falhe' if not has_previous_attempts else 'Recomendado após tentativas prévias'}. "
            f"{', '.join(extrajudicial_factors) if extrajudicial_factors else 'Notificação formal com peso legal'}. "
            f"Prazo estimado: 20-45 dias."
        )

        # Judicial
        judicial_factors = []
        if monetary_value and monetary_value > 10000:
            judicial_factors.append("valor elevado envolvido")
        if len(relevant_articles) >= 3:
            judicial_factors.append("caso complexo com múltiplas violações")

        reasons["judicial"] = (
            f"{'Última opção' if scores['judicial'] < 7.0 else 'Viável se outras falharem'}. "
            f"{', '.join(judicial_factors) if judicial_factors else 'Processo formal com maior prazo'}. "
            f"Prazo estimado: 3-12 meses."
        )

        return reasons
