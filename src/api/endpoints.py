"""
Endpoints REST com persistência.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import logging
import mimetypes

from ..database import get_db, ConversationRepository, MessageRepository, AnalysisCacheRepository
from ..cache import SessionCache
from ..llm import LLMClient
from ..conversation import ConversationManager
from ..storage import LocalStorage, FileValidator
from ..ocr import PDFExtractor, ImageOCR, DocumentAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


# === SCHEMAS ===

from pydantic import BaseModel, Field
from typing import Optional
from ..conversation.schemas import Message, AnalysisData, ToneType


class ChatRequest(BaseModel):
    """Request para enviar mensagem."""
    chat_id: str = Field(..., description="ID único da conversa")
    message: str = Field(..., description="Mensagem do usuário")
    user_name: Optional[str] = Field(None, description="Nome do usuário")
    tone: ToneType = Field("conciliador", description="Tom da conversa")


class ChatResponse(BaseModel):
    """Response com mensagem da IA."""
    chat_id: str
    message: str
    is_finished: bool = False
    analysis_data: Optional[AnalysisData] = None


class ConversationHistoryResponse(BaseModel):
    """Response com histórico completo."""
    chat_id: str
    user_name: Optional[str] = None
    messages: List[Message]
    tone: str
    is_finished: bool
    analysis_data: Optional[AnalysisData] = None
    message_count: int


class HealthResponse(BaseModel):
    """Response de health check."""
    status: str
    database: str
    redis: str


# === DEPENDENCIES ===

def get_llm_client() -> LLMClient:
    """Dependency: LLM Client."""
    return LLMClient(primary_provider="anthropic", enable_fallback=True)


def get_session_cache() -> SessionCache:
    """Dependency: Session Cache."""
    return SessionCache()


async def get_conversation_manager(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    session_cache: SessionCache = Depends(get_session_cache),
) -> ConversationManager:
    """Dependency: Conversation Manager com persistência."""
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    cache_repo = AnalysisCacheRepository(db)

    return ConversationManager(
        llm_client=llm_client,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        cache_repo=cache_repo,
        session_cache=session_cache,
    )


def get_storage() -> LocalStorage:
    """Dependency: Local Storage."""
    return LocalStorage()


# === ENDPOINTS ===

@router.post("/upload")
async def upload_file(
    chat_id: str,
    file: UploadFile = File(...),
    storage: LocalStorage = Depends(get_storage),
    manager: ConversationManager = Depends(get_conversation_manager),
):
    """
    Upload de arquivo para análise.

    Args:
        chat_id: ID da conversa
        file: Arquivo enviado
        storage: Storage local
        manager: Conversation Manager
    """
    try:
        logger.info(f"[UPLOAD] Recebendo arquivo: {file.filename}")

        # 1. Lê conteúdo
        content = await file.read()

        # 2. Valida
        is_valid, error = FileValidator.validate(file.filename, content)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

        # 3. Sanitiza nome
        safe_name = FileValidator.sanitize_filename(file.filename)

        # 4. Salva
        relative_path = await storage.save(safe_name, content, chat_id)
        full_path = storage.get_full_path(relative_path)

        # 5. Extrai texto (se aplicável)
        mime_type = mimetypes.guess_type(file.filename)[0] or ""
        extracted_text = ""

        if mime_type == "application/pdf":
            extracted_text = await PDFExtractor.extract_text(full_path)
        elif mime_type.startswith("image/"):
            extracted_text = await ImageOCR.extract_text(full_path)

        # 6. Analisa com IA (se extraiu texto)
        analysis = None
        if extracted_text:
            llm_client = get_llm_client()
            analyzer = DocumentAnalyzer(llm_client)

            # Busca contexto da conversa
            state = await manager.start_conversation(chat_id)
            context = "\n".join([f"{m.role}: {m.content}" for m in state.messages[-5:]])

            analysis = await analyzer.analyze(extracted_text, context)

        # 7. Adiciona ao state (via mensagem especial)
        document_summary = f"📄 Documento enviado: {safe_name}\n"
        if analysis:
            document_summary += f"Tipo: {analysis['document_type']}\n"
            document_summary += f"Resumo: {analysis['summary']}\n"
            if analysis.get('key_information'):
                document_summary += "Informações relevantes:\n"
                for info in analysis['key_information'][:3]:
                    document_summary += f"  • {info}\n"

        await manager.add_user_message(chat_id, document_summary)

        logger.info(f"[UPLOAD] ✅ Arquivo processado: {safe_name}")

        return {
            "success": True,
            "filename": safe_name,
            "path": relative_path,
            "size": len(content),
            "mime_type": mime_type,
            "extracted_text_length": len(extracted_text) if extracted_text else 0,
            "analysis": analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPLOAD] Erro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}",
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    manager: ConversationManager = Depends(get_conversation_manager),
):
    """
    Envia mensagem e recebe resposta (síncrono).
    """
    try:
        response = await manager.generate_response(
            chat_id=request.chat_id,
            user_message=request.message,
        )

        should_finish = await manager.should_finish(request.chat_id)

        analysis = None
        if should_finish:
            analysis = await manager.finish_conversation(request.chat_id)

        return ChatResponse(
            chat_id=request.chat_id,
            message=response,
            is_finished=should_finish,
            analysis_data=analysis,
        )

    except Exception as e:
        logger.error(f"[ERROR] Chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    manager: ConversationManager = Depends(get_conversation_manager),
):
    """
    Envia mensagem e recebe resposta em streaming (SSE).
    """
    async def event_generator():
        try:
            async for chunk in manager.generate_response_stream(
                chat_id=request.chat_id,
                user_message=request.message,
            ):
                yield f"data: {chunk}\n\n"

            should_finish = await manager.should_finish(request.chat_id)
            if should_finish:
                analysis = await manager.finish_conversation(request.chat_id)
                yield f"data: [ANALYSIS]{json.dumps(analysis.model_dump())}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[ERROR] Streaming: {e}")
            yield f"data: [ERROR]{str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/conversations/{chat_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    chat_id: str,
    manager: ConversationManager = Depends(get_conversation_manager),
):
    """
    Busca histórico completo de uma conversa.
    """
    history = await manager.get_conversation_history(chat_id)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversa {chat_id} não encontrada",
        )

    return ConversationHistoryResponse(
        chat_id=history.conversation_id,
        user_name=None,  # TODO: adicionar user_name no ConversationState
        messages=history.messages,
        tone=history.tone,
        is_finished=history.is_finalized,
        analysis_data=history.analysis_data,
        message_count=len(history.messages),
    )


@router.get("/conversations", response_model=List[ConversationHistoryResponse])
async def list_conversations(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista conversas ativas (admin/debug).
    """
    repo = ConversationRepository(db)
    conversations = await repo.get_active_conversations(limit=limit)

    return [
        ConversationHistoryResponse(
            chat_id=conv.chat_id,
            user_name=conv.user_name,
            messages=[],
            tone=conv.tone,
            is_finished=conv.is_finished,
            analysis_data=None,
            message_count=conv.message_count,
        )
        for conv in conversations
    ]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    session_cache: SessionCache = Depends(get_session_cache),
):
    """
    Verifica saúde da API, DB e Redis.
    """
    health = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    # Testa PostgreSQL
    try:
        await db.execute("SELECT 1")
        health["database"] = "healthy"
    except Exception as e:
        logger.error(f"[HEALTH] DB failed: {e}")
        health["database"] = "unhealthy"
        health["status"] = "degraded"

    # Testa Redis
    try:
        from ..cache import RedisClient
        redis = await RedisClient.get_client()
        await redis.ping()
        health["redis"] = "healthy"
    except Exception as e:
        logger.error(f"[HEALTH] Redis failed: {e}")
        health["redis"] = "unhealthy"
        health["status"] = "degraded"

    return HealthResponse(**health)
