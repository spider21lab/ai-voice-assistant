"""
Speech-to-Text implementation using Vosk (local, offline).
Supports: streaming recognition, silence detection, trigger word.
Реализация STT через Vosk (локально, оффлайн).
Поддерживает: потоковое распознавание, детекцию тишины, триггер-слово.
"""

import json
import struct
import time
from typing import Optional, Callable

from vosk import Model, KaldiRecognizer

from voice_assistant.core.config import STTSettings, get_config
from voice_assistant.core.logger import get_logger
from voice_assistant.stt.base import STTBase
from voice_assistant.utils.audio import AudioStream, calculate_rms

logger = get_logger(__name__)


class VoskSTT(STTBase):
    """
    Vosk-based Speech-to-Text implementation.
    Реализация STT на основе Vosk.
    """

    def __init__(self, config: Optional[STTSettings] = None):
        """
        Initialize Vosk STT.
        Инициализация STT через Vosk.

        Args:
            config: STT configuration / Конфигурация STT
        """
        self.config = config or get_config().stt
        self._model = self._load_model()

    def _load_model(self) -> Model:
        """
        Load Vosk model with error handling.
        Загрузка модели Vosk с обработкой ошибок.

        Returns:
            Loaded Vosk model / Загруженная модель Vosk
        """
        print(f"Loading Vosk model: {self.config.model_path}")
        try:
            return Model(str(self.config.model_path))
        except Exception as e:
            print(f"Error loading Vosk model: {e}")
            print("Please download model from: https://alphacephei.com/vosk/models")
            raise

    def _create_recognizer(self) -> KaldiRecognizer:
        """
        Create new recognizer instance.
        Создает новый экземпляр распознавателя.

        Returns:
            Configured KaldiRecognizer / Настроенный KaldiRecognizer
        """
        rec = KaldiRecognizer(self._model, self.config.sample_rate)
        rec.SetWords(True)
        return rec

    def recognize_trigger(
            self,
            audio_stream: AudioStream,
            trigger: str
    ) -> tuple[bool, Optional[str]]:
        """
        Listen for trigger word in audio stream.
        Слушает поток до обнаружения триггер-слова.
        """
        rec = self._create_recognizer()
        trigger_lower = trigger.lower()

        for chunk in audio_stream.read_chunks():
            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()
                if trigger_lower in text:
                    # Return text after trigger as context
                    # Возвращаем текст после триггера как контекст
                    context = text.replace(trigger_lower, "", 1).strip()
                    return True, context if context else None
        return False, None

    def recognize_command(
            self,
            audio_stream: AudioStream,
            on_partial: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Streaming command recognition with partial result callback.
        Потоковое распознавание команды с колбэком для промежуточных результатов.
        """
        rec = self._create_recognizer()

        silence_start: Optional[float] = None
        start_time = time.time()
        last_partial = ""

        for chunk in audio_stream.read_chunks():
            # Send to Vosk / Отправка в Vosk
            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text and text != last_partial:
                    last_partial = text
                    if on_partial:
                        on_partial(text)
            else:
                partial = json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text and partial_text != last_partial:
                    last_partial = partial_text
                    if on_partial:
                        on_partial(partial_text)

            # Silence detection by RMS / Детекция тишины по RMS
            rms = calculate_rms(chunk)
            if rms < self.config.silence_threshold:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > self.config.silence_timeout:
                    print("Silence detected - ending recognition")
                    break
            else:
                silence_start = None

            # Timeout check / Проверка таймаута
            if time.time() - start_time > self.config.record_timeout:
                print(f"Timeout reached ({self.config.record_timeout} seconds)")
                break

        # Final result / Финальный результат
        final = json.loads(rec.FinalResult())
        final_text = final.get("text", "").strip()

        return final_text or (last_partial.strip() if last_partial else None)