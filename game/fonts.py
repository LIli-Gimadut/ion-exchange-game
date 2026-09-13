"""Шрифты игры: Montserrat из assets/fonts (с запасным Arial, если файла нет).

Кэшируются по (size, bold), чтобы не пересоздавать каждый кадр.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_REGULAR = _DIR / "Montserrat-Regular.ttf"
_BOLD = _DIR / "Montserrat-Bold.ttf"


@lru_cache(maxsize=64)
def get(size: int, bold: bool = False) -> pygame.font.Font:
    # настоящие статические начертания (без синтетического «жирного», иначе
    # текст выглядит размытым и приплюснутым)
    path = _BOLD if bold else _REGULAR
    if path.exists():
        return pygame.font.Font(str(path), size)
    return pygame.font.SysFont("Arial", size, bold=bold)
