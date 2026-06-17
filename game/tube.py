"""Пробирка: позиция, раствор (цвет + уровень), отрисовка стекла и подписи."""

from __future__ import annotations

import pygame

from chemistry import Substance
from game import assets, config
from game.formula import render_formula

# Внутренняя полость в координатах изображения пробирки (логические 78×210).
WALL = 15
TOP = 32          # верх жидкости при полном заполнении
BOTTOM = 196      # дно полости
BOTTOM_R = 20


class Tube:
    def __init__(self, substance: Substance, x: int, y: int, level: float = 0.62):
        self.substance = substance
        self.x = x
        self.y = y
        self.level = level  # 0..1 доля заполнения

    # --- геометрия ---
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, config.TUBE_W, config.TUBE_H)

    @property
    def mouth(self) -> tuple[int, int]:
        """Точка горлышка (для струи при переливании)."""
        return self.x + config.TUBE_W // 2, self.y + 24

    # --- отрисовка ---
    def _liquid_surface(self, color, level: float) -> pygame.Surface:
        surf = pygame.Surface((config.TUBE_W, config.TUBE_H), pygame.SRCALPHA)
        level = max(0.0, min(1.0, level))
        if level <= 0:
            return surf
        span = BOTTOM - TOP
        y_top = BOTTOM - int(span * level)
        h = BOTTOM - y_top
        rect = pygame.Rect(WALL, y_top, config.TUBE_W - 2 * WALL, h)
        r = min(BOTTOM_R, h // 2)
        pygame.draw.rect(
            surf, color, rect,
            border_bottom_left_radius=r, border_bottom_right_radius=r,
        )
        # блик-мениск сверху жидкости
        if h > 6:
            top_band = pygame.Rect(WALL, y_top, config.TUBE_W - 2 * WALL, 4)
            light = tuple(min(255, c + 30) for c in color[:3]) + (color[3],)
            pygame.draw.rect(surf, light, top_band)
        return surf

    def draw(self, target: pygame.Surface, *, pos=None, tilt: float = 0.0,
             level: float | None = None, color=None):
        """Рисует жидкость + стекло. pos/tilt/level/color — для анимаций."""
        x, y = pos if pos else (self.x, self.y)
        level = self.level if level is None else level
        color = color if color is not None else self.substance.color

        comp0 = pygame.Surface((config.TUBE_W, config.TUBE_H), pygame.SRCALPHA)
        comp0.blit(self._liquid_surface(color, level), (0, 0))
        comp0.blit(assets.tube_image(), (0, 0))

        if tilt:
            comp0 = pygame.transform.rotate(comp0, tilt)
            r = comp0.get_rect(center=(x + config.TUBE_W // 2, y + config.TUBE_H // 2))
            target.blit(comp0, r.topleft)
        else:
            target.blit(comp0, (x, y))

    def draw_label(self, target: pygame.Surface, big, small, *, color=config.INK,
                   pos=None):
        x, y = pos if pos else (self.x, self.y)
        surf = render_formula(self.substance.formula, big, small, color)
        rect = surf.get_rect(midtop=(x + config.TUBE_W // 2, y + config.TUBE_H + 8))
        target.blit(surf, rect)
