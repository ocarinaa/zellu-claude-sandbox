"""
Setup de conexão assíncrona e síncrona com PostgreSQL.
"""

import os
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

from .models import Base

load_dotenv()

# Database URL (async)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/zellu_ia"
)

# Database URL (sync) - tenta carregar do .env ou converte da async
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
)

# Engine assíncrono
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True para debug
    poolclass=NullPool,  # Usar NullPool para desenvolvimento
    future=True,
)

# Engine síncrono (lazy - só cria quando necessário)
_engine_sync = None

def get_sync_engine():
    """Retorna engine síncrono, criando-o se necessário."""
    global _engine_sync
    if _engine_sync is None:
        _engine_sync = create_engine(
            DATABASE_URL_SYNC,
            echo=False,
            poolclass=NullPool,
            future=True,
        )
    return _engine_sync

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Session factory síncrona (lazy - para tickets)
_SessionLocal = None

def get_session_factory():
    """Retorna sessionmaker síncrono, criando-o se necessário."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            get_sync_engine(),
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


async def init_db() -> None:
    """
    Inicializa o banco de dados (cria tabelas).
    USE APENAS EM DESENVOLVIMENTO. Em produção, use Alembic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para FastAPI obter sessão do banco (async).

    Usage:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI obter sessão do banco (sync).

    Usage:
        @app.get("/example")
        def example(db: Session = Depends(get_db_session)):
            ...
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
