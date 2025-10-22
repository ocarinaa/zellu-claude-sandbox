"""
Cache de sessões ativas com Redis.
"""

from typing import Optional, Any
import json
from .redis_client import RedisClient


class SessionCache:
    """
    Gerencia cache de sessões de conversa no Redis.
    """

    def __init__(self):
        self.prefix = "session:"
        self.default_ttl = 3600  # 1 hora

    async def set(
        self,
        chat_id: str,
        data: dict,
        ttl: int | None = None,
    ) -> bool:
        """
        Salva sessão no cache.

        Args:
            chat_id: ID da conversa
            data: Dados da sessão (serializável em JSON)
            ttl: Time-to-live em segundos (padrão: 1h)

        Returns:
            True se sucesso
        """
        redis = await RedisClient.get_client()
        key = f"{self.prefix}{chat_id}"
        value = json.dumps(data)

        return await redis.set(
            key,
            value,
            ex=ttl or self.default_ttl,
        )

    async def get(self, chat_id: str) -> Optional[dict]:
        """
        Busca sessão no cache.

        Args:
            chat_id: ID da conversa

        Returns:
            Dados da sessão ou None se não encontrado
        """
        redis = await RedisClient.get_client()
        key = f"{self.prefix}{chat_id}"
        value = await redis.get(key)

        if value:
            return json.loads(value)
        return None

    async def delete(self, chat_id: str) -> bool:
        """Remove sessão do cache."""
        redis = await RedisClient.get_client()
        key = f"{self.prefix}{chat_id}"
        return await redis.delete(key) > 0

    async def exists(self, chat_id: str) -> bool:
        """Verifica se sessão existe no cache."""
        redis = await RedisClient.get_client()
        key = f"{self.prefix}{chat_id}"
        return await redis.exists(key) > 0

    async def extend_ttl(self, chat_id: str, ttl: int | None = None) -> bool:
        """Estende TTL de uma sessão."""
        redis = await RedisClient.get_client()
        key = f"{self.prefix}{chat_id}"
        return await redis.expire(key, ttl or self.default_ttl)
