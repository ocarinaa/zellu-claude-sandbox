"""
Nó Collector: Coleta informações através de conversa natural.
"""

from typing import Any
from ...llm import LLMClient
from ...prompts import get_system_prompt
from ..state import ConversationGraphState, ExtractedInfo

import logging
import json
import re

logger = logging.getLogger(__name__)


async def collector_node(
    state: ConversationGraphState,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """
    Coleta informações do usuário através de conversa natural.

    Args:
        state: Estado atual do grafo
        llm_client: Cliente LLM

    Returns:
        Estado atualizado
    """
    logger.info(f"[COLLECTOR] Processando mensagem (turn {state['turn_count']})")

    # Pega última mensagem do usuário
    last_user_message = state["messages"][-1]["content"]

    # Detecta se última mensagem é sobre documento
    if "📄 Documento enviado:" in last_user_message:
        logger.info("[COLLECTOR] Documento detectado, processando informações")

        # IA já recebeu resumo do documento, apenas extrai informações adicionais
        extracted = await _extract_structured_info(
            state["messages"],
            state["extracted_info"],
            llm_client,
        )

        # Marca que possui documentos
        extracted.has_documents = True

        state["extracted_info"] = extracted

        # Gera resposta curta reconhecendo documento
        response = "Recebi seu documento! Vou analisar as informações. " \
                   "Há mais alguma coisa que você gostaria de adicionar sobre seu caso?"

        state["messages"].append({
            "role": "assistant",
            "content": response,
        })

        state["turn_count"] += 1
        state["current_step"] = "validate"

        return state

    # System prompt com foco em extração
    extraction_prompt = f"""{get_system_prompt(state['tone'])}

TAREFA ADICIONAL: Enquanto conversa, extraia as seguintes informações:
- Descrição do problema (detalhes)
- Nome da empresa/pessoa (quem causou o problema)
- Valor monetário envolvido (se aplicável)
- Tentativas anteriores de resolução
- Documentos disponíveis
- Dados do usuário (nome, CPF, email, telefone)

Mantenha conversa natural e empática enquanto coleta essas informações.
"""

    # Gera resposta
    response = llm_client.chat(
        messages=state["messages"],
        system=extraction_prompt,
    )

    # Adiciona resposta ao state
    state["messages"].append({
        "role": "assistant",
        "content": response,
    })

    # Extrai informações estruturadas em paralelo
    extracted = await _extract_structured_info(
        state["messages"],
        state["extracted_info"],
        llm_client,
    )

    state["extracted_info"] = extracted
    state["turn_count"] += 1
    state["current_step"] = "validate"

    logger.info(f"[COLLECTOR] Confidence score: {extracted.confidence_score:.2f}")

    return state


async def _extract_structured_info(
    messages: list[dict],
    current_info: ExtractedInfo,
    llm_client: LLMClient,
) -> ExtractedInfo:
    """
    Extrai informações estruturadas das mensagens.
    """
    # Prompt de extração
    extraction_prompt = """Analise a conversa e extraia informações estruturadas.

Retorne APENAS um JSON válido (sem markdown, sem explicações):

{
  "problem_description": "string ou null",
  "company_name": "string ou null",
  "monetary_value": number ou null,
  "user_full_name": "string ou null",
  "user_cpf": "string ou null",
  "user_email": "string ou null",
  "user_phone": "string ou null",
  "previous_attempts": ["string"],
  "has_documents": boolean,
  "confidence_score": 0.0 a 1.0
}

REGRAS:
- Se não mencionado, use null
- monetary_value deve ser número (ex: 89.90, não "R$ 89,90")
- confidence_score: quão completas estão as informações (0=nada, 1=completo)
- previous_attempts: lista de tentativas mencionadas
"""

    # Pega últimas 10 mensagens (contexto suficiente)
    recent_messages = messages[-10:]

    response = llm_client.chat(
        messages=recent_messages,
        system=extraction_prompt,
    )

    # Parse JSON
    try:
        # Remove markdown se presente
        json_str = response.strip()
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)

        extracted_data = json.loads(json_str)

        # Merge com dados existentes (não sobrescreve se já existe)
        merged = current_info.model_dump()
        for key, value in extracted_data.items():
            if value is not None and (merged.get(key) is None or merged.get(key) == []):
                merged[key] = value

        return ExtractedInfo(**merged)

    except json.JSONDecodeError as e:
        logger.error(f"[COLLECTOR] Erro ao parsear JSON: {e}")
        logger.debug(f"[COLLECTOR] Response: {response}")
        return current_info  # Retorna sem mudanças


async def collector_node_with_context(state: ConversationGraphState) -> dict[str, Any]:
    """Wrapper para usar no LangGraph (sem precisar passar llm_client)."""
    from ...llm import LLMClient
    llm_client = LLMClient(primary_provider="anthropic")
    return await collector_node(state, llm_client)
