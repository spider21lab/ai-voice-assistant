"""
Text processing utilities.
Утилиты для обработки текста.
"""

import re
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    Нормализует пробелы в тексте.

    Args:
        text: Input text / Входной текст

    Returns:
        Text with normalized whitespace / Текст с нормализованными пробелами
    """
    return ' '.join(text.split())


def remove_markdown(text: str) -> str:
    """
    Remove markdown formatting from text.
    Удаляет markdown-разметку из текста.

    Args:
        text: Input text / Входной текст

    Returns:
        Text without markdown / Текст без markdown
    """
    # Remove bold / Убираем жирный текст
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove italic / Убираем курсив
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove code / Убираем код
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove links / Убираем ссылки
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to max length.
    Обрезает текст до максимальной длины.

    Args:
        text: Input text / Входной текст
        max_length: Maximum length / Максимальная длина
        suffix: Suffix for truncated text / Суффикс для обрезанного текста

    Returns:
        Truncated text / Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix