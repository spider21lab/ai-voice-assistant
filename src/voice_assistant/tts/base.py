"""
Abstract base interface for TTS providers.
Абстрактный базовый интерфейс для провайдеров TTS.
"""

import threading
from abc import ABC, abstractmethod
from typing import Optional, Callable


class TTSBase(ABC):
    """
    Abstract interface for Text-to-Speech providers.
    Абстрактный интерфейс для провайдеров синтеза речи.
    """

    @abstractmethod
    def say(
            self,
            text: str,
            block: bool = True,
            on_start: Optional[Callable] = None
    ) -> bool:
        """
        Speak the text.
        Озвучивает текст.

        Args:
            text: Text to speak / Текст для озвучки
            block: Block execution until playback completes
                  Блокировать выполнение до конца воспроизведения
            on_start: Optional callback when playback starts
                     Опциональный колбэк при старте воспроизведения

        Returns:
            Success status / Статус успеха
        """
        pass

    def say_async(
            self,
            text: str,
            on_start: Optional[Callable] = None
    ) -> threading.Thread:
        """
        Non-blocking call to say() in separate thread.
        Неблокирующий вызов say() в отдельном потоке.

        Args:
            text: Text to speak / Текст для озвучки
            on_start: Optional callback when playback starts
                     Опциональный колбэк при старте воспроизведения

        Returns:
            Thread object / Объект потока
        """

        def _run() -> None:
            self.say(text, block=True, on_start=on_start)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    @abstractmethod
    def stop(self) -> None:
        """
        Stop current playback.
        Останавливает текущее воспроизведение.
        """
        pass