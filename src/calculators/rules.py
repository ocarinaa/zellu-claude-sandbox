"""
Regras de negócio para cálculo de valores e scores.
"""

from typing import Dict

# === VALORES BASE POR ARTIGO CDC ===

CDC_VALUE_RULES = {
    "42": {
        # Cobrança indevida → devolução em dobro
        "multiplier": 2.0,
        "moral_damage_base": 2000.0,  # Dano moral base
        "description": "Devolução em dobro + dano moral",
    },
    "6": {
        # Direitos básicos violados → dano moral
        "multiplier": 1.0,
        "moral_damage_base": 3000.0,
        "description": "Dano moral por violação de direitos",
    },
    "14": {
        # Defeito no serviço → reparação + dano material
        "multiplier": 1.5,
        "moral_damage_base": 1500.0,
        "description": "Reparação por defeito",
    },
    "18": {
        # Produto impróprio → substituição ou reembolso
        "multiplier": 1.0,
        "moral_damage_base": 1000.0,
        "description": "Produto impróprio",
    },
    "20": {
        # Vício do serviço → reembolso
        "multiplier": 1.0,
        "moral_damage_base": 1000.0,
        "description": "Vício de qualidade",
    },
    "35": {
        # Descumprimento de oferta
        "multiplier": 1.0,
        "moral_damage_base": 1500.0,
        "description": "Descumprimento de oferta",
    },
    "39": {
        # Práticas abusivas → dano moral
        "multiplier": 1.0,
        "moral_damage_base": 2500.0,
        "description": "Práticas abusivas",
    },
    "49": {
        # Direito de arrependimento → reembolso integral
        "multiplier": 1.0,
        "moral_damage_base": 500.0,
        "description": "Direito de arrependimento",
    },
    "51": {
        # Cláusula nula → restituição
        "multiplier": 1.0,
        "moral_damage_base": 2000.0,
        "description": "Cláusula abusiva",
    },
    "71": {
        # Cobrança abusiva (criminal) → dano moral alto
        "multiplier": 2.0,
        "moral_damage_base": 5000.0,
        "description": "Cobrança abusiva grave",
    },
}

# === SCORES BASE PARA RECOMENDAÇÕES ===

RECOMMENDATION_BASE_SCORES = {
    "amigavel": {
        "base": 7.0,
        "max": 10.0,
        "description": "Resolução rápida e econômica",
    },
    "extrajudicial": {
        "base": 6.0,
        "max": 9.0,
        "description": "Notificação formal com peso legal",
    },
    "judicial": {
        "base": 5.0,
        "max": 8.5,
        "description": "Ação judicial com maior prazo",
    },
}

# === FATORES QUE AUMENTAM SCORE ===

SCORE_MODIFIERS = {
    # Aumenta score amigável
    "has_documents": {
        "amigavel": +1.0,
        "extrajudicial": +0.5,
        "judicial": +0.3,
    },
    "clear_violation": {  # Artigos 42, 71 (graves)
        "amigavel": +1.5,
        "extrajudicial": +1.0,
        "judicial": +0.5,
    },
    "low_value": {  # < R$ 1.000
        "amigavel": +1.0,
        "extrajudicial": +0.3,
        "judicial": -0.5,
    },
    "high_value": {  # > R$ 10.000
        "amigavel": -0.5,
        "extrajudicial": +0.5,
        "judicial": +1.0,
    },
    "previous_attempts": {
        "amigavel": -0.5,
        "extrajudicial": +1.0,
        "judicial": +0.5,
    },
    "multiple_violations": {  # 3+ artigos
        "amigavel": -0.3,
        "extrajudicial": +0.5,
        "judicial": +1.0,
    },
}
