"""
Abstract base interface for LLM providers.
Абстрактный базовый интерфейс для провайдеров LLM.
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Iterator


class LLMBase(ABC):
    """
    Abstract interface for LLM providers.
    Абстрактный интерфейс для провайдеров LLM.
    """

    @abstractmethod
    def ask(
            self,
            prompt: str,
            on_token: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Send request and return full response.
        Отправляет запрос и возвращает полный ответ.

        Args:
            prompt: User input / Пользовательский ввод
            on_token: Optional callback for streaming tokens
                     Опциональный колбэк для стриминга токенов

        Returns:
            Full response text / Полный текст ответа
        """
        pass

    @abstractmethod
    def ask_stream(
            self,
            prompt: str,
            on_token: Callable[[str], None]
    ) -> Iterator[str]:
        """
        Streaming request: on_token called for each token.
        Стриминговый запрос: on_token вызывается для каждого токена.

        Args:
            prompt: User input / Пользовательский ввод
            on_token: Callback for each received token
                     Колбэк для каждого полученного токена

        Yields:
            Individual tokens / Отдельные токены
        """
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """
        Clear conversation history.
        Очищает историю диалога.
        """
        pass