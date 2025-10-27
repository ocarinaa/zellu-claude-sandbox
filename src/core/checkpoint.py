"""
Checkpoint Service: Salva e recupera estado da conversa.
Previne perda de dados em caso de crash ou timeout.
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from .state import ConversationGraphState, ExtractedInfo

logger = logging.getLogger(__name__)


class CheckpointService:
    """
    Gerencia checkpoints de conversação usando Redis.

    Usage:
        checkpoint = CheckpointService()
        await checkpoint.save(chat_id, state)
        recovered_state = await checkpoint.load(chat_id)
    """

    def __init__(self, ttl: int = 86400):
        """
        Inicializa serviço de checkpoint.

        Args:
            ttl: Time-to-live em segundos (padrão: 24h)
        """
        self.ttl = ttl
        self._redis = None

    async def _get_redis(self):
        """Lazy initialization do Redis client."""
        if self._redis is None:
            from ..cache import RedisClient
            self._redis = await RedisClient.get_client()
        return self._redis

    def _generate_key(self, chat_id: str) -> str:
        """
        Gera chave Redis para checkpoint.

        Args:
            chat_id: ID da conversa

        Returns:
            Chave Redis
        """
        return f"checkpoint:{chat_id}"

    async def save(
        self,
        chat_id: str,
        state: ConversationGraphState,
        auto: bool = True,
    ) -> bool:
        """
        Salva checkpoint do estado atual.

        Args:
            chat_id: ID da conversa
            state: Estado completo do grafo
            auto: Se True, salva automaticamente; Se False, é checkpoint manual

        Returns:
            True se salvou com sucesso
        """
        try:
            redis = await self._get_redis()
            key = self._generate_key(chat_id)

            # Serializa estado
            checkpoint_data = {
                "chat_id": chat_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "auto_checkpoint": auto,
                "state": self._serialize_state(state),
            }

            # Salva no Redis
            await redis.setex(
                key,
                self.ttl,
                json.dumps(checkpoint_data, ensure_ascii=False),
            )

            checkpoint_type = "automático" if auto else "manual"
            logger.info(
                f"[CHECKPOINT] ✅ Checkpoint {checkpoint_type} salvo: {chat_id} "
                f"(turn {state.get('turn_count', 0)}, step: {state.get('current_step', 'unknown')})"
            )

            return True

        except Exception as e:
            logger.error(f"[CHECKPOINT] ❌ Erro ao salvar: {e}")
            return False

    async def load(self, chat_id: str) -> Optional[ConversationGraphState]:
        """
        Carrega checkpoint de uma conversa.

        Args:
            chat_id: ID da conversa

        Returns:
            Estado recuperado ou None se não existir
        """
        try:
            redis = await self._get_redis()
            key = self._generate_key(chat_id)

            # Busca no Redis
            data = await redis.get(key)

            if not data:
                logger.info(f"[CHECKPOINT] ℹ️ Nenhum checkpoint encontrado: {chat_id}")
                return None

            # Deserializa
            checkpoint_data = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)

            state = self._deserialize_state(checkpoint_data["state"])

            timestamp = checkpoint_data.get("timestamp", "unknown")
            logger.info(
                f"[CHECKPOINT] ✅ Checkpoint recuperado: {chat_id} "
                f"(salvo em: {timestamp}, turn: {state.get('turn_count', 0)})"
            )

            return state

        except Exception as e:
            logger.error(f"[CHECKPOINT] ❌ Erro ao carregar: {e}")
            return None

    async def delete(self, chat_id: str) -> bool:
        """
        Remove checkpoint de uma conversa.

        Args:
            chat_id: ID da conversa

        Returns:
            True se removeu com sucesso
        """
        try:
            redis = await self._get_redis()
            key = self._generate_key(chat_id)

            deleted = await redis.delete(key)

            if deleted:
                logger.info(f"[CHECKPOINT] 🗑️ Checkpoint removido: {chat_id}")
                return True
            else:
                logger.warning(f"[CHECKPOINT] ⚠️ Checkpoint não existia: {chat_id}")
                return False

        except Exception as e:
            logger.error(f"[CHECKPOINT] ❌ Erro ao deletar: {e}")
            return False

    async def exists(self, chat_id: str) -> bool:
        """
        Verifica se existe checkpoint para conversa.

        Args:
            chat_id: ID da conversa

        Returns:
            True se existe checkpoint
        """
        try:
            redis = await self._get_redis()
            key = self._generate_key(chat_id)

            return await redis.exists(key) > 0

        except Exception as e:
            logger.error(f"[CHECKPOINT] ❌ Erro ao verificar existência: {e}")
            return False

    async def list_all(self) -> list[str]:
        """
        Lista todos os checkpoints ativos.

        Returns:
            Lista de chat_ids com checkpoints
        """
        try:
            redis = await self._get_redis()

            # Busca todas chaves checkpoint:*
            keys = []
            async for key in redis.scan_iter(match="checkpoint:*"):
                # Remove prefixo "checkpoint:" (key pode ser bytes ou str)
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                chat_id = key.replace("checkpoint:", "")
                keys.append(chat_id)

            logger.info(f"[CHECKPOINT] 📋 Encontrados {len(keys)} checkpoints ativos")
            return keys

        except Exception as e:
            logger.error(f"[CHECKPOINT] ❌ Erro ao listar: {e}")
            return []

    def _serialize_state(self, state: ConversationGraphState) -> Dict[str, Any]:
        """
        Serializa estado para JSON.

        Args:
            state: Estado do grafo

        Returns:
            Dict serializável
        """
        serialized = {
            "messages": state.get("messages", []),
            "current_step": state.get("current_step", "collect"),
            "should_finish": state.get("should_finish", False),
            "tone": state.get("tone", "conciliador"),
            "chat_id": state.get("chat_id", ""),
            "user_name": state.get("user_name"),
            "turn_count": state.get("turn_count", 0),
            "relevant_cdc_articles": state.get("relevant_cdc_articles", []),
        }

        # Serializa ExtractedInfo (Pydantic model)
        extracted_info = state.get("extracted_info")
        if extracted_info:
            if hasattr(extracted_info, "model_dump"):
                serialized["extracted_info"] = extracted_info.model_dump()
            else:
                serialized["extracted_info"] = dict(extracted_info)
        else:
            serialized["extracted_info"] = {}

        # Serializa analysis_data se presente
        analysis_data = state.get("analysis_data")
        if analysis_data:
            serialized["analysis_data"] = analysis_data

        return serialized

    def _deserialize_state(self, data: Dict[str, Any]) -> ConversationGraphState:
        """
        Deserializa estado de JSON.

        Args:
            data: Dict com estado serializado

        Returns:
            Estado do grafo
        """
        # Reconstrói ExtractedInfo
        extracted_info_data = data.get("extracted_info", {})
        extracted_info = ExtractedInfo(**extracted_info_data)

        state: ConversationGraphState = {
            "messages": data.get("messages", []),
            "extracted_info": extracted_info,
            "current_step": data.get("current_step", "collect"),
            "should_finish": data.get("should_finish", False),
            "tone": data.get("tone", "conciliador"),
            "chat_id": data.get("chat_id", ""),
            "user_name": data.get("user_name"),
            "turn_count": data.get("turn_count", 0),
            "relevant_cdc_articles": data.get("relevant_cdc_articles", []),
        }

        # Adiciona analysis_data se presente
        if "analysis_data" in data:
            state["analysis_data"] = data["analysis_data"]

        return state


# === SINGLETON GLOBAL ===

_global_checkpoint: Optional[CheckpointService] = None


def get_checkpoint_service() -> CheckpointService:
    """
    Retorna instância global do checkpoint service (singleton).

    Returns:
        CheckpointService configurado
    """
    global _global_checkpoint

    if _global_checkpoint is None:
        _global_checkpoint = CheckpointService()

    return _global_checkpoint
