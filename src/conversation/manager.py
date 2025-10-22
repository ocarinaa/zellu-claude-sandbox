"""
Conversation Manager com persistência integrada.
"""

from typing import Optional, AsyncIterator
from datetime import datetime

from ..llm import LLMClient
from ..prompts import get_system_prompt, get_finalization_prompt
from ..database import ConversationRepository, MessageRepository, AnalysisCacheRepository
from ..cache import SessionCache
from .schemas import Message, ConversationState, AnalysisData, ToneType
from .extractor import extract_analysis_data

import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Gerencia conversas com IA incluindo persistência.

    Fluxo:
    1. Busca no Redis (cache rápido)
    2. Se não encontrar, busca no PostgreSQL
    3. Se não encontrar, cria nova
    4. Sempre atualiza Redis após operações
    """

    def __init__(
        self,
        llm_client: LLMClient,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        cache_repo: AnalysisCacheRepository,
        session_cache: SessionCache,
    ):
        self.llm = llm_client
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.cache_repo = cache_repo
        self.session_cache = session_cache

    async def start_conversation(
        self,
        chat_id: str,
        user_name: str | None = None,
        tone: ToneType = "conciliador",
    ) -> ConversationState:
        """
        Inicia nova conversa ou recupera existente.

        Args:
            chat_id: ID único da conversa
            user_name: Nome do usuário
            tone: Tom da conversa

        Returns:
            Estado da conversa
        """
        # 1. Tenta buscar no cache primeiro (rápido)
        cached = await self.session_cache.get(chat_id)
        if cached:
            logger.info(f"[CACHE HIT] Conversa {chat_id} recuperada do Redis")
            return ConversationState(**cached)

        # 2. Busca no banco (se não está no cache)
        db_conversation = await self.conversation_repo.get_by_chat_id(chat_id)

        if db_conversation:
            # Conversa existe no banco
            logger.info(f"[DB HIT] Conversa {chat_id} recuperada do PostgreSQL")
            state = ConversationState(
                conversation_id=chat_id,
                messages=[Message(**msg) for msg in db_conversation.messages],
                tone=db_conversation.tone,
                is_finalized=db_conversation.is_finished,
                analysis_data=AnalysisData(**db_conversation.analysis_data) if db_conversation.analysis_data else None,
            )
        else:
            # 3. Cria nova conversa
            logger.info(f"[NEW] Criando nova conversa {chat_id}")
            await self.conversation_repo.create(
                chat_id=chat_id,
                user_name=user_name,
                tone=tone,
            )
            state = ConversationState(
                conversation_id=chat_id,
                messages=[],
                tone=tone,
            )

        # 4. Salva no cache para acesso rápido
        await self.session_cache.set(chat_id, state.model_dump())
        logger.info(f"[CACHE SET] Conversa {chat_id} cacheada no Redis")

        return state

    async def add_user_message(
        self,
        chat_id: str,
        content: str,
    ) -> ConversationState:
        """
        Adiciona mensagem do usuário e persiste.
        """
        state = await self.start_conversation(chat_id)

        # Adiciona ao estado
        user_msg = Message(role="user", content=content)
        state.messages.append(user_msg)

        # Persiste no banco
        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="user",
            content=content,
        )

        # Atualiza cache
        await self.session_cache.set(chat_id, state.model_dump())

        logger.info(f"[USER MSG] Mensagem adicionada à conversa {chat_id}")
        return state

    async def generate_response(
        self,
        chat_id: str,
        user_message: str,
    ) -> str:
        """
        Gera resposta da IA e persiste.
        """
        # Adiciona mensagem do usuário
        state = await self.add_user_message(chat_id, user_message)

        # Prepara mensagens para LLM
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        # Gera resposta
        system_prompt = get_system_prompt(state.tone)
        response = self.llm.chat(
            messages=messages,
            system=system_prompt,
        )

        # Adiciona resposta ao estado
        assistant_msg = Message(role="assistant", content=response)
        state.messages.append(assistant_msg)

        # Persiste no banco
        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=response,
        )

        # Atualiza cache
        await self.session_cache.set(chat_id, state.model_dump())

        logger.info(f"[AI RESPONSE] Resposta gerada e persistida para {chat_id}")
        return response

    async def generate_response_stream(
        self,
        chat_id: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """
        Gera resposta da IA em streaming e persiste ao final.
        """
        # Adiciona mensagem do usuário
        state = await self.add_user_message(chat_id, user_message)

        # Prepara mensagens
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        # Streaming
        system_prompt = get_system_prompt(state.tone)
        full_response = ""

        for chunk in self.llm.chat_stream(
            messages=messages,
            system=system_prompt,
        ):
            full_response += chunk
            yield chunk

        # Persiste resposta completa
        assistant_msg = Message(role="assistant", content=full_response)
        state.messages.append(assistant_msg)

        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=full_response,
        )

        # Atualiza cache
        await self.session_cache.set(chat_id, state.model_dump())

        logger.info(f"[STREAM COMPLETE] Resposta streaming persistida para {chat_id}")

    async def should_finish(self, chat_id: str) -> bool:
        """
        Decide se deve finalizar conversa.

        Critérios:
        - Usuário confirmou que deu todas informações
        - 7+ mensagens com dados suficientes
        - IA detecta que tem info suficiente
        """
        state = await self.start_conversation(chat_id)

        # Mínimo 3 trocas (6 mensagens)
        if len(state.messages) < 6:
            return False

        # Verifica cache de análise parcial
        cache = await self.cache_repo.get(chat_id)
        if cache and cache.confidence_score > 0.8:
            logger.info(f"[SHOULD FINISH] Cache confidence {cache.confidence_score} > 0.8")
            return True

        # Pergunta ao LLM
        last_messages = state.messages[-6:]
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in last_messages
        ]

        decision_prompt = """Com base nas últimas mensagens, você tem informações suficientes para gerar uma análise completa?

