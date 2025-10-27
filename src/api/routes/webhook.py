"""
API Route: Webhook para integração com Zellu App.
Recebe mensagens do frontend e processa com IA.
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Literal, Optional
import httpx
import logging
import os

from ...core import create_conversation_graph, ConversationGraphState, ExtractedInfo
from ...llm import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS - REQUEST (Zellu → Nossa IA)
# ═══════════════════════════════════════════════════════════════

class WebhookRequest(BaseModel):
    """Payload recebido do Zellu App."""
    id: str = Field(..., description="UUID da mensagem")
    chat_id: str = Field(..., description="UUID da sessão de chat")
    nome: str = Field(..., description="Nome do usuário")
    message_type: Literal["text", "audio", "file", "mixed"]
    body_message: str = Field(..., description="Texto da mensagem")
    audio: Optional[list[str]] = Field(default=None, description="URLs de áudios")
    files: list[str] = Field(default_factory=list, description="URLs de arquivos")


# ═══════════════════════════════════════════════════════════════
# SCHEMAS - RESPONSE (Nossa IA → Zellu)
# ═══════════════════════════════════════════════════════════════

class RecommendationResponse(BaseModel):
    """Recomendação de solução."""
    type: Literal["amigavel", "extrajudicial", "judicial"]
    score: float = Field(..., ge=0, le=10)
    reason: str


class UserInfoResponse(BaseModel):
    """Informações do usuário."""
    name: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class OpposingPartyResponse(BaseModel):
    """Parte contrária."""
    type: Literal["pf", "pj"]
    name: Optional[str] = None
    document: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CaseDetailsResponse(BaseModel):
    """Detalhes do caso."""
    title: Optional[str] = None
    description: Optional[str] = None
    expectedSolution: Optional[str] = None
    documents: list[str] = Field(default_factory=list)


class AnalysisDataResponse(BaseModel):
    """Dados da análise completa."""
    problem: str
    rights: list[str] = Field(..., min_items=1)
    estimatedValue: float = Field(..., gt=0)
    recommendations: list[RecommendationResponse] = Field(..., min_items=3, max_items=3)
    userInfo: Optional[UserInfoResponse] = None
    opposingParty: Optional[OpposingPartyResponse] = None
    caseDetails: Optional[CaseDetailsResponse] = None


class WebhookResponse(BaseModel):
    """Resposta enviada de volta ao Zellu."""
    chat_id: str
    message: str
    is_finished: bool
    message_type: str = "text"
    files: list[str] = Field(default_factory=list)
    audio: Optional[str] = None
    analysis_data: Optional[AnalysisDataResponse] = None


# ═══════════════════════════════════════════════════════════════
# ENDPOINT - POST /webhook/chat
# ═══════════════════════════════════════════════════════════════

@router.post("/chat")
async def process_chat_message(
    request: WebhookRequest,
    background_tasks: BackgroundTasks,
):
    """
    Webhook principal: Recebe mensagem do Zellu e processa com IA.

    Fluxo:
    1. Recebe mensagem do usuário
    2. Processa com LangGraph (coleta → validação → análise)
    3. Retorna resposta intermediária OU análise final
    4. Envia callback ao Zellu em background
    """
    logger.info(f"[WEBHOOK] Recebida mensagem do chat_id: {request.chat_id}")
    logger.info(f"[WEBHOOK] Tipo: {request.message_type}, Usuário: {request.nome}")

    try:
        # ─────────────────────────────────────────────────────────
        # 1. RECUPERA OU CRIA ESTADO DA CONVERSA
        # ─────────────────────────────────────────────────────────

        # TODO: Integrar com checkpoint para recuperar estado existente
        # Por enquanto, cria estado novo a cada mensagem

        from ...core.checkpoint import get_checkpoint_service
        checkpoint = get_checkpoint_service()

        # Tenta recuperar estado existente
        state = await checkpoint.load(request.chat_id)

        if state is None:
            # Primeira mensagem da conversa - cria estado novo
            logger.info(f"[WEBHOOK] Nova conversa iniciada: {request.chat_id}")
            state: ConversationGraphState = {
                "messages": [],
                "extracted_info": ExtractedInfo(),
                "current_step": "collect",
                "should_finish": False,
                "tone": "conciliador",
                "chat_id": request.chat_id,
                "user_name": request.nome,
                "turn_count": 0,
                "relevant_cdc_articles": [],
            }
        else:
            logger.info(f"[WEBHOOK] Conversa recuperada: {request.chat_id} (turn {state['turn_count']})")

        # ─────────────────────────────────────────────────────────
        # 2. ADICIONA MENSAGEM DO USUÁRIO AO ESTADO
        # ─────────────────────────────────────────────────────────

        state["messages"].append({
            "role": "user",
            "content": request.body_message,
        })

        # ─────────────────────────────────────────────────────────
        # 3. PROCESSA COM LANGGRAPH
        # ─────────────────────────────────────────────────────────

        logger.info(f"[WEBHOOK] Processando com LangGraph...")

        # Cria cliente LLM (usa OpenAI se Anthropic não disponível)
        llm_client = LLMClient(primary_provider="openai")

        # Processa com collector node
        from ...core.nodes import collector_node
        state = await collector_node(state, llm_client)

        # Pega última resposta da IA
        last_message = state["messages"][-1]["content"]

        # ─────────────────────────────────────────────────────────
        # 4. DECIDE SE DEVE FINALIZAR
        # ─────────────────────────────────────────────────────────

        confidence = state["extracted_info"].confidence_score
        is_finished = confidence >= 0.8 and state["turn_count"] >= 3

        logger.info(f"[WEBHOOK] Confiança: {confidence:.0%}, Finalizar: {is_finished}")

        # ─────────────────────────────────────────────────────────
        # 5. SE FINALIZAR, GERA ANÁLISE COMPLETA
        # ─────────────────────────────────────────────────────────

        analysis_data = None

        if is_finished:
            logger.info(f"[WEBHOOK] Gerando análise final...")

            # Busca artigos CDC
            from ...rag.retriever import initialize_cdc_retriever
            retriever = await initialize_cdc_retriever()
            results = await retriever.retrieve(
                query=state["extracted_info"].problem_description or request.body_message,
                top_k=5
            )

            # Formata resultados para o formato esperado
            relevant_articles = []
            for article, score in results:
                relevant_articles.append({
                    "number": article.number,
                    "title": article.title,
                    "content": article.content,
                    "similarity_score": float(score),
                })

            state["relevant_cdc_articles"] = relevant_articles

            # Processa com finisher node
            from ...core.nodes import finisher_node
            state = await finisher_node(state, llm_client)

            # Extrai analysis_data
            if "analysis_data" in state and state["analysis_data"]:
                analysis_data = AnalysisDataResponse(**state["analysis_data"])
                logger.info(f"[WEBHOOK] ✅ Análise completa gerada!")

                # ─────────────────────────────────────────────────────
                # 5.1. CRIA TICKET AUTOMATICAMENTE
                # ─────────────────────────────────────────────────────
                try:
                    from ...tickets.service import TicketService
                    from ...database import SessionLocal

                    # Cria sessão síncrona do banco
                    db_session = SessionLocal()
                    try:
                        ticket_service = TicketService(db_session)

                        # Cria ticket
                        ticket = ticket_service.create_ticket_from_analysis(
                            chat_id=request.chat_id,
                            analysis_data=state["analysis_data"],
                            conversation_id=None  # Pode vincular se tiver ID da conversa
                        )

                        logger.info(f"[WEBHOOK] 🎫 Ticket #{ticket.ticket_number} criado automaticamente!")

                        # Salva ticket_number no state para referência
                        state["ticket_number"] = ticket.ticket_number

                    finally:
                        db_session.close()

                except Exception as e:
                    # Não falha a requisição se ticket der erro
                    logger.error(f"[WEBHOOK] ⚠️ Erro ao criar ticket: {e}")
                    logger.exception(e)

        # ─────────────────────────────────────────────────────────
        # 6. SALVA CHECKPOINT
        # ─────────────────────────────────────────────────────────

        await checkpoint.save(request.chat_id, state)
        logger.info(f"[WEBHOOK] Checkpoint salvo: {request.chat_id}")

        # ─────────────────────────────────────────────────────────
        # 7. MONTA RESPOSTA
        # ─────────────────────────────────────────────────────────

        response = WebhookResponse(
            chat_id=request.chat_id,
            message=last_message,
            is_finished=is_finished,
            message_type="text",
            analysis_data=analysis_data,
        )

        # ─────────────────────────────────────────────────────────
        # 8. ENVIA CALLBACK AO ZELLU (BACKGROUND)
        # ─────────────────────────────────────────────────────────

        background_tasks.add_task(send_callback_to_zellu, response)

        # ─────────────────────────────────────────────────────────
        # 9. RETORNA SUCESSO (Zellu não espera resposta síncrona)
        # ─────────────────────────────────────────────────────────

        return {
            "status": "success",
            "message": "Mensagem processada com sucesso",
            "chat_id": request.chat_id,
        }

    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Erro ao processar: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# HELPER - ENVIAR CALLBACK AO ZELLU
# ═══════════════════════════════════════════════════════════════

async def send_callback_to_zellu(response: WebhookResponse):
    """
    Envia resposta de volta ao Zellu via webhook callback.

    Args:
        response: Resposta formatada para o Zellu
    """
    zellu_webhook_url = os.getenv("ZELLU_WEBHOOK_URL", "http://localhost:8655/api/chat/webhook")
    api_key = os.getenv("API_KEY_ZELLU_IA", "")

    if not api_key:
        logger.error("[WEBHOOK] ❌ API_KEY_ZELLU_IA não configurada!")
        return

    logger.info(f"[WEBHOOK] Enviando callback ao Zellu: {zellu_webhook_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            http_response = await client.post(
                zellu_webhook_url,
                json=response.model_dump(),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                },
            )

            if http_response.status_code == 200:
                logger.info(f"[WEBHOOK] ✅ Callback enviado com sucesso")
            else:
                logger.error(f"[WEBHOOK] ❌ Callback falhou: {http_response.status_code} - {http_response.text}")

    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Erro ao enviar callback: {e}")
        logger.exception(e)
