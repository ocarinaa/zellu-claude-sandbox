"""
ORM Models para PostgreSQL.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Conversation(Base):
    """
    Armazena conversas completas com o usuário.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    user_name = Column(String(255), nullable=True)

    # Estado da conversa
    status = Column(String(50), default="active", index=True)  # active, completed, cancelled
    is_finished = Column(Boolean, default=False, index=True)

    # Mensagens (array de objetos)
    messages = Column(JSONB, default=list, nullable=False)

    # Análise final (quando is_finished=true)
    analysis_data = Column(JSONB, nullable=True)

    # Metadata
    tone = Column(String(50), default="conciliador")  # conciliador, formal, tecnico
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Conversation(chat_id={self.chat_id}, status={self.status})>"


class Message(Base):
    """
    Armazena mensagens individuais (para consultas otimizadas).
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chat_id = Column(String(255), nullable=False, index=True)

    # Conteúdo
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)

    # Metadata
    message_type = Column(String(50), default="text")  # text, audio, file, mixed
    files = Column(JSONB, default=list)
    audio = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Message(chat_id={self.chat_id}, role={self.role})>"


class AnalysisCache(Base):
    """
    Cache de análises parciais (para otimização).
    """
    __tablename__ = "analysis_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)

    # Dados extraídos até agora
    extracted_data = Column(JSONB, default=dict)

    # Confiança (0-1)
    confidence_score = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # TTL de 24h