Informações necessárias:
- Descrição do problema
- Nome da empresa/pessoa envolvida
- Valor monetário (se aplicável)
- Tentativas anteriores
- Dados do usuário (nome, CPF, contato)

Responda APENAS: SIM ou NAO"""

        response = self.llm.chat(
            messages=messages,
            system=decision_prompt,
        )

        should_finish = "sim" in response.lower()
        logger.info(f"[SHOULD FINISH] LLM decidiu: {should_finish}")
        return should_finish

    async def finish_conversation(
        self,
        chat_id: str,
    ) -> AnalysisData:
        """
        Finaliza conversa e gera análise completa.
        """
        state = await self.start_conversation(chat_id)

        # Prepara mensagens
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        # Gera análise
        finalization_prompt = get_finalization_prompt()
        response = self.llm.chat(
            messages=messages,
            system=finalization_prompt,
        )

        # Extrai JSON
        analysis_data = extract_analysis_data(response)

        # Persiste no banco
        await self.conversation_repo.finish_conversation(
            chat_id=chat_id,
            analysis_data=analysis_data.model_dump(),
        )

        # Remove do cache (finalizada)
        await self.session_cache.delete(chat_id)

        logger.info(f"[FINISHED] Conversa {chat_id} finalizada com análise completa")
        return analysis_data

    async def get_conversation_history(
        self,
        chat_id: str,
    ) -> Optional[ConversationState]:
        """
        Busca histórico completo de uma conversa.
        """
        db_conversation = await self.conversation_repo.get_by_chat_id(chat_id)
        if not db_conversation:
            return None

        return ConversationState(
            conversation_id=chat_id,
            messages=[Message(**msg) for msg in db_conversation.messages],
            tone=db_conversation.tone,
            is_finalized=db_conversation.is_finished,
            analysis_data=AnalysisData(**db_conversation.analysis_data) if db_conversation.analysis_data else None,
        )
