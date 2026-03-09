"""
Centralized prompt storage.
Easy to modify, test, and version.
Централизованное хранилище промптов.
Легко менять, тестировать и версионировать.
"""

from typing import Final

# System prompt for voice assistant / Системный промпт для голосового ассистента
SYSTEM_PROMPT: Final[str] = (
    "You are a concise and precise voice assistant, a best friend for a small child. "
    "Answer only to the point, without unnecessary words, but remember to be polite. "
    "If asked to explain something, do it as for preschoolers. "
    "Do not use Roman numerals - write their value in text. "
    "Do not use abbreviations (e.g., etc., i.e.) or acronyms. "
    "Do not start answers with 'Of course!', 'Here is the answer:', 'Sorry, but'. "
    "Give only brief answers, maximum 2-3 sentences."
)

# Error handling prompt / Промпт для обработки ошибок
ERROR_PROMPT: Final[str] = (
    "A technical error occurred. Briefly and friendly suggest the user repeat the question."
)

# Empty input prompt / Промпт для пустого ввода
EMPTY_INPUT_PROMPT: Final[str] = (
    "I did not catch that. Please say it again, I am listening."
)

# Trigger without command prompt / Промпт для триггера без команды
NO_COMMAND_PROMPT: Final[str] = (
    "I am here! What would you like to ask?"
)


def format_for_tts(text: str) -> str:
    """
    Clean text from markdown and special symbols before TTS.
    Очищает текст от маркдауна и спецсимволов перед озвучкой.

    Args:
        text: Input text / Входной текст

    Returns:
        Cleaned text / Очищенный текст
    """
    # Remove markdown formatting / Убираем markdown-разметку
    text = text.replace("**", "").replace("*", "").replace("`", "")
    # Remove extra whitespace / Убираем лишние пробелы
    text = ' '.join(text.split())
    return text