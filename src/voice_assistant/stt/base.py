"""
Abstract base interface for STT providers.
Абстрактный базовый интерфейс для провайдеров STT.
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable

from voice_assistant.utils.audio import AudioStream


class STTBase(ABC):
    """
    Abstract interface for Speech-to-Text providers.
    Абстрактный интерфейс для провайдеров распознавания речи.
    """

    @abstractmethod
    def recognize_trigger(
            self,
            audio_stream: AudioStream,
            trigger: str
    ) -> tuple[bool, Optional[str]]:
        """
        Listen for trigger word in audio stream.
        Слушает поток до обнаружения триггер-слова.

        Args:
            audio_stream: Audio input stream / Аудио-поток ввода
            trigger: Trigger word to detect / Триггер-слово для обнаружения

        Returns:
            Tuple of (trigger_detected, context_text)
            Кортеж из (обнаружен_триггер, контекстный_текст)
        """
        pass

    @abstractmethod
    def recognize_command(
            self,
            audio_stream: AudioStream,
            on_partial: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Recognize command with optional callback for partial results.
        Распознаёт команду с опциональным колбэком для промежуточных результатов.

        Args:
            audio_stream: Audio input stream / Аудио-поток ввода
            on_partial: Optional callback for partial recognition results
                       Опциональный колбэк для промежуточных результатов распознавания

        Returns:
            Recognized command text or None / Распознанный текст команды или None
        """
        pass