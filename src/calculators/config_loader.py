"""
Config Loader: Carrega regras de negócio de JSON.
Permite edição fácil por não-técnicos.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RulesConfigLoader:
    """
    Carrega e gerencia configurações de regras de negócio.

    Usage:
        config = RulesConfigLoader()
        cdc_rules = config.get_cdc_rules()
        estimator_settings = config.get_estimator_settings()
    """

    def __init__(self, config_path: str | None = None):
        """
        Inicializa loader.

        Args:
            config_path: Caminho customizado para JSON (opcional)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Path padrão: config/rules_config.json
            self.config_path = Path(__file__).parent / "config" / "rules_config.json"

        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Carrega configuração do arquivo JSON."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

            logger.info(f"[CONFIG] ✅ Regras carregadas de {self.config_path}")
            logger.info(f"[CONFIG]   - Versão: {self._config.get('version', 'unknown')}")
            logger.info(f"[CONFIG]   - CDC rules: {len(self.get_cdc_rules())}")

        except FileNotFoundError:
            logger.error(f"[CONFIG] ❌ Arquivo não encontrado: {self.config_path}")
            self._load_fallback()
        except json.JSONDecodeError as e:
            logger.error(f"[CONFIG] ❌ JSON inválido: {e}")
            self._load_fallback()
        except Exception as e:
            logger.error(f"[CONFIG] ❌ Erro ao carregar config: {e}")
            self._load_fallback()

    def _load_fallback(self) -> None:
        """Carrega regras padrão do módulo rules.py (fallback)."""
        logger.warning("[CONFIG] ⚠️ Usando fallback: rules.py")

        try:
            from .rules import (
                CDC_VALUE_RULES,
                RECOMMENDATION_BASE_SCORES,
                SCORE_MODIFIERS,
            )

            # Converte formato Python para formato JSON
            self._config = {
                "version": "1.0.0-fallback",
                "estimator_settings": {
                    "min_value": 500,
                    "max_value": 50000,
                    "bonus_multipliers": {
                        "has_documents": 1.2,
                        "multiple_violations": 1.3,
                    },
                    "multiple_violations_threshold": 3,
                },
                "cdc_value_rules": CDC_VALUE_RULES,
                "recommendation_base_scores": RECOMMENDATION_BASE_SCORES,
                "score_modifiers": SCORE_MODIFIERS,
            }

            logger.info("[CONFIG] ✅ Fallback carregado com sucesso")

        except ImportError as e:
            logger.critical(f"[CONFIG] ❌ Não foi possível carregar nem JSON nem fallback: {e}")
            raise RuntimeError("Configuração de regras indisponível") from e

    # === GETTERS ===

    def get_config_version(self) -> str:
        """Retorna versão da configuração."""
        return self._config.get("version", "unknown")

    def get_estimator_settings(self) -> Dict[str, Any]:
        """
        Retorna configurações do estimador de valores.

        Returns:
            Dict com min_value, max_value, bonus_multipliers, etc.
        """
        return self._config.get("estimator_settings", {})

    def get_cdc_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna regras de valores por artigo CDC.

        Returns:
            Dict mapeando número do artigo -> {multiplier, moral_damage_base, ...}
        """
        rules = self._config.get("cdc_value_rules", {})
        # Remove chave 'description' se presente
        return {k: v for k, v in rules.items() if k != "description"}

    def get_cdc_rule(self, article_number: str) -> Dict[str, Any] | None:
        """
        Retorna regra de um artigo específico.

        Args:
            article_number: Número do artigo (ex: "42", "71")

        Returns:
            Dict com regra ou None se não encontrado
        """
        return self.get_cdc_rules().get(article_number)

    def get_recommendation_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna scores base para recomendações.

        Returns:
            Dict com amigavel, extrajudicial, judicial
        """
        scores = self._config.get("recommendation_base_scores", {})
        # Remove chave 'description' se presente
        return {k: v for k, v in scores.items() if k != "description"}

    def get_score_modifiers(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna modificadores de score.

        Returns:
            Dict com has_documents, clear_violation, etc.
        """
        modifiers = self._config.get("score_modifiers", {})
        # Remove chave 'description' se presente
        return {k: v for k, v in modifiers.items() if k != "description"}

    def get_reason_templates(self) -> Dict[str, Any]:
        """
        Retorna templates para geração de justificativas.

        Returns:
            Dict com templates para cada tipo de recomendação
        """
        templates = self._config.get("reason_templates", {})
        # Remove chave 'description' se presente
        return {k: v for k, v in templates.items() if k != "description"}

    # === RELOAD ===

    def reload(self) -> None:
        """
        Recarrega configuração do arquivo.
        Útil para hot-reload em produção.
        """
        logger.info("[CONFIG] 🔄 Recarregando configuração...")
        self._load_config()

    # === VALIDAÇÃO ===

    def validate(self) -> bool:
        """
        Valida se configuração está completa.

        Returns:
            True se válida, False caso contrário
        """
        required_keys = [
            "estimator_settings",
            "cdc_value_rules",
            "recommendation_base_scores",
            "score_modifiers",
        ]

        for key in required_keys:
            if key not in self._config:
                logger.error(f"[CONFIG] ❌ Chave obrigatória ausente: {key}")
                return False

        # Valida estrutura CDC rules
        cdc_rules = self.get_cdc_rules()
        for article, rule in cdc_rules.items():
            if "multiplier" not in rule or "moral_damage_base" not in rule:
                logger.error(f"[CONFIG] ❌ Artigo {article} com estrutura inválida")
                return False

        logger.info("[CONFIG] ✅ Validação passou")
        return True


# === SINGLETON GLOBAL ===

_global_config: RulesConfigLoader | None = None


def get_config() -> RulesConfigLoader:
    """
    Retorna instância global do config loader (singleton).

    Returns:
        RulesConfigLoader configurado
    """
    global _global_config

    if _global_config is None:
        _global_config = RulesConfigLoader()

    return _global_config


def reload_config() -> None:
    """
    Força reload da configuração global.
    Útil para testes ou hot-reload.
    """
    global _global_config

    if _global_config:
        _global_config.reload()
    else:
        _global_config = RulesConfigLoader()
