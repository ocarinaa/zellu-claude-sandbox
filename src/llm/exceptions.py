"""
Exceções customizadas para operações LLM.
"""

class LLMError(Exception):
    """Base exception para erros de LLM."""
    pass


class LLMProviderError(LLMError):
    """Erro específico de um provider (Anthropic/OpenAI)."""

    def __init__(self, provider: str, original_error: Exception):
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"Erro no provider {provider}: {str(original_error)}")


class LLMRateLimitError(LLMError):
    """Rate limit atingido."""

    def __init__(self, provider: str, retry_after: int | None = None):
        self.provider = provider
        self.retry_after = retry_after
        message = f"Rate limit atingido em {provider}"
        if retry_after:
            message += f". Retry após {retry_after}s"
        super().__init__(message)


class LLMTimeoutError(LLMError):
    """Timeout na requisição."""

    def __init__(self, provider: str, timeout: int):
        self.provider = provider
        self.timeout = timeout
        super().__init__(f"Timeout de {timeout}s atingido em {provider}")


class AllProvidersFailedError(LLMError):
    """Todos os providers falharam."""

    def __init__(self, errors: dict[str, Exception]):
        self.errors = errors
        providers = ", ".join(errors.keys())
        super().__init__(f"Todos providers falharam: {providers}")
