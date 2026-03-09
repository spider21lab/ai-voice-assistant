"""
LLM client for OpenRouter (OpenAI-compatible API).
Supports: token streaming, conversation history, error handling.
Клиент LLM для OpenRouter (OpenAI-compatible API).
Поддерживает: стриминг токенов, историю диалога, обработку ошибок.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Iterator, List

import requests

from voice_assistant.core.config import LLMSettings, get_config
from voice_assistant.core.logger import get_logger
from voice_assistant.llm.base import LLMBase
from voice_assistant.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


@dataclass
class Message:
    """
    Message structure for conversation history.
    Структура сообщения для истории диалога.
    """
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


class OpenRouterClient(LLMBase):
    """
    Client for OpenRouter API.
    Клиент для API OpenRouter.
    """

    def __init__(self, config: Optional[LLMSettings] = None):
        """
        Initialize OpenRouter client.
        Инициализация клиента OpenRouter.

        Args:
            config: LLM configuration / Конфигурация LLM
        """
        self.config = config or get_config().llm
        self._session = requests.Session()
        self._history: List[Message] = [
            Message(role="system", content=SYSTEM_PROMPT)
        ]

    def _prepare_payload(self, prompt: str, stream: bool = False) -> dict:
        """
        Prepare request payload for API.
        Готовит payload для API-запроса.

        Args:
            prompt: User prompt / Пользовательский промпт
            stream: Enable streaming mode / Включить режим стриминга

        Returns:
            API request payload / Payload для запроса API
        """
        # Add user request to history / Добавляем пользовательский запрос в историю
        self._history.append(Message(role="user", content=prompt))

        # Limit history (excluding system prompt) / Ограничиваем историю (без system-промпта)
        if len(self._history) > 10:  # system + 9 latest messages
            self._history = [self._history[0]] + self._history[-9:]

        return {
            "model": self.config.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in self._history
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream,
            "stop": ["\n\n", "User:", "###"]
        }

    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        """
        Parse chunk from OpenRouter SSE stream.
        Handles edge cases: empty choices, missing fields.
        """
        line = line.strip()
        if not line or line.startswith(":"):
            return None
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                return None
            try:
                chunk = json.loads(data)
                # 🔹 Безопасное извлечение токена
                choices = chunk.get("choices", [])
                if not choices:
                    return None
                delta = choices[0].get("delta", {})
                if not delta:
                    return None
                return delta.get("content")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON chunk: {line[:100]}")
                return None
            except (KeyError, IndexError, AttributeError) as e:
                logger.warning(f"Chunk parsing error: {e}, chunk: {chunk}")
                return None
        return None

    def ask_stream(
            self,
            prompt: str,
            on_token: Callable[[str], None]
    ) -> Iterator[str]:
        """
        Streaming request with callback for each token.
        """
        payload = self._prepare_payload(prompt, stream=True)
        full_response: List[str] = []

        try:
            with self._session.post(
                    self.config.api_url,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                        "X-Title": "Voice Assistant"
                    },
                    json=payload,
                    stream=True,
                    timeout=self.config.timeout
            ) as response:
                # 🔹 Явно указываем кодировку для корректной обработки кириллицы
                response.encoding = "utf-8"
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    token = self._parse_stream_chunk(line)
                    if token:
                        full_response.append(token)
                        on_token(token)
                        yield token

                # Save response to history
                if full_response:
                    self._history.append(
                        Message(role="assistant", content="".join(full_response))
                    )

        except requests.exceptions.Timeout:
            on_token("\n[Timeout: connection error]")
        except requests.exceptions.ConnectionError:
            on_token("\n[Connection error: no internet]")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            on_token(f"\n[Error: {type(e).__name__}]")

    def ask(
            self,
            prompt: str,
            on_token: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Regular request (or streaming if enabled in config).
        If on_token provided, uses streaming mode.
        Обычный запрос (или стриминг, если включено в конфиге).
        Если передан on_token — используется стриминг.
        """
        if on_token and self.config.stream:
            # Streaming mode / Стриминговый режим
            tokens = list(self.ask_stream(prompt, on_token))
            return "".join(tokens).strip()
        else:
            # Regular mode / Обычный режим
            payload = self._prepare_payload(prompt, stream=False)

            try:
                response = self._session.post(
                    self.config.api_url,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()

                data = response.json()
                assistant_reply = data["choices"][0]["message"]["content"].strip()

                # Save to history / Сохраняем в историю
                self._history.append(Message(role="assistant", content=assistant_reply))

                return assistant_reply

            except requests.exceptions.Timeout:
                print("Error: timeout while connecting to LLM")
                return "Sorry, timeout while connecting to AI."
            except requests.exceptions.ConnectionError:
                print("Error: no internet connection")
                return "Error: no internet connection."
            except Exception as e:
                logger.error(f"LLM error: {e}")
                print(f"Error: {e}")
                return "Error processing request."

    def clear_history(self) -> None:
        """
        Clear conversation history, keeping only system prompt.
        Очищает историю, оставляя только system-промпт.
        """
        self._history = [self._history[0]] if self._history else [
            Message(role="system", content=SYSTEM_PROMPT)
        ]

    def get_history(self) -> List[dict]:
        """
        Return history for debugging.
        Возвращает историю для отладки.

        Returns:
            List of message dictionaries / Список словарей сообщений
        """
        return [{"role": m.role, "content": m.content} for m in self._history]