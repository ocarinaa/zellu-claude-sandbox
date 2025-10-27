"""
Testes para RulesConfigLoader.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.calculators.config_loader import RulesConfigLoader, get_config


def test_load_default_config():
    """Testa carregamento do config padrão."""
    config = RulesConfigLoader()

    # Verifica se carregou
    assert config.get_config_version() is not None

    # Verifica estruturas principais
    assert len(config.get_cdc_rules()) > 0
    assert len(config.get_recommendation_scores()) == 3
    assert len(config.get_score_modifiers()) > 0


def test_get_cdc_rule():
    """Testa busca de regra específica."""
    config = RulesConfigLoader()

    # Busca artigo existente
    rule_42 = config.get_cdc_rule("42")
    assert rule_42 is not None
    assert "multiplier" in rule_42
    assert "moral_damage_base" in rule_42
    assert rule_42["multiplier"] == 2.0

    # Busca artigo inexistente
    rule_999 = config.get_cdc_rule("999")
    assert rule_999 is None


def test_estimator_settings():
    """Testa configurações do estimador."""
    config = RulesConfigLoader()

    settings = config.get_estimator_settings()

    assert "min_value" in settings
    assert "max_value" in settings
    assert "bonus_multipliers" in settings

    assert settings["min_value"] == 1000
    assert settings["max_value"] == 80000


def test_recommendation_scores():
    """Testa scores de recomendações."""
    config = RulesConfigLoader()

    scores = config.get_recommendation_scores()

    assert "amigavel" in scores
    assert "extrajudicial" in scores
    assert "judicial" in scores

    # Verifica estrutura
    for solution_type, data in scores.items():
        assert "base" in data
        assert "max" in data
        assert data["base"] < data["max"]


def test_score_modifiers():
    """Testa modificadores de score."""
    config = RulesConfigLoader()

    modifiers = config.get_score_modifiers()

    assert "has_documents" in modifiers
    assert "clear_violation" in modifiers
    assert "low_value" in modifiers
    assert "high_value" in modifiers

    # Verifica que modificadores têm valores para cada tipo
    docs_mod = modifiers["has_documents"]
    assert "amigavel" in docs_mod
    assert "extrajudicial" in docs_mod
    assert "judicial" in docs_mod


def test_custom_config_path():
    """Testa carregamento de config customizado."""
    # Cria config temporário
    temp_config = {
        "version": "test-1.0.0",
        "estimator_settings": {
            "min_value": 100,
            "max_value": 10000,
            "bonus_multipliers": {"has_documents": 1.5},
            "multiple_violations_threshold": 2,
        },
        "cdc_value_rules": {
            "42": {
                "multiplier": 3.0,
                "moral_damage_base": 5000.0,
                "description": "Test rule",
            }
        },
        "recommendation_base_scores": {
            "amigavel": {"base": 8.0, "max": 10.0},
            "extrajudicial": {"base": 7.0, "max": 9.0},
            "judicial": {"base": 6.0, "max": 8.0},
        },
        "score_modifiers": {
            "has_documents": {
                "amigavel": 2.0,
                "extrajudicial": 1.0,
                "judicial": 0.5,
            }
        },
    }

    # Salva em arquivo temporário
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(temp_config, f)
        temp_path = f.name

    try:
        # Carrega config customizado
        config = RulesConfigLoader(config_path=temp_path)

        assert config.get_config_version() == "test-1.0.0"
        assert config.get_estimator_settings()["min_value"] == 100
        assert config.get_cdc_rule("42")["multiplier"] == 3.0

    finally:
        # Limpa arquivo temporário
        Path(temp_path).unlink()


def test_fallback_on_missing_file():
    """Testa fallback para rules.py quando JSON não existe."""
    # Tenta carregar arquivo inexistente
    config = RulesConfigLoader(config_path="/path/that/does/not/exist.json")

    # Deve usar fallback
    assert config.get_config_version() == "1.0.0-fallback"

    # Mas ainda deve ter regras
    assert len(config.get_cdc_rules()) > 0
    assert config.get_cdc_rule("42") is not None


def test_fallback_on_invalid_json():
    """Testa fallback quando JSON é inválido."""
    # Cria arquivo com JSON inválido
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{invalid json here}")
        temp_path = f.name

    try:
        config = RulesConfigLoader(config_path=temp_path)

        # Deve usar fallback
        assert config.get_config_version() == "1.0.0-fallback"

        # Mas ainda funciona
        assert len(config.get_cdc_rules()) > 0

    finally:
        Path(temp_path).unlink()


def test_validate():
    """Testa validação de config."""
    config = RulesConfigLoader()

    # Config padrão deve ser válido
    assert config.validate() is True


def test_singleton_get_config():
    """Testa que get_config() retorna singleton."""
    config1 = get_config()
    config2 = get_config()

    # Deve ser a mesma instância
    assert config1 is config2


def test_reason_templates():
    """Testa templates de justificativas."""
    config = RulesConfigLoader()

    templates = config.get_reason_templates()

    assert "amigavel" in templates
    assert "extrajudicial" in templates
    assert "judicial" in templates

    # Verifica estrutura
    for solution_type, data in templates.items():
        assert "factors" in data or "default" in data


@pytest.mark.parametrize("article_number,expected_multiplier", [
    ("42", 2.0),
    ("6", 1.0),
    ("14", 1.5),
    ("71", 2.5),  # Atualizado - cobrança abusiva criminal tem multiplier maior
])
def test_cdc_rules_multipliers(article_number, expected_multiplier):
    """Testa multipliers específicos de artigos."""
    config = RulesConfigLoader()

    rule = config.get_cdc_rule(article_number)
    assert rule is not None
    assert rule["multiplier"] == expected_multiplier


@pytest.mark.parametrize("article_number,min_moral_damage", [
    ("42", 5000.0),  # Atualizado com jurisprudência STJ REsp 1.737.428
    ("6", 7000.0),   # Atualizado com jurisprudência STJ REsp 1.651.893
    ("71", 12000.0), # Atualizado com jurisprudência STJ REsp 1.753.069
])
def test_cdc_rules_moral_damage(article_number, min_moral_damage):
    """Testa valores de dano moral baseados em jurisprudência."""
    config = RulesConfigLoader()

    rule = config.get_cdc_rule(article_number)
    assert rule is not None
    assert rule["moral_damage_base"] == min_moral_damage
