"""
Cache Redis para respostas LLM.
Economiza chamadas custosas à API.
"""

import hashlib
import json
import logging
from typing import Optional
from ..cache import RedisClient

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Cache de respostas LLM usando Redis.

    Usa hash das mensagens + system prompt como chave.
    TTL padrão: 1 hora (respostas conversacionais).
    """

    def __init__(self, ttl: int = 3600):
        """
        Args:
            ttl: Time-to-live em segundos (padrão: 1h)
        """
        self.ttl = ttl
        self._redis = None

    async def _get_redis(self):
        """Lazy initialization do Redis client."""
        if self._redis is None:
            self._redis = await RedisClient.get_client()
        return self._redis

    def _generate_cache_key(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        provider: str,
    ) -> str:
        """
        Gera chave de cache baseada no conteúdo.

        Args:
            messages: Mensagens da conversa
            system: System prompt
            provider: Provider usado (anthropic/openai)

        Returns:
            Hash MD5 como chave de cache
        """
        # Normaliza para JSON determinístico
        content = {
            "messages": messages,
            "system": system or "",
            "provider": provider,
        }

        # Gera hash
        content_str = json.dumps(content, sort_keys=True)
        hash_obj = hashlib.md5(content_str.encode())

        return f"llm_cache:{provider}:{hash_obj.hexdigest()}"

    async def get(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        provider: str,
    ) -> Optional[str]:
        """
        Busca resposta no cache.

        Returns:
            Resposta cacheada ou None se não encontrada
        """
        try:
            redis = await self._get_redis()
            cache_key = self._generate_cache_key(messages, system, provider)

            cached = await redis.get(cache_key)

            if cached:
                logger.info(f"[LLM_CACHE] ✅ HIT para {provider} (key: {cache_key[:16]}...)")
                return cached.decode('utf-8') if isinstance(cached, bytes) else cached

            logger.info(f"[LLM_CACHE] ❌ MISS para {provider}")
            return None

        except Exception as e:
            logger.error(f"[LLM_CACHE] Erro ao buscar cache: {e}")
            return None

    async def set(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        provider: str,
        response: str,
    ) -> bool:
        """
        Salva resposta no cache.

        Args:
            messages: Mensagens da conversa
            system: System prompt
            provider: Provider usado
            response: Resposta da LLM

        Returns:
            True se salvou com sucesso
        """
        try:
            redis = await self._get_redis()
            cache_key = self._generate_cache_key(messages, system, provider)

            await redis.setex(cache_key, self.ttl, response)

            logger.info(f"[LLM_CACHE] 💾 Salvo: {provider} (TTL: {self.ttl}s)")
            return True

        except Exception as e:
            logger.error(f"[LLM_CACHE] Erro ao salvar cache: {e}")
            return False

    async def clear_all(self) -> int:
        """
        Limpa todo o cache LLM (usar com cuidado).

        Returns:
            Número de chaves removidas
        """
        try:
            redis = await self._get_redis()

            # Busca todas chaves llm_cache:*
            keys = []
            async for key in redis.scan_iter(match="llm_cache:*"):
                keys.append(key)

            if keys:
                deleted = await redis.delete(*keys)
                logger.warning(f"[LLM_CACHE] 🗑️ Limpou {deleted} entradas")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"[LLM_CACHE] Erro ao limpar cache: {e}")
            return 0

    async def get_stats(self) -> dict:
        """
        Retorna estatísticas do cache.

        Returns:
            Dict com contadores
        """
        try:
            redis = await self._get_redis()

            # Conta chaves
            count = 0
            async for _ in redis.scan_iter(match="llm_cache:*"):
                count += 1

            return {
                "total_entries": count,
                "ttl_seconds": self.ttl,
            }

        except Exception as e:
            logger.error(f"[LLM_CACHE] Erro ao obter stats: {e}")
            return {"error": str(e)}
