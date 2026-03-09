"""
Speech-to-Text module.
Модуль распознавания речи.
"""

from voice_assistant.stt.base import STTBase
from voice_assistant.stt.vosk import VoskSTT

__all__ = ["STTBase", "VoskSTT"]