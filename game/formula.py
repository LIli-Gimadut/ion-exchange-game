"""Отрисовка химических формул/уравнений с подстрочными индексами.

Цифры внутри формулы (идущие после буквы или ')') рисуются меньшим кеглем и со
смещением вниз; коэффициенты (цифры в начале токена) — обычным кеглем.
Стрелки ↑ ↓ и знак → выводятся как обычные символы (есть в Arial).
"""

from __future__ import annotations

import pygame

_cache: dict[tuple, pygame.Surface] = {}


def _is_letter(ch: str) -> bool:
    return ch.isalpha()


def render_formula(
    text: str,
    big: pygame.font.Font,
    small: pygame.font.Font,
    color: tuple[int, int, int],
) -> pygame.Surface:
    """Surface с формулой/уравнением; нижние индексы рисуются меньшим шрифтом."""
    key = (text, id(big), id(small), color)
    if key in _cache:
        return _cache[key]

    big_h = big.get_height()
    small_h = small.get_height()
    sub_drop = int(big_h * 0.34)  # насколько опустить индекс
    total_h = sub_drop + small_h
    total_h = max(total_h, big_h)

    glyphs: list[tuple[pygame.Surface, int]] = []  # (surface, y_offset)
    prev = ""
    for ch in text:
        is_subscript = ch.isdigit() and (_is_letter(prev) or prev == ")")
        if is_subscript:
            surf = small.render(ch, True, color)
            glyphs.append((surf, sub_drop))
        else:
            surf = big.render(ch, True, color)
            glyphs.append((surf, 0))
        prev = ch

    width = sum(s.get_width() for s, _ in glyphs)
    out = pygame.Surface((max(width, 1), total_h), pygame.SRCALPHA)
    x = 0
    for surf, dy in glyphs:
        out.blit(surf, (x, dy))
        x += surf.get_width()

    _cache[key] = out
    return out


def render_equation(
    segments,
    big: pygame.font.Font,
    small: pygame.font.Font,
    plain: tuple[int, int, int],
    highlight: tuple[int, int, int],
) -> pygame.Surface:
    """Уравнение из сегментов (текст, подсветка?) с нижними индексами.

    Сегменты с флагом подсветки (газ/осадок/вода) рисуются цветом `highlight`.
    """
    parts = [
        render_formula(text, big, small, highlight if hi else plain)
        for text, hi in segments
    ]
    width = sum(p.get_width() for p in parts)
    height = max((p.get_height() for p in parts), default=1)
    out = pygame.Surface((max(width, 1), height), pygame.SRCALPHA)
    x = 0
    for p in parts:
        out.blit(p, (x, 0))
        x += p.get_width()
    return out
