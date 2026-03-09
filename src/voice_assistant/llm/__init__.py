"""
LLM client module.
Модуль клиента LLM.
"""

from voice_assistant.llm.base import LLMBase
from voice_assistant.llm.openrouter import OpenRouterClient

__all__ = ["LLMBase", "OpenRouterClient"]