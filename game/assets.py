"""Загрузка графических ассетов; генерация PNG из SVG при отсутствии."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

from game import config

_PNG = Path(__file__).resolve().parent.parent / "assets" / "png" / "tube.png"


@lru_cache(maxsize=1)
def tube_image() -> pygame.Surface:
    """PNG стеклянной пробирки, масштабированный к TUBE_W×TUBE_H."""
    if not _PNG.exists():
        from tools import gen_assets

        gen_assets.build(force=True)
    img = pygame.image.load(str(_PNG)).convert_alpha()
    return pygame.transform.smoothscale(img, (config.TUBE_W, config.TUBE_H))
