"""
Text-to-Speech module.
Модуль синтеза речи.
"""

from voice_assistant.tts.base import TTSBase
from voice_assistant.tts.edge import EdgeTTS

__all__ = ["TTSBase", "EdgeTTS"]