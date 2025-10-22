"""
Fixtures compartilhadas para testes.
"""

import pytest
import pytest_asyncio
from pathlib import Path
import asyncio

# Mock environment variables
import os
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_zellu"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from src.llm import LLMClient
from src.rag import CDCKnowledgeBase, EmbeddingGenerator, CDCVectorStore
from src.calculators import ValueEstimator, RecommendationScorer
from src.storage import LocalStorage, FileValidator
from src.core import ConversationGraphState, ExtractedInfo


@pytest.fixture
def cdc_kb():
    """Fixture: CDC Knowledge Base."""
    return CDCKnowledgeBase()


@pytest.fixture
def value_estimator():
    """Fixture: Value Estimator."""
    return ValueEstimator()


@pytest.fixture
def recommendation_scorer():
    """Fixture: Recommendation Scorer."""
    return RecommendationScorer()


@pytest.fixture
def file_validator():
    """Fixture: File Validator."""
    return FileValidator()


@pytest.fixture
def local_storage(tmp_path):
    """Fixture: Local Storage com diretório temporário."""
    return LocalStorage(base_path=str(tmp_path / "uploads"))


@pytest.fixture
def sample_conversation_state():
    """Fixture: Estado de conversa de exemplo."""
    return ConversationGraphState(
        messages=[
            {"role": "user", "content": "Fui cobrado indevidamente"},
            {"role": "assistant", "content": "Entendo. Qual empresa?"},
        ],
        extracted_info=ExtractedInfo(
            problem_description="Cobrança indevida",
            company_name="NET Claro",
            monetary_value=89.90,
        ),
        current_step="collect",
        should_finish=False,
        tone="conciliador",
        chat_id="test-123",
        user_name="João Silva",
        turn_count=1,
    )


@pytest.fixture
def sample_cdc_articles():
    """Fixture: Artigos CDC de exemplo."""
    return [
        {
            "number": "42",
            "title": "Cobrança Indevida",
            "content": "Na cobrança de débitos...",
            "similarity_score": 0.95,
        },
        {
            "number": "6",
            "title": "Direitos Básicos",
            "content": "São direitos básicos...",
            "similarity_score": 0.85,
        },
    ]


# Async fixtures
@pytest_asyncio.fixture
async def llm_client_mock():
    """Fixture: Mock LLM Client."""

    class MockLLMClient:
        async def chat(self, messages, system=None):
            return "Resposta mockada do LLM"

        async def chat_stream(self, messages, system=None):
            async def stream():
                for chunk in ["Resposta ", "mockada ", "do ", "LLM"]:
                    yield chunk

            async for chunk in stream():
                yield chunk

    return MockLLMClient()


# Event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
