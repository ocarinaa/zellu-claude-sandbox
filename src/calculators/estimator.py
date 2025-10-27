"""
Estimator: Calcula valor estimado do caso.
"""

from typing import List, Dict, Any
from .config_loader import get_config

import logging

logger = logging.getLogger(__name__)


class ValueEstimator:
    """
    Calcula estimatedValue baseado em artigos CDC e valores envolvidos.
    """

    def __init__(self):
        """Inicializa estimador com config loader."""
        self.config = get_config()

    def calculate(
        self,
        monetary_value: float | None,
        relevant_articles: List[Dict[str, Any]],
        has_documents: bool = False,
    ) -> float:
        """
        Calcula valor estimado.

        Args:
            monetary_value: Valor monetário envolvido (cobrado/pago)
            relevant_articles: Artigos CDC identificados pelo RAG
            has_documents: Se usuário tem documentação

        Returns:
            Valor estimado em reais
        """
        logger.info(f"[ESTIMATOR] Calculando valor para {len(relevant_articles)} artigos")

        # Carrega configurações
        cdc_rules = self.config.get_cdc_rules()
        settings = self.config.get_estimator_settings()

        total_material = 0.0
        total_moral = 0.0

        # 1. Processa cada artigo CDC
        for article_data in relevant_articles:
            article_number = article_data["number"]

            if article_number not in cdc_rules:
                logger.warning(f"[ESTIMATOR] Artigo {article_number} sem regra definida")
                continue

            rule = cdc_rules[article_number]

            # Calcula dano material (se aplicável)
            if monetary_value and monetary_value > 0:
                material_damage = monetary_value * rule["multiplier"]
                total_material += material_damage
                logger.info(f"[ESTIMATOR]   Art. {article_number}: R$ {material_damage:.2f} (material)")

            # Calcula dano moral
            moral_damage = rule["moral_damage_base"]
            total_moral += moral_damage
            logger.info(f"[ESTIMATOR]   Art. {article_number}: R$ {moral_damage:.2f} (moral)")

        # 2. Aplica modificadores (agora via config)
        bonus_multipliers = settings.get("bonus_multipliers", {})
        multiple_violations_threshold = settings.get("multiple_violations_threshold", 3)

        if has_documents:
            # Documentação aumenta chances
            doc_multiplier = bonus_multipliers.get("has_documents", 1.2)
            total_moral *= doc_multiplier
            logger.info(f"[ESTIMATOR] Bonus documentação: +{int((doc_multiplier - 1) * 100)}% moral")

        if len(relevant_articles) >= multiple_violations_threshold:
            # Múltiplas violações aumentam dano moral
            violation_multiplier = bonus_multipliers.get("multiple_violations", 1.3)
            total_moral *= violation_multiplier
            logger.info(f"[ESTIMATOR] Bonus múltiplas violações: +{int((violation_multiplier - 1) * 100)}% moral")

        # 3. Total
        estimated_value = total_material + total_moral

        # 4. Limites de sanidade (agora via config)
        min_value = settings.get("min_value", 500)
        max_value = settings.get("max_value", 50000)

        if estimated_value < min_value:
            estimated_value = min_value

        if estimated_value > max_value:
            estimated_value = max_value

        logger.info(f"[ESTIMATOR] ✅ Valor estimado: R$ {estimated_value:.2f}")
        logger.info(f"[ESTIMATOR]   - Material: R$ {total_material:.2f}")
        logger.info(f"[ESTIMATOR]   - Moral: R$ {total_moral:.2f}")

        return round(estimated_value, 2)
