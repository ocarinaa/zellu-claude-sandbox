"""Módulo de configurações e clients LLM."""

from .config import LLMConfig, LLMProvider, get_config, CLAUDE_CONFIG, OPENAI_CONFIG
from .client import LLMClient
from .exceptions import (
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    AllProvidersFailedError,
)

__all__ = [
    # Config
    "LLMConfig",
    "LLMProvider",
    "get_config",
    "CLAUDE_CONFIG",
    "OPENAI_CONFIG",
    # Client
    "LLMClient",
    # Exceptions
    "LLMError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "AllProvidersFailedError",
]
