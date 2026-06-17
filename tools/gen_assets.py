"""Авторская SVG-пробирка → PNG (через pygame/SDL_image, без системного cairo).

Запуск напрямую: `uv run python tools/gen_assets.py` — пересоздаёт ассеты.
Также вызывается из game.assets при отсутствии PNG.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "assets" / "svg"
PNG_DIR = ROOT / "assets" / "png"

# Логический размер совпадает с config.TUBE_W/TUBE_H; держим локально, чтобы
# tools не зависел от pygame-конфига на этапе импорта.
TUBE_W, TUBE_H = 78, 210
SCALE = 2

# Внутренняя область стекла (для отрисовки жидкости в коде).
WALL = 14          # толщина стенки/левый отступ полости
LIP_Y = 24         # верх горлышка
BODY_BOTTOM = 198  # центр скругления дна
BOTTOM_R = 24      # радиус скругления дна


def tube_svg() -> str:
    """SVG пустой стеклянной пробирки: горлышко, корпус, блик."""
    left = WALL
    right = TUBE_W - WALL
    cx = TUBE_W / 2
    body = (
        f"M{left},{LIP_Y} "
        f"L{left},{BODY_BOTTOM - BOTTOM_R} "
        f"Q{left},{BODY_BOTTOM} {cx},{BODY_BOTTOM} "
        f"Q{right},{BODY_BOTTOM} {right},{BODY_BOTTOM - BOTTOM_R} "
        f"L{right},{LIP_Y} Z"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TUBE_W} {TUBE_H}">
  <!-- стеклянный корпус: лёгкая полупрозрачная заливка + контур -->
  <path d="{body}" fill="#dff0f6" fill-opacity="0.35"
        stroke="#7fb0c2" stroke-width="3" stroke-linejoin="round"/>
  <!-- горлышко (ободок) -->
  <ellipse cx="{cx}" cy="{LIP_Y}" rx="{(right - left) / 2 + 3}" ry="6"
           fill="#eef7fb" fill-opacity="0.6" stroke="#7fb0c2" stroke-width="3"/>
  <!-- вертикальный блик -->
  <rect x="{left + 6}" y="{LIP_Y + 14}" width="6" height="120" rx="3"
        fill="#ffffff" fill-opacity="0.55"/>
</svg>"""


def build(force: bool = True) -> Path:
    """Генерирует SVG и PNG пробирки. Возвращает путь к PNG."""
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    svg_path = SVG_DIR / "tube.svg"
    png_path = PNG_DIR / "tube.png"
    svg_path.write_text(tube_svg(), encoding="utf-8")

    if png_path.exists() and not force:
        return png_path

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))

    surface = pygame.image.load_sized_svg(
        str(svg_path), (TUBE_W * SCALE, TUBE_H * SCALE)
    )
    pygame.image.save(surface, str(png_path))
    return png_path


if __name__ == "__main__":
    out = build(force=True)
    print(f"Готово: {out} ({out.stat().st_size} байт)")
