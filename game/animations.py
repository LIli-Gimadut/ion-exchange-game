"""Анимации: переливание и эффекты результата (газ/осадок/вода/крестик).

Каждый объект-анимация имеет update(dt) и draw(...), и свойство `done`.
Эффекты результата рисуются поверх основной пробирки.
"""

from __future__ import annotations

import math
import random

import pygame

from game import config
from game.formula import render_formula
from game.tube import BOTTOM, TOP, WALL


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


class Pour:
    """Переливание из выбранной пробирки в основную.

    Двигает src от исходной позиции к точке слива справа-сверху от основной,
    наклоняет её, понижает уровень в src и поднимает в основной, рисует струю.
    """

    def __init__(self, main_tube, src_tube, src_start, mix_color):
        self.main = main_tube
        self.src = src_tube
        self.src_start = src_start
        self.mix_color = mix_color
        self.t = 0.0
        self.duration = config.POUR_TIME
        self._main_level0 = main_tube.level
        self._src_level0 = src_tube.level
        self._pour_pos = (main_tube.x + 58, main_tube.y - 36)

    @property
    def done(self) -> bool:
        return self.t >= self.duration

    @property
    def progress(self) -> float:
        return _clamp01(self.t / self.duration)

    def update(self, dt: float):
        self.t += dt

    def draw(self, surface, big, small):
        p = self.progress
        # фазы: A приближение, B наклон+слив, C завершение
        move = _clamp01(p / 0.35)
        sx = _lerp(self.src_start[0], self._pour_pos[0], move)
        sy = _lerp(self.src_start[1], self._pour_pos[1], move)

        pour = _clamp01((p - 0.35) / 0.5)
        tilt = _lerp(0, 58, pour)
        src_level = _lerp(self._src_level0, self._src_level0 * 0.35, pour)
        main_level = _lerp(self._main_level0, min(0.9, self._main_level0 + 0.28), pour)

        # основная пробирка (с растущим уровнем; цвет смешивается к mix_color)
        main_color = self.main.substance.color
        if pour > 0:
            main_color = _blend(main_color, self.mix_color, 0.5 * pour)
        self.main.draw(surface, level=main_level, color=main_color)

        # струя
        if 0 < pour < 1:
            self._draw_stream(surface)

        # выбранная пробирка (наклонённая)
        self.src.draw(surface, pos=(int(sx), int(sy)), tilt=tilt, level=src_level)

    def _draw_stream(self, surface):
        x0, y0 = self._pour_pos[0] + 6, self._pour_pos[1] + 40
        x1, y1 = self.main.x + config.TUBE_W // 2, self.main.y + 26
        for i in range(6):
            f = i / 6 + (self.t * 6 % 1) / 6
            x = _lerp(x0, x1, f)
            y = _lerp(y0, y1, f)
            pygame.draw.circle(surface, self.mix_color[:3], (int(x), int(y)), 3)


def _blend(c1, c2, t):
    return tuple(int(_lerp(c1[i], c2[i], t)) for i in range(4))


class _Effect:
    duration = config.RESULT_TIME

    def __init__(self):
        self.t = 0.0

    @property
    def done(self) -> bool:
        return self.t >= self.duration

    def update(self, dt: float):
        self.t += dt


