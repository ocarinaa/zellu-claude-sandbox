"""
Configurações de LLM (modelos, parâmetros, etc).
"""

from typing import Literal
from pydantic import BaseModel

LLMProvider = Literal["anthropic", "openai"]


class LLMConfig(BaseModel):
    """Configuração de um modelo LLM."""

    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    stream: bool = True


# Configurações padrão
CLAUDE_CONFIG = LLMConfig(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    temperature=0.7,
    max_tokens=1000,
    stream=True
)

OPENAI_CONFIG = LLMConfig(
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
    stream=True
)


def get_config(provider: LLMProvider = "anthropic") -> LLMConfig:
    """
    Retorna configuração para o provider especificado.

    Args:
        provider: "anthropic" ou "openai"

    Returns:
        LLMConfig apropriada
    """
    configs = {
        "anthropic": CLAUDE_CONFIG,
        "openai": OPENAI_CONFIG
    }
    return configs[provider]
