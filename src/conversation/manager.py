"""
Gerenciador de conversação com IA.
Integra prompts, LLM client e estado da conversa.
"""

import json
import uuid
from typing import Iterator, Optional
from datetime import datetime

from ..llm import LLMClient, LLMConfig
from ..prompts import get_system_prompt, get_finalization_prompt, get_few_shot_prompt
from .schemas import ConversationState, AnalysisData, Message


class ConversationManager:
    """
    Gerenciador central de conversas.

    Responsável por:
    - Gerenciar histórico de mensagens
    - Integrar prompts + LLM
    - Detectar momento de finalizar
    - Extrair analysis_data do JSON final

    Usage:
        manager = ConversationManager()
        conversation_id = manager.start_conversation()

        # Enviar mensagens
        response = manager.send_message(conversation_id, "Olá!")

        # Ou com streaming
        for chunk in manager.send_message_stream(conversation_id, "Olá!"):
            print(chunk, end="")
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        default_tone: str = "conciliador",
    ):
        """
        Inicializa o gerenciador.

        Args:
            llm_client: Cliente LLM customizado (usa padrão se None)
            default_tone: Tom padrão das conversas
        """
        self.llm_client = llm_client or LLMClient()
        self.default_tone = default_tone

        # Armazena conversas em memória (em produção, usar DB)
        self._conversations: dict[str, ConversationState] = {}

    def start_conversation(
        self,
        tone: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        Inicia uma nova conversa.

        Args:
            tone: Tom da conversa (usa default se None)
            conversation_id: ID customizado (gera UUID se None)

        Returns:
            ID da conversa criada
        """
        conv_id = conversation_id or str(uuid.uuid4())
        tone = tone or self.default_tone

        self._conversations[conv_id] = ConversationState(
            conversation_id=conv_id,
            tone=tone,
        )

        return conv_id

    def send_message(
        self,
        conversation_id: str,
        user_message: str,
        config: Optional[LLMConfig] = None,
    ) -> str:
        """
        Envia mensagem e retorna resposta completa.

        Args:
            conversation_id: ID da conversa
            user_message: Mensagem do usuário
            config: Configuração LLM customizada

        Returns:
            Resposta da IA

        Raises:
            ValueError: Se conversa não existir ou já estiver finalizada
        """
        state = self._get_conversation(conversation_id)

        if state.is_finalized:
            raise ValueError("Conversa já foi finalizada")

        # Adiciona mensagem do usuário
        state.add_message("user", user_message)

        # Verifica se deve finalizar
        should_finalize = self._should_finalize(state)

        if should_finalize:
            # Gera análise final
            analysis = self._generate_analysis(state, config)
            state.analysis_data = analysis
            state.is_finalized = True

            # Resposta de finalização
            response = (
                "Perfeito! Coletei todas as informações necessárias. "
                "Sua análise está pronta! 📋"
            )
        else:
            # Conversa normal
            response = self._get_llm_response(state, config)

        # Adiciona resposta ao histórico
        state.add_message("assistant", response)

        return response

    def send_message_stream(
        self,
        conversation_id: str,
        user_message: str,
        config: Optional[LLMConfig] = None,
    ) -> Iterator[str]:
        """
        Envia mensagem e retorna generator de chunks (streaming).

        Args:
            conversation_id: ID da conversa
            user_message: Mensagem do usuário
            config: Configuração LLM customizada

        Yields:
            Chunks da resposta
        """
        state = self._get_conversation(conversation_id)

        if state.is_finalized:
            raise ValueError("Conversa já foi finalizada")

        # Adiciona mensagem do usuário
        state.add_message("user", user_message)

        # Verifica se deve finalizar
        should_finalize = self._should_finalize(state)

        if should_finalize:
            # Gera análise final
            analysis = self._generate_analysis(state, config)
            state.analysis_data = analysis
            state.is_finalized = True

            # Resposta de finalização
            response = (
                "Perfeito! Coletei todas as informações necessárias. "
                "Sua análise está pronta! 📋"
            )
            state.add_message("assistant", response)
            yield response
        else:
            # Conversa normal com streaming
            full_response = ""
            for chunk in self._get_llm_response_stream(state, config):
                full_response += chunk
                yield chunk

            # Adiciona resposta completa ao histórico
            state.add_message("assistant", full_response)

    def get_conversation(self, conversation_id: str) -> ConversationState:
        """
        Retorna estado da conversa.

        Args:
            conversation_id: ID da conversa

        Returns:
            Estado atual da conversa
        """
        return self._get_conversation(conversation_id)

    def get_analysis(self, conversation_id: str) -> Optional[AnalysisData]:
        """
        Retorna análise final da conversa (se finalizada).

        Args:
            conversation_id: ID da conversa

        Returns:
            AnalysisData se finalizada, None caso contrário
        """
        state = self._get_conversation(conversation_id)
        return state.analysis_data

    def _get_conversation(self, conversation_id: str) -> ConversationState:
        """Retorna conversa ou lança erro."""
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversa {conversation_id} não encontrada")
        return self._conversations[conversation_id]

    def _should_finalize(self, state: ConversationState) -> bool:
        """
        Determina se deve finalizar a conversa.

        Critérios:
        1. Usuário explicitamente pede para finalizar
        2. Já tem 7+ mensagens E análise detecta informações suficientes
        """
        last_user_message = None
        for msg in reversed(state.messages):
            if msg.role == "user":
                last_user_message = msg.content.lower()
                break

        if not last_user_message:
            return False

        # Palavras-chave que indicam finalização
        finalization_keywords = [
            "finalizar",
            "terminar",
            "é isso",
            "só isso",
            "acabei",
            "já falei tudo",
            "pronto",
            "pode analisar",
        ]

        # Usuário pediu explicitamente
        if any(keyword in last_user_message for keyword in finalization_keywords):
            return True

        # Heurística: 7+ mensagens do usuário = provavelmente tem info suficiente
        if state.user_message_count >= 7:
            return True

        return False

    def _get_llm_response(
        self,
        state: ConversationState,
        config: Optional[LLMConfig] = None,
    ) -> str:
        """Obtém resposta da LLM."""
        system_prompt = self._build_system_prompt(state)
        messages = state.get_messages_for_llm()

        return self.llm_client.chat(
            messages=messages,
            system=system_prompt,
            config=config,
        )

    def _get_llm_response_stream(
        self,
        state: ConversationState,
        config: Optional[LLMConfig] = None,
    ) -> Iterator[str]:
        """Obtém resposta da LLM em streaming."""
        system_prompt = self._build_system_prompt(state)
        messages = state.get_messages_for_llm()

        yield from self.llm_client.chat_stream(
            messages=messages,
            system=system_prompt,
            config=config,
        )

    def _build_system_prompt(self, state: ConversationState) -> str:
        """Constrói system prompt completo."""
        base_prompt = get_system_prompt(state.tone)
        few_shot = get_few_shot_prompt()

        # Contexto adicional baseado no progresso
        progress_context = f"\n\nProgresso: {state.user_message_count} mensagens coletadas."

        return base_prompt + "\n\n" + few_shot + progress_context

    def _generate_analysis(
        self,
        state: ConversationState,
        config: Optional[LLMConfig] = None,
    ) -> AnalysisData:
        """
        Gera análise final do caso.

        Envia finalization_prompt para LLM extrair JSON estruturado.
        """
        finalization_prompt = get_finalization_prompt()
        messages = state.get_messages_for_llm()

        # Pede para LLM gerar JSON
        json_response = self.llm_client.chat(
            messages=messages,
            system=finalization_prompt,
            config=config,
        )

        # Parse JSON
        try:
            # Remove markdown code blocks se existirem
            json_str = json_response.strip()
            if json_str.startswith("```"):
                # Remove ```json ou ```
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])

            data = json.loads(json_str)
            return AnalysisData(**data)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: retorna análise com valores padrão
            return AnalysisData(
                problem="Erro ao extrair análise. Revise o histórico manualmente.",
                rights=["Direitos do consumidor (CDC)"],
                estimatedValue=1000.0,
                recommendations=[
                    {
                        "type": "amigavel",
                        "score": 5.0,
                        "reason": "Análise incompleta",
                    },
                    {
                        "type": "extrajudicial",
                        "score": 5.0,
                        "reason": "Análise incompleta",
                    },
                    {
                        "type": "judicial",
                        "score": 5.0,
                        "reason": "Análise incompleta",
                    },
                ],
                userInfo={},
                opposingParty={},
                caseDetails={},
            )
