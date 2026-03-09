
# 🎙️ AI Voice Assistant

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
Локальный голосовой ассистент с поддержкой русского языка, сочетающий оффлайн-распознавание речи и мощные облачные языковые модели.

## ✨ Возможности

- 🔹 **Локальное распознавание речи** — Vosк работает без интернета
- 🔹 **Гибкое подключение к LLM** — поддержка любых моделей через OpenRouter
- 🔹 **Качественный синтез речи** — естественные голоса от Microsoft
- 🔹 **Низкая задержка** — потоковая обработка ответа
- 🔹 **Гибкая настройка** — конфигурация через `.env`
- 🔹 **Кроссплатформенность** — Windows, Linux, macOS

- 🔹 **Кроссплатформенность** — Windows, Linux, macOS

## 🛠 Технологии

| Компонент | Технология | Локально / Облако | Ссылка |
|-----------|-----------|-------------------|--------|
| 🎙️ Распознавание речи | Vosk | ✅ Локально | [GitHub](https://github.com/alphacep/vosk) |
| 🧠 Языковая модель | OpenRouter API | ☁️ Облако | [OpenRouter.ai](https://openrouter.ai) |
| 🗣️ Синтез речи | edge-tts | ☁️ Облако | [GitHub](https://github.com/rany2/edge-tts) |
| ⚙️ Конфигурация | pydantic-settings | ✅ Локально | [PyPI](https://pypi.org/project/pydantic-settings/) |
| 🔊 Аудио | PyAudio + pygame | ✅ Локально | [PyAudio](https://pypi.org/project/PyAudio/) |

## 🚀 Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/spider21lab/ai-voice-assistant.git
cd ai-voice-assistant

# Установить зависимости
pip install -e ".[dev]"

# Настроить окружение
cp .env.example .env

# Автоматическая загрузка модели Vosk
python scripts/download_models.py

# Или вручную: скачайте с https://alphacephei.com/vosk/models
# Распакуйте в папку models/model-small-ru

# Запустить
python -m voice_assistant
