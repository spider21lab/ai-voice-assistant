"""
Typed configuration management via pydantic-settings.
Supports: .env file, environment variables, validation.
"""

import os
from pathlib import Path
from typing import Literal, Optional, ClassVar

# 🔹 Важно: BaseModel для вложенных настроек, BaseSettings только для корня
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class STTSettings(BaseModel):
    """Speech-to-Text settings (Vosk)."""
    model_path: Path = Path("models/model-small-ru")
    sample_rate: int = 16000
    chunk_size: int = 1024
    silence_threshold: float = 600
    silence_timeout: float = 0.8
    record_timeout: float = 10.0
    audio_device_index: Optional[int] = None

    @field_validator("model_path")
    @classmethod
    def warn_if_missing(cls, v: Path) -> Path:
        if not v.exists():
            print(f"Warning: Vosk model not found: {v}")
            print("Download from: https://alphacephei.com/vosk/models")
        return v


class LLMSettings(BaseModel):
    """LLM settings (OpenRouter)."""
    api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    api_key: str  # Обязательное поле
    model: str = "meta-llama/llama-3.1-8b-instruct:free"
    max_tokens: int = 256
    temperature: float = 0.3
    timeout: int = 60
    stream: bool = True

    @field_validator("api_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v or (not v.startswith("sk-or-") and len(v) < 10):
            raise ValueError("API key must be set via LLM_API_KEY in .env")
        return v


class TTSSettings(BaseModel):
    """Text-to-Speech settings (edge-tts)."""
    voice: str = "ru-RU-SvetlanaNeural"
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None
    sample_rate: int = 24000

    @field_validator("cache_dir")
    @classmethod
    def resolve_cache(cls, v: Optional[Path]) -> Path:
        return v or Path("/tmp/ai-voice-assistant-tts")


class AppSettings(BaseSettings):
    """
    Global application settings.
    Only this class inherits from BaseSettings to load .env.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Project paths
    project_root: ClassVar[Path] = Path(__file__).resolve().parents[3]

    # 🔹 Flat fields with prefixes - Pydantic will map env vars automatically
    # STT settings (prefix: VOSK_)
    vosk_model_path: Path = Field(default=Path("models/model-small-ru"), alias="VOSK_MODEL_PATH")
    vosk_sample_rate: int = Field(default=16000, alias="VOSK_SAMPLE_RATE")
    vosk_chunk_size: int = Field(default=1024, alias="VOSK_CHUNK_SIZE")
    vosk_silence_threshold: float = Field(default=600, alias="VOSK_SILENCE_THRESHOLD")
    vosk_silence_timeout: float = Field(default=0.8, alias="VOSK_SILENCE_TIMEOUT")
    vosk_record_timeout: float = Field(default=10.0, alias="VOSK_RECORD_TIMEOUT")
    vosk_audio_device_index: Optional[int] = Field(default=None, alias="VOSK_AUDIO_DEVICE_INDEX")

    # LLM settings (prefix: LLM_)
    llm_api_url: str = Field(default="https://openrouter.ai/api/v1/chat/completions", alias="LLM_API_URL")
    llm_api_key: str = Field(alias="LLM_API_KEY")  # Обязательное
    llm_model: str = Field(default="meta-llama/llama-3.1-8b-instruct:free", alias="LLM_MODEL")
    llm_max_tokens: int = Field(default=256, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_timeout: int = Field(default=60, alias="LLM_TIMEOUT")
    llm_stream: bool = Field(default=True, alias="LLM_STREAM")

    # TTS settings (prefix: TTS_)
    tts_voice: str = Field(default="ru-RU-SvetlanaNeural", alias="TTS_VOICE")
    tts_cache_enabled: bool = Field(default=True, alias="TTS_CACHE_ENABLED")
    tts_cache_dir: Optional[Path] = Field(default=None, alias="TTS_CACHE_DIR")
    tts_sample_rate: int = Field(default=24000, alias="TTS_SAMPLE_RATE")

    # General settings (no prefix)
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    trigger_word: str = "alis"

    # 🔹 Nested settings objects (populated after loading flat fields)
    stt: Optional[STTSettings] = Field(default=None, exclude=True)
    llm: Optional[LLMSettings] = Field(default=None, exclude=True)
    tts: Optional[TTSSettings] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def build_nested_settings(self):
        """
        Build nested settings objects from flat fields after env loading.
        Это ключевой метод: создаёт STT/LLM/TTS объекты из загруженных переменных.
        """
        self.stt = STTSettings(
            model_path=self.vosk_model_path,
            sample_rate=self.vosk_sample_rate,
            chunk_size=self.vosk_chunk_size,
            silence_threshold=self.vosk_silence_threshold,
            silence_timeout=self.vosk_silence_timeout,
            record_timeout=self.vosk_record_timeout,
            audio_device_index=self.vosk_audio_device_index,
        )

        self.llm = LLMSettings(
            api_url=self.llm_api_url,
            api_key=self.llm_api_key,
            model=self.llm_model,
            max_tokens=self.llm_max_tokens,
            temperature=self.llm_temperature,
            timeout=self.llm_timeout,
            stream=self.llm_stream,
        )

        self.tts = TTSSettings(
            voice=self.tts_voice,
            cache_enabled=self.tts_cache_enabled,
            cache_dir=self.tts_cache_dir,
            sample_rate=self.tts_sample_rate,
        )

        return self

    @model_validator(mode="after")
    def setup_dirs(self):
        """Create necessary directories."""
        if self.tts and self.tts.cache_dir:
            self.tts.cache_dir.mkdir(parents=True, exist_ok=True)
        return self


# Global config instance
_config: Optional[AppSettings] = None


def get_config() -> AppSettings:
    """Return global config instance (initialized once)."""
    global _config
    if _config is None:
        _config = AppSettings()
    return _config


def reload_config() -> None:
    """Reload configuration (useful for testing)."""
    global _config
    _config = AppSettings()