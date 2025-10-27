"""Módulo de prompts para a IA conversacional."""

from .system import get_system_prompt, get_finalization_prompt, ToneType
from .examples import CONVERSATION_EXAMPLES, get_few_shot_prompt

__all__ = [
    "get_system_prompt",
    "get_finalization_prompt",
    "ToneType",
    "CONVERSATION_EXAMPLES",
    "get_few_shot_prompt",
]
