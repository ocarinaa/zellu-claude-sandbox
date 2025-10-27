"""
Scorer: Rankeia recomendações (amigável/extrajudicial/judicial).
"""

from typing import List, Dict, Any
from .config_loader import get_config

import logging

logger = logging.getLogger(__name__)


class RecommendationScorer:
    """
    Rankeia soluções baseado no contexto do caso.
    """

    def __init__(self):
        """Inicializa scorer com config loader."""
        self.config = get_config()

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

        # Carrega configurações
        base_scores_config = self.config.get_recommendation_scores()
        modifiers_config = self.config.get_score_modifiers()

        # Scores base
        scores = {
            "amigavel": base_scores_config["amigavel"]["base"],
            "extrajudicial": base_scores_config["extrajudicial"]["base"],
            "judicial": base_scores_config["judicial"]["base"],
        }

        # === APLICAR MODIFICADORES ===

        # 1. Documentos
        if has_documents:
            mod = modifiers_config.get("has_documents", {})
            for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                scores[solution_type] += mod.get(solution_type, 0)
            logger.info(f"[SCORER] Modificador: possui documentos")

        # 2. Violação clara (Art. 42 ou 71)
        article_numbers = [a["number"] for a in relevant_articles]
        clear_violation_mod = modifiers_config.get("clear_violation", {})
        clear_violation_articles = clear_violation_mod.get("articles", ["42", "71"])

        if any(art in article_numbers for art in clear_violation_articles):
            for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                scores[solution_type] += clear_violation_mod.get(solution_type, 0)
            logger.info(f"[SCORER] Modificador: violação clara (Art. {'/'.join(clear_violation_articles)})")

        # 3. Valor envolvido
        if monetary_value:
            low_value_mod = modifiers_config.get("low_value", {})
            high_value_mod = modifiers_config.get("high_value", {})

            low_threshold = low_value_mod.get("threshold", 1000)
            high_threshold = high_value_mod.get("threshold", 10000)

            if monetary_value < low_threshold:
                for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                    scores[solution_type] += low_value_mod.get(solution_type, 0)
                logger.info(f"[SCORER] Modificador: valor baixo (< R$ {low_threshold:,.2f})")
            elif monetary_value > high_threshold:
                for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                    scores[solution_type] += high_value_mod.get(solution_type, 0)
                logger.info(f"[SCORER] Modificador: valor alto (> R$ {high_threshold:,.2f})")

        # 4. Tentativas anteriores
        if has_previous_attempts:
            mod = modifiers_config.get("previous_attempts", {})
            for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                scores[solution_type] += mod.get(solution_type, 0)
            logger.info(f"[SCORER] Modificador: tentativas anteriores")

        # 5. Múltiplas violações
        multiple_violations_mod = modifiers_config.get("multiple_violations", {})
        multiple_threshold = multiple_violations_mod.get("threshold", 3)

        if len(relevant_articles) >= multiple_threshold:
            for solution_type in ["amigavel", "extrajudicial", "judicial"]:
                scores[solution_type] += multiple_violations_mod.get(solution_type, 0)
            logger.info(f"[SCORER] Modificador: múltiplas violações")

        # === LIMITA AO MÁXIMO ===
        for solution_type in scores:
            max_score = base_scores_config[solution_type]["max"]
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
