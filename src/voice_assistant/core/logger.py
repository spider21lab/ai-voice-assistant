"""
Logging configuration for the application.
Настройка логирования для всего приложения.
"""

import logging
import sys

from voice_assistant.core.config import get_config


def get_logger(name: str) -> logging.Logger:
    """
    Return configured logger instance.
    Возвращает настроенный логгер.

    Args:
        name: Logger name (usually __name__)
        name: Имя логгера (обычно __name__)

    Returns:
        Configured logger instance / Настроенный экземпляр логгера
    """
    config = get_config()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level))

    # Avoid duplicate handlers / Избегаем дублирования хендлеров
    if logger.handlers:
        return logger

    # Console handler / Консольный хендлер
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, config.log_level))

    # Format / Формат
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger