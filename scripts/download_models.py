#!/usr/bin/env python3
"""
Script for downloading models (Vosk, etc.).
Run: python scripts/download_models.py
Скрипт для загрузки моделей (Vosk и др.).
Запуск: python scripts/download_models.py
"""

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path

# Model definitions / Определения моделей
MODELS = {
    "small-ru": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
        "dest": "models/model-small-ru",
        "size_mb": 40,
        "extract": True,
    }
}


def download_file(url: str, dest: Path) -> bool:
    """
    Download file using wget or curl.
    Скачивает файл через wget или curl.

    Args:
        url: Download URL / URL для скачивания
        dest: Destination path / Путь назначения

    Returns:
        Success status / Статус успеха
    """
    tmp_file = dest.with_suffix(".tmp")

    # Try wget first, fallback to curl / Пробуем wget, fallback на curl
    if shutil.which("wget"):
        cmd = ["wget", "-q", "--show-progress", url, "-O", str(tmp_file)]
    elif shutil.which("curl"):
        cmd = ["curl", "-L", "-o", str(tmp_file), url]
    else:
        print("Error: neither wget nor curl found")
        return False

    try:
        subprocess.run(cmd, check=True)
        tmp_file.rename(dest)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading: {e}")
        return False


def download_model(name: str) -> bool:
    """
    Download specified model.
    Скачивает указанную модель.

    Args:
        name: Model name / Название модели

    Returns:
        Success status / Статус успеха
    """
    if name not in MODELS:
        print(f"Error: unknown model: {name}")
        print(f"Available: {', '.join(MODELS)}")
        return False

    model = MODELS[name]
    dest = Path(model["dest"])

    if dest.exists():
        print(f"Model already downloaded: {dest}")
        return True

    print(f"Downloading {name} ({model['size_mb']} MB)...")
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp_file = dest.with_suffix(".tmp")

    if not download_file(model["url"], tmp_file):
        return False

    # Extract if archive / Распаковка если архив
    if model.get("extract") and model["url"].endswith(".zip"):
        print("Extracting archive...")
        try:
            with zipfile.ZipFile(tmp_file, 'r') as zf:
                zf.extractall(dest.parent)
            tmp_file.unlink()
        except zipfile.BadZipFile:
            print("Error: invalid zip archive")
            return False

    print(f"Done: {dest}")
    return True


def main() -> int:
    """
    Main entry point.
    Основная точка входа.

    Returns:
        Exit code / Код завершения
    """
    parser = argparse.ArgumentParser(
        description="Download models for Voice Assistant"
    )
    parser.add_argument(
        "--model",
        choices=list(MODELS) + ["all"],
        default="all",
        help="Model to download (default: all)"
    )
    args = parser.parse_args()

    if args.model == "all":
        results = [download_model(name) for name in MODELS]
        if all(results):
            print("All models downloaded successfully")
            return 0
        else:
            print("Warning: some models failed to download")
            return 1
    else:
        return 0 if download_model(args.model) else 1


if __name__ == "__main__":
    exit(main())