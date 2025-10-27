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


class Ticket(Base):
    """
    Sistema de tickets para gerenciamento de casos.
    Criado automaticamente quando análise é finalizada.
    """
    __tablename__ = "tickets"

    # Identificação
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(Integer, unique=True, nullable=False, index=True, autoincrement=True)
    chat_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Status e prioridade
    status = Column(
        String(50),
        default="novo",
        nullable=False,
        index=True
    )  # novo, em_analise, aguardando_cliente, resolvido, arquivado

    priority = Column(
        String(50),
        default="media",
        nullable=False,
        index=True
    )  # baixa, media, alta, urgente

    # Atribuição
    assigned_to = Column(String(255), nullable=True, index=True)  # Email/ID do advogado
    assigned_at = Column(DateTime, nullable=True)

    # Dados do usuário (extraídos da análise)
    user_name = Column(String(255), nullable=True)
    user_cpf = Column(String(14), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_phone = Column(String(20), nullable=True)

    # Dados do caso
    company_name = Column(String(255), nullable=True, index=True)
    problem_description = Column(Text, nullable=True)
    monetary_value = Column(Float, default=0.0)
    estimated_value = Column(Float, default=0.0)

    # Análise completa (JSON com todos os detalhes)
    analysis_data = Column(JSONB, nullable=False)

    # Recomendação principal
    recommended_approach = Column(String(50), nullable=True)  # amigavel, extrajudicial, judicial
    recommended_score = Column(Float, default=0.0)

    # Artigos CDC aplicáveis
    cdc_articles = Column(JSONB, default=list)  # Lista de artigos relevantes

    # Documentos anexados
    has_documents = Column(Boolean, default=False)
    documents = Column(JSONB, default=list)  # URLs dos documentos

    # Notas e observações
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, default=list)  # Tags para organização

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Ticket(number={self.ticket_number}, status={self.status}, priority={self.priority})>"
