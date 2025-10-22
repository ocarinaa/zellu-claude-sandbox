"""
Estimator: Calcula valor estimado do caso.
"""

from typing import List, Dict, Any
from .rules import CDC_VALUE_RULES

import logging

logger = logging.getLogger(__name__)


class ValueEstimator:
    """
    Calcula estimatedValue baseado em artigos CDC e valores envolvidos.
    """

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

        total_material = 0.0
        total_moral = 0.0

        # 1. Processa cada artigo CDC
        for article_data in relevant_articles:
            article_number = article_data["number"]

            if article_number not in CDC_VALUE_RULES:
                logger.warning(f"[ESTIMATOR] Artigo {article_number} sem regra definida")
                continue

            rule = CDC_VALUE_RULES[article_number]

            # Calcula dano material (se aplicável)
            if monetary_value and monetary_value > 0:
                material_damage = monetary_value * rule["multiplier"]
                total_material += material_damage
                logger.info(f"[ESTIMATOR]   Art. {article_number}: R$ {material_damage:.2f} (material)")

            # Calcula dano moral
            moral_damage = rule["moral_damage_base"]
            total_moral += moral_damage
            logger.info(f"[ESTIMATOR]   Art. {article_number}: R$ {moral_damage:.2f} (moral)")

        # 2. Aplica modificadores
        if has_documents:
            # Documentação aumenta chances, eleva dano moral em 20%
            total_moral *= 1.2
            logger.info(f"[ESTIMATOR] Bonus documentação: +20% moral")

        if len(relevant_articles) >= 3:
            # Múltiplas violações aumentam dano moral
            total_moral *= 1.3
            logger.info(f"[ESTIMATOR] Bonus múltiplas violações: +30% moral")

        # 3. Total
        estimated_value = total_material + total_moral

        # 4. Limites de sanidade
        if estimated_value < 500:
            estimated_value = 500  # Mínimo razoável

        if estimated_value > 50000:
            estimated_value = 50000  # Cap para casos comuns

        logger.info(f"[ESTIMATOR] ✅ Valor estimado: R$ {estimated_value:.2f}")
        logger.info(f"[ESTIMATOR]   - Material: R$ {total_material:.2f}")
        logger.info(f"[ESTIMATOR]   - Moral: R$ {total_moral:.2f}")

        return round(estimated_value, 2)
