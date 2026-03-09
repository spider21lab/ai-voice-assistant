#!/usr/bin/env python3
"""
Entry point for the application.
Run with: python -m voice_assistant
Точка входа в приложение.
Запуск: python -m voice_assistant
"""

import sys

from voice_assistant.assistant.agent import VoiceAssistant
from voice_assistant.core.config import get_config
from voice_assistant.core.logger import get_logger

logger = get_logger(__name__)


def main() -> int:
    """
    Main entry point.
    Основная точка входа.

    Returns:
        Exit code (0 for success, 1 for error)
        Код завершения (0 для успеха, 1 для ошибки)
    """
    # Load configuration / Загрузка конфигурации
    config = get_config()

    if config.debug:
        logger.debug("Debug mode enabled")

    # Initialize and run assistant / Инициализация и запуск ассистента
    try:
        assistant = VoiceAssistant()
        assistant.run()
        return 0
    except KeyboardInterrupt:
        print("Stopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())