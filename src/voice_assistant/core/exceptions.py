"""
Custom exceptions for the application.
Кастомные исключения для приложения.
"""


class VoiceAssistantError(Exception):
    """Base exception for voice assistant errors.
    Базовое исключение для ошибок голосового ассистента."""
    pass


class STTError(VoiceAssistantError):
    """Speech-to-Text processing error.
    Ошибка обработки распознавания речи."""
    pass


class LLMError(VoiceAssistantError):
    """LLM API communication error.
    Ошибка взаимодействия с API LLM."""
    pass


class TTSError(VoiceAssistantError):
    """Text-to-Speech processing error.
    Ошибка обработки синтеза речи."""
    pass


class ConfigurationError(VoiceAssistantError):
    """Configuration validation error.
    Ошибка валидации конфигурации."""
    pass