"""
Rotas da API de conversação.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..dependencies import get_conversation_manager
from ..schemas import (
    StartConversationRequest,
    StartConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetConversationResponse,
    GetAnalysisResponse,
    MessageSchema,
)
from ...conversation import ConversationManager


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=StartConversationResponse,
    status_code=201,
    summary="Iniciar nova conversa",
    description="Cria uma nova conversa com a IA Zellu. Retorna ID da conversa para uso posterior.",
)
async def start_conversation(
    request: StartConversationRequest,
    manager: Annotated[ConversationManager, Depends(get_conversation_manager)],
) -> StartConversationResponse:
    """
    Inicia uma nova conversa.

    Args:
        request: Configurações da conversa (tom de voz)
        manager: ConversationManager injetado

    Returns:
        Dados da conversa criada
    """
    conversation_id = manager.start_conversation(tone=request.tone)
    state = manager.get_conversation(conversation_id)

    return StartConversationResponse(
        conversation_id=conversation_id,
        tone=state.tone,
        created_at=state.created_at,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    summary="Enviar mensagem",
    description="Envia uma mensagem do usuário e recebe resposta da IA. Suporta streaming via SSE.",
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    manager: Annotated[ConversationManager, Depends(get_conversation_manager)],
):
    """
    Envia mensagem para a conversa.

    Se `stream=True`, retorna Server-Sent Events (SSE) para streaming em tempo real.
    Se `stream=False`, retorna resposta completa.

    Args:
        conversation_id: ID da conversa
        request: Mensagem do usuário
        manager: ConversationManager injetado

    Returns:
        Resposta da IA (streaming ou completa)

    Raises:
        HTTPException 404: Conversa não encontrada
        HTTPException 400: Conversa já finalizada
    """
    try:
        if request.stream:
            # Streaming via SSE
            async def event_generator():
                """Gera eventos SSE."""
                try:
                    for chunk in manager.send_message_stream(
                        conversation_id, request.message
                    ):
                        yield {
                            "event": "message",
                            "data": chunk,
                        }

                    # Envia evento de finalização
                    state = manager.get_conversation(conversation_id)
                    yield {
                        "event": "done",
                        "data": {
                            "is_finalized": state.is_finalized,
                            "message_count": state.message_count,
                        },
                    }
                except ValueError as e:
                    yield {
                        "event": "error",
                        "data": {"error": str(e)},
                    }

            return EventSourceResponse(event_generator())

        else:
            # Resposta completa (non-streaming)
            response = manager.send_message(conversation_id, request.message)
            state = manager.get_conversation(conversation_id)

            return SendMessageResponse(
                conversation_id=conversation_id,
                message=response,
                is_finalized=state.is_finalized,
                message_count=state.message_count,
            )

    except ValueError as e:
        if "não encontrada" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "já foi finalizada" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{conversation_id}",
    response_model=GetConversationResponse,
    summary="Obter conversa",
    description="Retorna todos os dados da conversa (mensagens, estado, etc).",
)
async def get_conversation(
    conversation_id: str,
    manager: Annotated[ConversationManager, Depends(get_conversation_manager)],
) -> GetConversationResponse:
    """
    Obtém conversa completa.

    Args:
        conversation_id: ID da conversa
        manager: ConversationManager injetado

    Returns:
        Dados completos da conversa

    Raises:
        HTTPException 404: Conversa não encontrada
    """
    try:
        state = manager.get_conversation(conversation_id)

        return GetConversationResponse(
            conversation_id=state.conversation_id,
            tone=state.tone,
            is_finalized=state.is_finalized,
            message_count=state.message_count,
            messages=[
                MessageSchema(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                )
                for msg in state.messages
            ],
            created_at=state.created_at,
            updated_at=state.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{conversation_id}/analysis",
    response_model=GetAnalysisResponse,
    summary="Obter análise do caso",
    description="Retorna análise estruturada do caso (disponível apenas após finalização).",
)
async def get_analysis(
    conversation_id: str,
    manager: Annotated[ConversationManager, Depends(get_conversation_manager)],
) -> GetAnalysisResponse:
    """
    Obtém análise final da conversa.

    Args:
        conversation_id: ID da conversa
        manager: ConversationManager injetado

    Returns:
        Análise estruturada (se finalizada)

    Raises:
        HTTPException 404: Conversa não encontrada
    """
    try:
        state = manager.get_conversation(conversation_id)
        analysis = manager.get_analysis(conversation_id)

        return GetAnalysisResponse(
            conversation_id=conversation_id,
            is_finalized=state.is_finalized,
            analysis=analysis,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
