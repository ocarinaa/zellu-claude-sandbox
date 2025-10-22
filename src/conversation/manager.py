"""
Conversation Manager com LangGraph integrado.
"""

from typing import Optional, AsyncIterator
from datetime import datetime

from ..llm import LLMClient
from ..prompts import get_system_prompt, get_finalization_prompt
from ..database import ConversationRepository, MessageRepository, AnalysisCacheRepository
from ..cache import SessionCache
from .schemas import Message, ConversationState, AnalysisData, ToneType
from .extractor import extract_analysis_data

# Importa LangGraph
try:
    from ..core import compile_conversation_graph, ConversationGraphState, ExtractedInfo
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger_import = __import__('logging').getLogger(__name__)
    logger_import.warning("[IMPORT] LangGraph não disponível, usando modo fallback")

import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Gerencia conversas com IA usando LangGraph.

    Fluxo:
    1. Busca no Redis (cache rápido)
    2. Se não encontrar, busca no PostgreSQL
    3. Se não encontrar, cria nova
    4. Sempre atualiza Redis após operações
    5. Usa LangGraph para orquestrar coleta de informações
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

        # Inicializa grafo se disponível
        if LANGGRAPH_AVAILABLE:
            try:
                self.graph = compile_conversation_graph()
                logger.info("[GRAPH] LangGraph compilado e pronto")
            except Exception as e:
                logger.error(f"[GRAPH] Erro ao compilar grafo: {e}")
                self.graph = None
        else:
            self.graph = None
            logger.warning("[GRAPH] LangGraph não disponível, usando modo fallback")

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
        Gera resposta da IA usando LangGraph.

        Args:
            chat_id: ID da conversa
            user_message: Mensagem do usuário

        Returns:
            Resposta da IA
        """
        # Se grafo não está disponível, usa fallback
        if not self.graph:
            logger.warning(f"[FALLBACK] Grafo não disponível para {chat_id}")
            return await self._generate_response_fallback(chat_id, user_message)

        logger.info(f"[GRAPH] Processando mensagem com LangGraph para {chat_id}")

        # 1. Adiciona mensagem do usuário
        state = await self.add_user_message(chat_id, user_message)

        # 2. Converte state do manager → state do grafo
        graph_state = self._convert_to_graph_state(state)

        # 3. Executa grafo
        try:
            result = await self.graph.ainvoke(graph_state)
            logger.info(f"[GRAPH] Grafo executado com sucesso para {chat_id}")
        except Exception as e:
            logger.error(f"[GRAPH] Erro ao executar grafo: {e}")
            # Fallback para lógica anterior (sem grafo)
            return await self._generate_response_fallback(chat_id, user_message)

        # 4. Extrai resposta (última mensagem do assistant)
        assistant_messages = [
            msg for msg in result["messages"]
            if msg["role"] == "assistant"
        ]

        if not assistant_messages:
            logger.error(f"[GRAPH] Nenhuma resposta gerada pelo grafo")
            return await self._generate_response_fallback(chat_id, user_message)

        response = assistant_messages[-1]["content"]

        # 5. Persiste resposta
        assistant_msg = Message(role="assistant", content=response)
        state.messages.append(assistant_msg)

        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=response,
        )

        # 6. Atualiza state com extracted_info
        state.extracted_info = result["extracted_info"]

        # 7. Atualiza cache
        await self.session_cache.set(chat_id, state.model_dump())

        logger.info(f"[GRAPH] Resposta gerada e persistida para {chat_id}")
        logger.info(f"[GRAPH] Confidence score: {result['extracted_info'].confidence_score:.2f}")

        return response

    async def generate_response_stream(
        self,
        chat_id: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """
        Gera resposta em streaming (NOTA: LangGraph não suporta streaming nativo).

        Por enquanto, executa o grafo completo e simula streaming da resposta.

        Args:
            chat_id: ID da conversa
            user_message: Mensagem do usuário

        Yields:
            Chunks da resposta
        """
        # Se grafo não está disponível, usa fallback
        if not self.graph:
            logger.warning(f"[FALLBACK STREAM] Grafo não disponível para {chat_id}")
            async for chunk in self._generate_response_stream_fallback(chat_id, user_message):
                yield chunk
            return

        logger.info(f"[GRAPH STREAM] Processando com LangGraph para {chat_id}")

        # 1. Adiciona mensagem do usuário
        state = await self.add_user_message(chat_id, user_message)

        # 2. Converte state
        graph_state = self._convert_to_graph_state(state)

        # 3. Executa grafo (completo)
        try:
            result = await self.graph.ainvoke(graph_state)
        except Exception as e:
            logger.error(f"[GRAPH STREAM] Erro: {e}")
            # Fallback
            async for chunk in self._generate_response_stream_fallback(chat_id, user_message):
                yield chunk
            return

        # 4. Extrai resposta
        assistant_messages = [
            msg for msg in result["messages"]
            if msg["role"] == "assistant"
        ]

        if not assistant_messages:
            logger.error(f"[GRAPH STREAM] Nenhuma resposta gerada")
            return

        full_response = assistant_messages[-1]["content"]

        # 5. Simula streaming (chunk por chunk)
        chunk_size = 10  # caracteres por chunk
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i + chunk_size]
            yield chunk

        # 6. Persiste resposta completa
        assistant_msg = Message(role="assistant", content=full_response)
        state.messages.append(assistant_msg)

        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=full_response,
        )

        # 7. Atualiza state
        state.extracted_info = result["extracted_info"]
        await self.session_cache.set(chat_id, state.model_dump())

        logger.info(f"[GRAPH STREAM] Resposta completa persistida para {chat_id}")

    async def should_finish(self, chat_id: str) -> bool:
        """
        Decide se deve finalizar conversa.

        Agora delega a decisão para o grafo (decider_node).
        """
        state = await self.start_conversation(chat_id)

        # Se state tem extracted_info, usa decisão do grafo
        if state.extracted_info:
            extracted = state.extracted_info

            # Critérios do decider_node
            MIN_TURNS = 3
            MIN_CONFIDENCE = 0.7

            if len(state.messages) < (MIN_TURNS * 2):
                return False

            if extracted.missing_fields:
                return False

            if extracted.confidence_score < MIN_CONFIDENCE:
                return False

            return True

        # Fallback: lógica anterior
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
        Finaliza conversa e gera análise.

        Usa o finisher_node do grafo se possível.
        """
        logger.info(f"[FINISH] Finalizando conversa {chat_id}")

        state = await self.start_conversation(chat_id)

        # Se state já tem analysis_data (do grafo ou anterior), usa
        if state.analysis_data:
            logger.info(f"[FINISH] Usando analysis_data existente")
            analysis_data = state.analysis_data
        else:
            # Se grafo está disponível e state tem extracted_info
            if self.graph and state.extracted_info:
                logger.info(f"[FINISH] Forçando execução completa do grafo")

                graph_state = self._convert_to_graph_state(state)
                graph_state["should_finish"] = True
                graph_state["current_step"] = "analyze"

                try:
                    result = await self.graph.ainvoke(graph_state)

                    if "analysis_data" in result and result["analysis_data"]:
                        analysis_data = AnalysisData(**result["analysis_data"])
                    else:
                        # Fallback: usa método anterior
                        logger.warning(f"[FINISH] Grafo não gerou analysis_data, usando fallback")
                        analysis_data = await self._finish_conversation_fallback(state)
                except Exception as e:
                    logger.error(f"[FINISH] Erro ao executar grafo: {e}")
                    analysis_data = await self._finish_conversation_fallback(state)
            else:
                # Fallback completo
                logger.warning(f"[FINISH] Usando fallback (sem grafo)")
                analysis_data = await self._finish_conversation_fallback(state)

        # Persiste
        await self.conversation_repo.finish_conversation(
            chat_id=chat_id,
            analysis_data=analysis_data.model_dump(),
        )

        await self.session_cache.delete(chat_id)

        logger.info(f"[FINISH] Conversa {chat_id} finalizada")
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

    # === MÉTODOS AUXILIARES ===

    def _convert_to_graph_state(self, state: ConversationState) -> ConversationGraphState:
        """
        Converte state do manager para state do grafo.
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph não disponível")

        return ConversationGraphState(
            messages=[
                {"role": msg.role, "content": msg.content}
                for msg in state.messages
            ],
            extracted_info=state.extracted_info if state.extracted_info else ExtractedInfo(),
            current_step="collect",
            should_finish=False,
            tone=state.tone,
            chat_id=state.conversation_id,
            turn_count=len(state.messages) // 2,
        )

    async def _generate_response_fallback(self, chat_id: str, user_message: str) -> str:
        """Fallback: gera resposta sem usar grafo."""
        logger.warning(f"[FALLBACK] Usando lógica anterior sem grafo")

        state = await self.add_user_message(chat_id, user_message)

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        system_prompt = get_system_prompt(state.tone)
        response = self.llm.chat(
            messages=messages,
            system=system_prompt,
        )

        assistant_msg = Message(role="assistant", content=response)
        state.messages.append(assistant_msg)

        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=response,
        )

        await self.session_cache.set(chat_id, state.model_dump())

        return response

    async def _generate_response_stream_fallback(
        self,
        chat_id: str,
        user_message: str
    ) -> AsyncIterator[str]:
        """Fallback: streaming sem grafo."""
        logger.warning(f"[FALLBACK STREAM] Usando lógica anterior")

        state = await self.add_user_message(chat_id, user_message)

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        system_prompt = get_system_prompt(state.tone)
        full_response = ""

        for chunk in self.llm.chat_stream(
            messages=messages,
            system=system_prompt,
        ):
            full_response += chunk
            yield chunk

        assistant_msg = Message(role="assistant", content=full_response)
        state.messages.append(assistant_msg)

        await self.conversation_repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=full_response,
        )

        await self.session_cache.set(chat_id, state.model_dump())

    async def _finish_conversation_fallback(self, state: ConversationState) -> AnalysisData:
        """Fallback: finaliza sem grafo."""
        logger.warning(f"[FALLBACK FINISH] Usando lógica anterior")

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in state.messages
        ]

        finalization_prompt = get_finalization_prompt()
        response = self.llm.chat(
            messages=messages,
            system=finalization_prompt,
        )

        analysis_data = extract_analysis_data(response)

        return analysis_data
