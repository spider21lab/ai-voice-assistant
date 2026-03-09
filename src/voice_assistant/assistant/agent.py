"""
Main voice assistant orchestrator.
Coordinates: STT -> LLM -> TTS pipeline.
Главный класс голосового ассистента.
Оркестрирует пайплайн: STT -> LLM -> TTS.
"""

import time
import sys
from typing import Optional

from voice_assistant.core.config import get_config
from voice_assistant.core.logger import get_logger
from voice_assistant.stt.vosk import VoskSTT
from voice_assistant.llm.openrouter import OpenRouterClient
from voice_assistant.tts.edge import EdgeTTS
from voice_assistant.utils.audio import AudioStream
from voice_assistant.prompts import NO_COMMAND_PROMPT, EMPTY_INPUT_PROMPT

logger = get_logger(__name__)


class VoiceAssistant:
    """
    Main voice assistant class.
    Основной класс ассистента.
    """

    def __init__(self):
        """
        Initialize voice assistant components.
        Инициализация компонентов ассистента.
        """
        config = get_config()

        logger.info("Initializing assistant")

        # Initialize components / Инициализация компонентов
        self.stt = VoskSTT(config.stt)
        self.llm = OpenRouterClient(config.llm)
        self.tts = EdgeTTS(config.tts, debug=config.debug)

        # Settings / Настройки
        self.trigger_word = config.trigger_word

        logger.info(f"Ready. Trigger word: '{self.trigger_word}'")

    def _on_partial_stt(self, text: str) -> None:
        """
        Callback for displaying partial STT results.
        Колбэк для отображения частичного распознавания.
        """
        print(f"\rYou: {text}", end="", flush=True)

    def _on_token_llm(self, token: str) -> None:
        """
        Callback for streaming LLM tokens.
        Колбэк для стриминга токенов LLM.
        """
        print(token, end='', flush=True)

    def _on_tts_start(self) -> None:
        """
        Callback when TTS playback starts.
        Колбэк при старте озвучки.
        """
        print("\nSpeaking...", end='', flush=True)

    def run(self) -> None:
        """
        Main assistant loop.
        Основной цикл ассистента.
        """
        print(f"\nReady. Say '{self.trigger_word}' to start.\n")

        with AudioStream() as audio:
            try:
                while True:
                    # Wait for trigger / Ждём триггер
                    triggered, context = self.stt.recognize_trigger(
                        audio,
                        self.trigger_word
                    )

                    if not triggered:
                        continue

                    print(f"\nTrigger '{self.trigger_word}' recognized")

                    # Recognize command / Распознаём команду
                    command = self.stt.recognize_command(
                        audio,
                        on_partial=self._on_partial_stt
                    )

                    if not command:
                        print("\nWarning: no command recognized")
                        self.tts.say(EMPTY_INPUT_PROMPT)
                        continue

                    # Format LLM request / Формируем запрос к LLM
                    full_prompt = f"{context} {command}".strip() if context else command
                    print(f"\nSending to LLM: {full_prompt}")

                    # LLM request with streaming / Запрос к LLM со стримингом
                    print("Response: ", end='', flush=True)
                    response = self.llm.ask(
                        full_prompt,
                        on_token=self._on_token_llm
                    )
                    print()  # New line after streaming / Новая строка после стриминга

                    if not response:
                        continue

                    # TTS playback / Озвучка ответа
                    self.tts.say(response, on_start=self._on_tts_start)

                    # Small pause before next cycle / Небольшая пауза перед следующим циклом
                    time.sleep(0.3)

            except KeyboardInterrupt:
                logger.info("Stopped by user")
            except Exception as e:
                logger.exception(f"Critical error: {e}")
                print(f"\nError: {e}")
                sys.exit(1)
            finally:
                logger.info("Shutting down")
                self.tts.stop()