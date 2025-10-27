"""
Cliente Redis assíncrono.
"""

import os
import json
from typing import Any, Optional
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisClient:
    """
    Cliente Redis assíncrono singleton.
    """

    _instance: Optional[Redis] = None

    @classmethod
    async def get_client(cls) -> Redis:
        """Retorna instância singleton do Redis."""
        if cls._instance is None:
            cls._instance = Redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Fecha conexão."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