class GasEffect(_Effect):
    """Пузырьки газа поднимаются в основной + формула газа со стрелкой вверх."""

    def __init__(self, star_formula: str):
        super().__init__()
        self.formula = star_formula + "↑"
        self.bubbles = [
            [random.uniform(WALL + 6, config.TUBE_W - WALL - 6),
             random.uniform(TOP + 30, BOTTOM),
             random.uniform(2, 5),
             random.uniform(28, 60)]
            for _ in range(14)
        ]

    def draw(self, surface, main_tube, big, small):
        ox, oy = main_tube.x, main_tube.y
        for b in self.bubbles:
            b[1] -= b[3] * (1 / config.FPS)
            if b[1] < TOP + 6:
                b[1] = BOTTOM
                b[0] = random.uniform(WALL + 6, config.TUBE_W - WALL - 6)
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(ox + b[0]), int(oy + b[1])), int(b[2]), 1)
        # формула газа проявляется над пробиркой — на одном уровне с подписью
        # осадка (oy - 14), не выше. Газы бесцветны → подпись белым.
        alpha = int(_lerp(0, 255, _clamp01(self.t / 0.4)))
        surf = render_formula(self.formula, big, small, (255, 255, 255)).copy()
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(ox + config.TUBE_W // 2, oy - 14))
        surface.blit(surf, rect)


class PrecipitateEffect(_Effect):
    """Помутнение раствора и оседание частиц осадка на дно + формула осадка."""

    def __init__(self, star_formula: str, color):
        super().__init__()
        self.formula = star_formula + "↓"
        self.color = color
        self.parts = [
            [random.uniform(WALL + 5, config.TUBE_W - WALL - 5),
             random.uniform(TOP + 20, TOP + 70),
             random.uniform(2, 4),
             random.uniform(BOTTOM - 30, BOTTOM - 4)]
            for _ in range(22)
        ]

    def draw(self, surface, main_tube, big, small):
        ox, oy = main_tube.x, main_tube.y
        for pt in self.parts:
            if pt[1] < pt[3]:
                pt[1] += 70 * (1 / config.FPS)
            pygame.draw.circle(surface, self.color[:3],
                               (int(ox + pt[0]), int(oy + pt[1])), int(pt[2]))
        # подпись осадка — цветом самого осадка, без обводки
        surf = render_formula(self.formula, big, small, self.color[:3])
        rect = surf.get_rect(center=(ox + config.TUBE_W // 2, oy - 14))
        surface.blit(surf, rect)


class WaterEffect(_Effect):
    """Плавное появление формулы воды H2O над пробиркой."""

    def __init__(self, star_formula: str = "H2O"):
        super().__init__()
        self.formula = star_formula

    def draw(self, surface, main_tube, big, small):
        ox, oy = main_tube.x, main_tube.y
        alpha = int(_lerp(0, 255, _clamp01(self.t / 0.6)))
        scale = _lerp(0.7, 1.0, _clamp01(self.t / 0.6))
        base = render_formula(self.formula, big, small, config.WATER_TINT)
        w = max(1, int(base.get_width() * scale))
        h = max(1, int(base.get_height() * scale))
        surf = pygame.transform.smoothscale(base, (w, h)).copy()
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(ox + config.TUBE_W // 2, oy - 16))
        surface.blit(surf, rect)


class WrongEffect(_Effect):
    """Красный крест над основной пробиркой + тряска (offset для сцены)."""

    duration = config.RESULT_TIME

    def shake_offset(self) -> tuple[int, int]:
        if self.t > config.SHAKE_TIME:
            return (0, 0)
        amp = _lerp(8, 0, self.t / config.SHAKE_TIME)
        return (int(math.sin(self.t * 60) * amp), 0)

    def draw(self, surface, main_tube, big, small):
        ox, oy = main_tube.x, main_tube.y
        cx, cy = ox + config.TUBE_W // 2, oy + config.TUBE_H // 2
        s = 34
        alpha = int(_lerp(0, 255, _clamp01(self.t / 0.25)))
        layer = pygame.Surface((s * 2 + 12, s * 2 + 12), pygame.SRCALPHA)
        c = (s + 6, s + 6)
        pygame.draw.line(layer, config.RED, (c[0] - s, c[1] - s),
                         (c[0] + s, c[1] + s), 10)
        pygame.draw.line(layer, config.RED, (c[0] + s, c[1] - s),
                         (c[0] - s, c[1] + s), 10)
        layer.set_alpha(alpha)
        surface.blit(layer, layer.get_rect(center=(cx, cy)))


def make_effect(effect: str, star_formula: str, color) -> _Effect:
    if effect == "GAS":
        return GasEffect(star_formula)
    if effect == "PRECIPITATE":
        return PrecipitateEffect(star_formula, color)
    return WaterEffect(star_formula)
