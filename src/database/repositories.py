"""
Repository pattern para acesso aos dados.
Abstrai lógica de persistência.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .models import Conversation, Message, AnalysisCache


class ConversationRepository:
    """Repository para operações de Conversation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        chat_id: str,
        user_name: str | None = None,
        tone: str = "conciliador",
    ) -> Conversation:
        """Cria nova conversa."""
        conversation = Conversation(
            chat_id=chat_id,
            user_name=user_name,
            tone=tone,
            messages=[],
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_by_chat_id(self, chat_id: str) -> Optional[Conversation]:
        """Busca conversa por chat_id."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
    ) -> Conversation:
        """Adiciona mensagem à conversa."""
        conversation = await self.get_by_chat_id(chat_id)
        if not conversation:
            raise ValueError(f"Conversa {chat_id} não encontrada")

        # Adiciona ao array JSONB
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        messages = conversation.messages or []
        messages.append(new_message)

        conversation.messages = messages
        conversation.message_count = len(messages)
        conversation.updated_at = datetime.utcnow()

        await self.db.flush()
        return conversation

    async def finish_conversation(
        self,
        chat_id: str,
        analysis_data: dict,
    ) -> Conversation:
        """Marca conversa como finalizada e salva análise."""
        conversation = await self.get_by_chat_id(chat_id)
        if not conversation:
            raise ValueError(f"Conversa {chat_id} não encontrada")

        conversation.is_finished = True
        conversation.status = "completed"
        conversation.analysis_data = analysis_data
        conversation.finished_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        await self.db.flush()
        return conversation

    async def get_active_conversations(self, limit: int = 50) -> List[Conversation]:
        """Retorna conversas ativas (útil para admin)."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.status == "active")
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


class MessageRepository:
    """Repository para mensagens individuais."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: UUID,
        chat_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        files: list = None,
        audio: list = None,
    ) -> Message:
        """Cria nova mensagem."""
        message = Message(
            conversation_id=conversation_id,
            chat_id=chat_id,
            role=role,
            content=content,
            message_type=message_type,
            files=files or [],
            audio=audio or [],
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_by_chat_id(self, chat_id: str) -> List[Message]:
        """Retorna todas mensagens de uma conversa."""
        result = await self.db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()


class AnalysisCacheRepository:
    """Repository para cache de análises parciais."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def set(
        self,
        chat_id: str,
        extracted_data: dict,
        confidence_score: float,
        ttl_hours: int = 24,
    ) -> AnalysisCache:
        """Salva ou atualiza cache."""
        # Tenta buscar existente
        result = await self.db.execute(
            select(AnalysisCache).where(AnalysisCache.chat_id == chat_id)
        )
        cache = result.scalar_one_or_none()

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        if cache:
            cache.extracted_data = extracted_data
            cache.confidence_score = confidence_score
            cache.updated_at = datetime.utcnow()
            cache.expires_at = expires_at
        else:
            cache = AnalysisCache(
                chat_id=chat_id,
                extracted_data=extracted_data,
                confidence_score=confidence_score,
                expires_at=expires_at,
            )
            self.db.add(cache)

        await self.db.flush()
        return cache

    async def get(self, chat_id: str) -> Optional[AnalysisCache]:
        """Busca cache por chat_id."""
        result = await self.db.execute(
            select(AnalysisCache)
            .where(AnalysisCache.chat_id == chat_id)
            .where(AnalysisCache.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()

    async def delete_expired(self) -> int:
        """Deleta caches expirados. Retorna quantidade deletada."""
        result = await self.db.execute(
            delete(AnalysisCache)
            .where(AnalysisCache.expires_at <= datetime.utcnow())
        )
        return result.rowcount
