"""
Audio utilities: PyAudio wrappers, RMS calculation, player.
Утилиты для работы с аудио: обёртки PyAudio, RMS, плеер.
"""

import struct
import threading
import time
from typing import Iterator, Optional

import pyaudio

from voice_assistant.core.config import get_config


def calculate_rms(data: bytes) -> float:
    """
    Calculate RMS (volume) for audio chunk.
    Вычисляет RMS (громкость) для аудио-чанка.

    Args:
        data: Audio bytes / Байты аудио

    Returns:
        RMS value / Значение RMS
    """
    samples = struct.unpack(f'{len(data) // 2}h', data)
    if not samples:
        return 0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


class AudioStream:
    """
    PyAudio stream wrapper for chunk iteration.
    Обёртка над PyAudio stream для итерации по чанкам.
    """

    def __init__(self, device_index: Optional[int] = None):
        """
        Initialize audio stream.
        Инициализация аудио-потока.

        Args:
            device_index: Optional audio device index
                         Опциональный индекс аудио-устройства
        """
        config = get_config().stt
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.sample_rate,
            input=True,
            frames_per_buffer=config.chunk_size,
            input_device_index=device_index
        )

    def read_chunks(self) -> Iterator[bytes]:
        """
        Infinite generator of audio chunks.
        Бесконечный генератор аудио-чанков.

        Yields:
            Audio chunk bytes / Байты аудио-чанка
        """
        while True:
            yield self.stream.read(
                get_config().stt.chunk_size,
                exception_on_overflow=False
            )

    def close(self) -> None:
        """
        Close stream and PyAudio instance.
        Закрывает стрим и PyAudio.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def __enter__(self) -> 'AudioStream':
        return self

    def __exit__(self, *args) -> None:
        self.close()


class AudioPlayer:
    """
    Simple pygame-based player supporting bytes and files.
    Простой плеер на pygame с поддержкой bytes и файлов.
    """

    def __init__(self, sample_rate: int = 24000):
        """
        Initialize audio player.
        Инициализация аудио-плеера.

        Args:
            sample_rate: Audio sample rate / Частота дискретизации аудио
        """
        self.sample_rate = sample_rate
        self._initialized = False
        self._lock = threading.Lock()

    def _init(self) -> None:
        """
        Initialize pygame.mixer (lazy initialization).
        Инициализирует pygame.mixer (лениво).
        """
        if self._initialized:
            return
        try:
            import pygame
            pygame.mixer.init(frequency=self.sample_rate, channels=1, buffer=512)
            self._initialized = True
        except Exception as e:
            print(f"Warning: failed to initialize audio: {e}")

    def play_bytes(self, audio_bytes: bytes, block: bool = True) -> bool:
        """
        Play audio from bytes.
        Воспроизводит аудио из bytes.

        Args:
            audio_bytes: Audio data / Аудио-данные
            block: Block until playback completes / Блокировать до конца воспроизведения

        Returns:
            Success status / Статус успеха
        """
        self._init()
        if not self._initialized:
            return False

        import pygame
        import io

        with self._lock:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.load(io.BytesIO(audio_bytes))
                pygame.mixer.music.play()
                if block:
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                return True
            except Exception as e:
                print(f"Error playing audio: {e}")
                return False

    def play_file(self, filepath: str, block: bool = True) -> bool:
        """
        Play audio file.
        Воспроизводит аудиофайл.

        Args:
            filepath: Path to audio file / Путь к аудиофайлу
            block: Block until playback completes / Блокировать до конца воспроизведения

        Returns:
            Success status / Статус успеха
        """
        self._init()
        if not self._initialized:
            return False

        import pygame
        import os

        if not os.path.exists(filepath):
            print(f"Warning: file not found: {filepath}")
            return False

        with self._lock:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            if block:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
            return True

    def stop(self) -> None:
        """
        Stop playback.
        Останавливает воспроизведение.
        """
        if self._initialized:
            import pygame
            pygame.mixer.music.stop()