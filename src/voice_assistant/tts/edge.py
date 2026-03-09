"""
Text-to-Speech implementation using edge-tts.
Supports: caching, auto language detection, async playback.
Реализация TTS через edge-tts.
Поддерживает: кэширование, авто-определение языка, асинхронное воспроизведение.
"""

import asyncio
import hashlib
import tempfile
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Callable

from voice_assistant.core.config import TTSSettings, get_config
from voice_assistant.core.logger import get_logger
from voice_assistant.tts.base import TTSBase
from voice_assistant.utils.audio import AudioPlayer
from voice_assistant.prompts import format_for_tts

logger = get_logger(__name__)


class EdgeTTS(TTSBase):
    """
    edge-tts based Text-to-Speech implementation.
    Реализация TTS на основе edge-tts.
    """

    # Supported voices / Поддерживаемые голоса
    VOICES = {
        "ru": {
            "kseniya": "ru-RU-SvetlanaNeural",
            "natasha": "ru-RU-DariyaNeural",
            "dmitry": "ru-RU-DmitryNeural",
        },
        "en": {
            "jenny": "en-US-JennyNeural",
            "guy": "en-US-GuyNeural",
            "emma": "en-GB-EmmaNeural",
        }
    }

    def __init__(
            self,
            config: Optional[TTSSettings] = None,
            debug: bool = False
    ):
        """
        Initialize edge-tts TTS.
        Инициализация TTS через edge-tts.

        Args:
            config: TTS configuration / Конфигурация TTS
            debug: Enable debug output / Включить отладочный вывод
        """
        self.config = config or get_config().tts
        self.debug = debug
        self._cache: dict[str, Path] = {}
        self._lock = threading.Lock()
        self._player = AudioPlayer(sample_rate=self.config.sample_rate)
        self._loop = asyncio.new_event_loop()

        # Warm up edge-tts connection / Предзагрузка соединения с edge-tts
        self._warmup()

    def _warmup(self) -> None:
        """
        Warm up edge-tts connection.
        Разогревает соединение с edge-tts.
        """
        try:
            asyncio.run_coroutine_threadsafe(
                self._generate_audio("ready", self.config.voice),
                self._loop
            ).result(timeout=5)
        except Exception:
            pass  # Ignore warmup errors / Игнорируем ошибки при разогреве

    def _detect_language(self, text: str) -> str:
        """
        Detect language by character analysis.
        Определяет язык по символам.

        Args:
            text: Input text / Входной текст

        Returns:
            Language code: 'ru' or 'en' / Код языка: 'ru' или 'en'
        """
        if not text:
            return "ru"
        cyrillic = sum(1 for c in text if 'а' <= c <= 'я' or 'А' <= c <= 'Я' or c == 'ё')
        latin = sum(1 for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
        return 'ru' if cyrillic >= latin else 'en'

    def _get_voice(self, lang: str, voice_name: Optional[str] = None) -> str:
        """
        Get voice ID for language.
        Возвращает ID голоса для языка.

        Args:
            lang: Language code / Код языка
            voice_name: Optional voice name / Опциональное имя голоса

        Returns:
            Voice ID string / Строка ID голоса
        """
        if voice_name and voice_name in self.VOICES.get(lang, {}):
            return self.VOICES[lang][voice_name]
        # Fallback to default voice / Fallback на дефолтный голос
        return self.VOICES.get(lang, {}).get("kseniya" if lang == "ru" else "jenny")

    async def _generate_audio(self, text: str, voice: str) -> Optional[bytes]:
        """Generate audio as bytes (in-memory, no disk write)."""
        try:
            import edge_tts

            # 🔹 Очистка текста от невалидных символов
            text = text.encode("utf-8", errors="ignore").decode("utf-8")
            text = text.strip()

            if not text:
                print("Warning: empty text for TTS")
                return None

            buffer = BytesIO()
            communicate = edge_tts.Communicate(text, voice)

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])

            buffer.seek(0)
            result = buffer.read()

            if result and len(result) > 100:
                return result
            else:
                print(f"Warning: generated audio too small ({len(result) if result else 0} bytes)")
                return None

        except ImportError:
            print("Error: edge-tts not installed. Run: pip install edge-tts")
            return None
        except Exception as e:
            logger.error(f"edge-tts error: {e}")
            print(f"Error generating audio: {e}")
            print(f"Text that failed: {text[:200]}")  # 🔹 Лог для отладки
            return None

    def _get_cache_key(self, text: str, voice: str) -> str:
        """
        Generate cache key for text-voice combination.
        Генерирует ключ для кэша комбинации текст-голос.

        Args:
            text: Input text / Входной текст
            voice: Voice ID / ID голоса

        Returns:
            MD5 hash string / Строка хэша MD5
        """
        return hashlib.md5(f"{text.strip()}|{voice}".encode()).hexdigest()

    def say(
            self,
            text: str,
            block: bool = True,
            on_start: Optional[Callable] = None
    ) -> bool:
        """
        Speak the text.
        Озвучивает текст.
        """
        if not text or not text.strip():
            return False

        # Format text for TTS / Форматирование текста для TTS
        text = format_for_tts(text)

        lang = self._detect_language(text)
        voice = self._get_voice(lang)
        cache_key = self._get_cache_key(text, voice)

        # Check cache / Проверка кэша
        if self.config.cache_enabled and cache_key in self._cache:
            cached_path = self._cache[cache_key]
            if cached_path.exists():
                if self.debug:
                    print("TTS: using cached audio")
                if on_start:
                    on_start()
                return self._player.play_file(str(cached_path), block=block)

        # Generate audio / Генерация аудио
        start = time.time()
        audio_bytes = self._loop.run_until_complete(
            self._generate_audio(text, voice)
        )

        if not audio_bytes:
            print("Error: failed to generate audio")
            return False

        if self.debug:
            print(f"TTS generation time: {time.time() - start:.2f} seconds")

        # Cache to disk if enabled / Кэширование на диск если включено
        if self.config.cache_enabled and self.config.cache_dir:
            cache_path = self.config.cache_dir / f"{cache_key}.mp3"
            cache_path.write_bytes(audio_bytes)
            self._cache[cache_key] = cache_path

        # Playback / Воспроизведение
        if on_start:
            on_start()
        return self._player.play_bytes(audio_bytes, block=block)

    def stop(self) -> None:
        """
        Stop current playback.
        Останавливает текущее воспроизведение.
        """
        self._player.stop()

    def clear_cache(self) -> None:
        """
        Clear cached audio files.
        Очищает кэш аудиофайлов.
        """
        if not self.config.cache_enabled:
            return
        for path in self._cache.values():
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        self._cache.clear()
        if self.debug:
            print("TTS cache cleared")