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

    # Salva checkpoint antes de processar (recuperação em caso de falha)
    from ..checkpoint import get_checkpoint_service
    checkpoint = get_checkpoint_service()
    await checkpoint.save(state["chat_id"], state, auto=True)

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

    # System prompt com foco em extração + few-shot examples
    from ...prompts import get_few_shot_prompt

    extraction_prompt = f"""{get_system_prompt(state['tone'])}

TAREFA ADICIONAL: Enquanto conversa, extraia as seguintes informações:
- Descrição do problema (detalhes)
- Nome da empresa/pessoa (quem causou o problema)
- Valor monetário envolvido (se aplicável)
- Tentativas anteriores de resolução
- Documentos disponíveis
- Dados do usuário (nome, CPF, email, telefone)

Mantenha conversa natural e empática enquanto coleta essas informações.

{get_few_shot_prompt()}
"""

    # Gera resposta (usa async para melhor performance)
    response = await llm_client.chat(
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

    # Salva checkpoint após processar
    await checkpoint.save(state["chat_id"], state, auto=True)

    return state


async def _extract_structured_info(
    messages: list[dict],
    current_info: ExtractedInfo,
    llm_client: LLMClient,
) -> ExtractedInfo:
    """
    Extrai informações estruturadas das mensagens.
    """
    # Prompt de extração melhorado
    extraction_prompt = """Você é um extrator de informações. Analise a conversa e retorne APENAS um JSON válido.

IMPORTANTE: Sua resposta deve ser SOMENTE o JSON, sem nenhum texto antes ou depois.

Formato exato:
{
  "problem_description": "descrição ou null",
  "company_name": "nome ou null",
  "monetary_value": 0.0,
  "user_full_name": "nome ou null",
  "user_cpf": "cpf ou null",
  "user_email": "email ou null",
  "user_phone": "telefone ou null",
  "previous_attempts": [],
  "has_documents": false,
  "confidence_score": 0.0
}

REGRAS CRÍTICAS:
1. monetary_value: número decimal (ex: 89.90), use 0.0 se não mencionado
2. confidence_score: 0.0 a 1.0 baseado em:
   - 0.0-0.3: Informações mínimas (só problema)
   - 0.4-0.6: Informações parciais (problema + empresa/valor)
   - 0.7-0.8: Informações quase completas (falta 1-2 dados pessoais)
   - 0.9-1.0: Todas informações coletadas (nome, CPF, email, telefone)
3. has_documents: true se mencionou "tenho", "possuo", "print", "comprovante"
4. previous_attempts: lista vazia [] se não mencionado
5. null apenas para strings não mencionadas
6. NÃO adicione comentários ou texto extra

RESPONDA APENAS COM O JSON."""

    # Pega últimas 10 mensagens (contexto suficiente)
    recent_messages = messages[-10:]

    # Usa async para melhor performance
    response = await llm_client.chat(
        messages=recent_messages,
        system=extraction_prompt,
    )

    # Parse JSON com múltiplos fallbacks
    try:
        # Limpeza agressiva
        json_str = response.strip()

        # Remove markdown (múltiplas variações)
        json_str = re.sub(r'^```(?:json)?\s*', '', json_str, flags=re.IGNORECASE)
        json_str = re.sub(r'\s*```\s*$', '', json_str)

        # Remove texto antes/depois do JSON
        # Procura por { até } (pode ter texto ao redor)
        json_match = re.search(r'\{[\s\S]*\}', json_str)
        if json_match:
            json_str = json_match.group(0)

        # Tenta parsear
        extracted_data = json.loads(json_str)

        # Valida se tem as chaves esperadas
        required_keys = ["problem_description", "confidence_score"]
        if not all(key in extracted_data for key in required_keys):
            logger.warning(f"[COLLECTOR] JSON inválido (faltam chaves), usando fallback")
            raise ValueError("Missing required keys")

        # Merge com dados existentes
        merged = current_info.model_dump()

        # Campos que SEMPRE atualizam (mesmo se já existem)
        always_update = ["confidence_score", "has_documents"]

        for key, value in extracted_data.items():
            if key in always_update:
                # Sempre atualiza confidence e has_documents
                if value is not None:
                    merged[key] = value
            elif value is not None and (merged.get(key) is None or merged.get(key) == [] or merged.get(key) == 0.0):
                # Outros campos: só atualiza se estiver vazio
                merged[key] = value

        logger.info(f"[COLLECTOR] ✅ Extração JSON bem-sucedida (confidence: {extracted_data.get('confidence_score', 0):.2f})")
        return ExtractedInfo(**merged)

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"[COLLECTOR] Erro ao parsear JSON: {e}")
        logger.debug(f"[COLLECTOR] Response recebida: {response[:200]}...")

        # FALLBACK: Extração manual básica
        logger.info(f"[COLLECTOR] Usando fallback de extração manual")

        # Conta informações presentes
        info_count = 0
        current_dict = current_info.model_dump()

        if current_dict.get("problem_description"):
            info_count += 1
        if current_dict.get("company_name"):
            info_count += 1
        if current_dict.get("monetary_value"):
            info_count += 1
        if current_dict.get("user_full_name"):
            info_count += 1
        if current_dict.get("user_cpf"):
            info_count += 1
        if current_dict.get("user_email"):
            info_count += 1
        if current_dict.get("user_phone"):
            info_count += 1

        # Calcula confidence baseado em quantas informações temos
        confidence = min(info_count / 7.0, 1.0)  # 7 campos principais

        logger.info(f"[COLLECTOR] Fallback calculou confidence: {confidence:.2f} ({info_count}/7 campos)")

        # Atualiza confidence
        current_dict["confidence_score"] = confidence

        return ExtractedInfo(**current_dict)


async def collector_node_with_context(state: ConversationGraphState) -> dict[str, Any]:
    """Wrapper para usar no LangGraph (sem precisar passar llm_client)."""
    from ...llm import LLMClient
    llm_client = LLMClient(primary_provider="anthropic")
    return await collector_node(state, llm_client)
