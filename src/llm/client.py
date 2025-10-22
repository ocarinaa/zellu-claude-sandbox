"""
Cliente unificado para LLMs com fallback automático.
"""

import os
import time
from typing import Iterator, Literal
from anthropic import Anthropic, APIError as AnthropicAPIError
from openai import OpenAI, APIError as OpenAIAPIError
from dotenv import load_dotenv

from .config import LLMConfig, get_config
from .exceptions import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    AllProvidersFailedError,
)

load_dotenv()


class LLMClient:
    """
    Cliente unificado para chamadas LLM com fallback automático.

    Usage:
        client = LLMClient()
        response = client.chat(messages=[...], system="...")

        # Ou com streaming
        for chunk in client.chat_stream(messages=[...]):
            print(chunk, end="")
    """

    def __init__(
        self,
        primary_provider: Literal["anthropic", "openai"] = "anthropic",
        enable_fallback: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Inicializa cliente LLM.

        Args:
            primary_provider: Provider preferencial
            enable_fallback: Se True, tenta outro provider em caso de falha
            max_retries: Tentativas por provider
            timeout: Timeout em segundos
        """
        self.primary_provider = primary_provider
        self.enable_fallback = enable_fallback
        self.max_retries = max_retries
        self.timeout = timeout

        # Inicializa clients
        self._anthropic_client = None
        self._openai_client = None
        self._init_clients()

    def _init_clients(self) -> None:
        """Inicializa clients dos providers."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if anthropic_key:
            self._anthropic_client = Anthropic(api_key=anthropic_key)

        if openai_key:
            self._openai_client = OpenAI(api_key=openai_key)

        if not self._anthropic_client and not self._openai_client:
            raise ValueError(
                "Nenhuma API key configurada. "
                "Configure ANTHROPIC_API_KEY ou OPENAI_API_KEY no .env"
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> str:
        """
        Envia mensagens para LLM e retorna resposta completa.

        Args:
            messages: Lista de mensagens [{"role": "user", "content": "..."}]
            system: System prompt (opcional)
            config: Configuração customizada (usa padrão se None)

        Returns:
            Resposta do LLM como string

        Raises:
            AllProvidersFailedError: Se todos providers falharem
        """
        if config is None:
            config = get_config(self.primary_provider)

        errors = {}

        # Tenta primary provider
        try:
            return self._call_provider(
                provider=config.provider,
                messages=messages,
                system=system,
                config=config,
            )
        except Exception as e:
            errors[config.provider] = e

        # Tenta fallback se habilitado
        if self.enable_fallback:
            fallback_provider = "openai" if config.provider == "anthropic" else "anthropic"
            fallback_config = get_config(fallback_provider)

            try:
                return self._call_provider(
                    provider=fallback_provider,
                    messages=messages,
                    system=system,
                    config=fallback_config,
                )
            except Exception as e:
                errors[fallback_provider] = e

        raise AllProvidersFailedError(errors)

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        config: LLMConfig | None = None,
    ) -> Iterator[str]:
        """
        Envia mensagens para LLM e retorna generator de chunks (streaming).

        Args:
            messages: Lista de mensagens
            system: System prompt
            config: Configuração customizada

        Yields:
            Chunks da resposta conforme vão chegando
        """
        if config is None:
            config = get_config(self.primary_provider)

        # Force streaming
        config.stream = True

        errors = {}

        # Tenta primary provider
        try:
            yield from self._call_provider_stream(
                provider=config.provider,
                messages=messages,
                system=system,
                config=config,
            )
            return
        except Exception as e:
            errors[config.provider] = e

        # Tenta fallback
        if self.enable_fallback:
            fallback_provider = "openai" if config.provider == "anthropic" else "anthropic"
            fallback_config = get_config(fallback_provider)
            fallback_config.stream = True

            try:
                yield from self._call_provider_stream(
                    provider=fallback_provider,
                    messages=messages,
                    system=system,
                    config=fallback_config,
                )
                return
            except Exception as e:
                errors[fallback_provider] = e

        raise AllProvidersFailedError(errors)

    def _call_provider(
        self,
        provider: str,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> str:
        """Chama provider específico com retry."""
        for attempt in range(self.max_retries):
            try:
                if provider == "anthropic":
                    return self._call_anthropic(messages, system, config)
                else:
                    return self._call_openai(messages, system, config)
            except (LLMRateLimitError, LLMTimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            except Exception as e:
                raise LLMProviderError(provider, e)

        raise LLMProviderError(provider, Exception("Max retries atingido"))

    def _call_provider_stream(
        self,
        provider: str,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> Iterator[str]:
        """Chama provider em modo streaming."""
        if provider == "anthropic":
            yield from self._call_anthropic_stream(messages, system, config)
        else:
            yield from self._call_openai_stream(messages, system, config)

    def _call_anthropic(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> str:
        """Chama Anthropic API."""
        if not self._anthropic_client:
            raise ValueError("Anthropic client não inicializado")

        try:
            response = self._anthropic_client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=system or "",
                messages=messages,
            )
            return response.content[0].text
        except AnthropicAPIError as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError("anthropic")
            raise

    def _call_anthropic_stream(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> Iterator[str]:
        """Chama Anthropic em streaming."""
        if not self._anthropic_client:
            raise ValueError("Anthropic client não inicializado")

        with self._anthropic_client.messages.stream(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=system or "",
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _call_openai(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> str:
        """Chama OpenAI API."""
        if not self._openai_client:
            raise ValueError("OpenAI client não inicializado")

        # Adiciona system message se fornecido
        full_messages = messages.copy()
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        try:
            response = self._openai_client.chat.completions.create(
                model=config.model,
                messages=full_messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            return response.choices[0].message.content
        except OpenAIAPIError as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError("openai")
            raise

    def _call_openai_stream(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        config: LLMConfig,
    ) -> Iterator[str]:
        """Chama OpenAI em streaming."""
        if not self._openai_client:
            raise ValueError("OpenAI client não inicializado")

        full_messages = messages.copy()
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        stream = self._openai_client.chat.completions.create(
            model=config.model,
            messages=full_messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
