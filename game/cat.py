"""Котик-химик, выглядывающий из правого края фона.

Рисуется процедурно (без ассетов) на surface с 2× сглаживанием. Три настроения:
`neutral` — обычное, `happy` — при верном ответе, `sad` — при неверном.
Результаты кэшируются по (mood, размер), т.к. меняются редко.
"""

from __future__ import annotations

from functools import lru_cache

import pygame

# --- палитра котика ---
FUR = (236, 166, 84)
FUR_SH = (212, 140, 60)
STRIPE = (205, 128, 54)
EAR_IN = (247, 203, 196)
MUZZLE = (250, 242, 229)
NOSE = (198, 104, 120)
MOUTH = (122, 72, 72)
EYE = (46, 38, 54)
WHITE = (255, 255, 255)
GOGGLE = (255, 209, 102)          # #FFD166 — золотая оправа
GLASS = (150, 205, 245)
COAT = (247, 248, 252)
COAT_SH = (211, 218, 234)
BLUSH = (245, 148, 158, 215)      # чёткий розовый кружок на щеке
TEAR = (120, 190, 240)

# логический размер холста котика (до масштабирования)
W, H = 360, 430


@lru_cache(maxsize=12)
def _render(mood: str, w: int, h: int) -> pygame.Surface:
    S = 2
    surf = pygame.Surface((w * S, h * S), pygame.SRCALPHA)

    def ell(color, cx, cy, rx, ry, width=0):
        pygame.draw.ellipse(surf, color,
                            pygame.Rect((cx - rx) * S, (cy - ry) * S,
                                        2 * rx * S, 2 * ry * S),
                            width * S if width else 0)

    def circ(color, cx, cy, r, width=0):
        pygame.draw.circle(surf, color, (int(cx * S), int(cy * S)),
                           int(r * S), width * S if width else 0)

    def poly(color, pts, width=0):
        pygame.draw.polygon(surf, color, [(x * S, y * S) for x, y in pts],
                            width * S if width else 0)

    def line(color, a, b, width=1):
        pygame.draw.line(surf, color, (a[0] * S, a[1] * S), (b[0] * S, b[1] * S),
                         max(1, width * S))

    def curve(color, cx, cy, half_w, sag, thick):
        pts, n = [], 18
        for i in range(n + 1):
            t = -1 + 2 * i / n
            pts.append(((cx + t * half_w) * S, (cy + sag * (1 - t * t)) * S))
        pygame.draw.lines(surf, color, False, pts, max(1, thick * S))

    hx, hy, rx, ry = 190, 210, 108, 98

    # плечи в халате (за головой)
    ell(FUR_SH, hx, 400, 150, 96)
    ell(COAT, hx - 6, 410, 128, 82)
    poly(COAT, [(hx, 300), (hx - 62, 330), (hx - 30, 388)])   # левый лацкан
    poly(COAT, [(hx, 300), (hx + 62, 330), (hx + 30, 388)])   # правый лацкан
    line(COAT_SH, (hx, 306), (hx - 30, 384), 2)
    line(COAT_SH, (hx, 306), (hx + 30, 384), 2)

    # уши — пошире; основание уходит под голову, чтобы ухо не «отрывалось».
    # при грусти кончик уха надламывается и печально свисает вниз.
    droop = mood == "sad"
    for sx in (-1, 1):
        base_out = (hx + sx * 82, hy - 56)
        base_in = (hx + sx * 14, hy - 84)
        if droop:
            fold_out = (hx + sx * 76, hy - 104)
            fold_in = (hx + sx * 26, hy - 108)
            tip = (hx + sx * 116, hy - 78)
            stand = [base_out, fold_out, fold_in, base_in]
            poly(FUR, stand)                       # стоячее основание уха
            poly(FUR_SH, [fold_out, tip, fold_in])  # надломленный кончик (тыл)
            cxx = sum(p[0] for p in stand) / 4
            cyy = sum(p[1] for p in stand) / 4
            poly(EAR_IN, [(cxx + (px - cxx) * 0.5, cyy + (py - cyy) * 0.5)
                          for px, py in stand])
        else:
            tri = [base_out, (hx + sx * 100, hy - 152), base_in]
            poly(FUR, tri)
            cxx = sum(p[0] for p in tri) / 3
            cyy = sum(p[1] for p in tri) / 3
            poly(EAR_IN, [(cxx + (px - cxx) * 0.58, cyy + (py - cyy) * 0.58)
                          for px, py in tri])

    # голова
    ell(FUR, hx, hy, rx, ry)
    # тигровые полоски на лбу
    for dx in (-30, 0, 30):
        line(STRIPE, (hx + dx, hy - 92), (hx + dx * 0.7, hy - 58), 5)

    # мордочка (светлое пятно)
    ell(MUZZLE, hx, hy + 40, 64, 48)

    # очки-гогглы химика на лбу (как в начале, но чуть ниже)
    for sx in (-1, 1):
        gx, gy = hx + sx * 42, hy - 52
        circ(GLASS, gx, gy, 24)
        circ(GOGGLE, gx, gy, 24, 5)
    line(GOGGLE, (hx - 42, hy - 52), (hx + 42, hy - 52), 5)     # перемычка
    line(GOGGLE, (hx - 66, hy - 54), (hx - 96, hy - 68), 5)     # ремешок

    ex, ey = 44, hy - 6          # смещение и высота глаз
    # --- глаза по настроению ---
    if mood == "happy":
        for sx in (-1, 1):
            curve(EYE, hx + sx * ex, ey + 4, 18, 10, 6)         # ◡ довольные
        # розовый кружок румянца на щеках
        for sx in (-1, 1):
            circ(BLUSH, hx + sx * 60, hy + 30, 14)
    elif mood == "sad":
        for sx in (-1, 1):
            circ(EYE, hx + sx * ex, ey + 6, 13)
            circ(WHITE, hx + sx * ex - 4, ey + 1, 4)
            # печальные брови (внутренние концы приподняты)
            line(FUR_SH, (hx + sx * ex - sx * 18, ey - 24),
                 (hx + sx * ex + sx * 12, ey - 14), 5)
        # слеза под левым глазом
        circ(TEAR, hx - ex - 2, ey + 26, 6)
        poly(TEAR, [(hx - ex - 8, ey + 24), (hx - ex + 4, ey + 24),
                    (hx - ex - 2, ey + 12)])
    else:  # neutral
        for sx in (-1, 1):
            circ(EYE, hx + sx * ex, ey, 15)
            circ(WHITE, hx + sx * ex - 5, ey - 5, 5)

    # нос
    poly(NOSE, [(hx - 11, hy + 24), (hx + 11, hy + 24), (hx, hy + 38)])
    line(MOUTH, (hx, hy + 38), (hx, hy + 50), 3)

    # рот по настроению
    if mood == "happy":
        curve(MOUTH, hx, hy + 50, 34, 18, 6)
    elif mood == "sad":
        curve(MOUTH, hx, hy + 64, 26, -13, 6)
    else:
        curve(MOUTH, hx, hy + 52, 18, 6, 5)

    # усы
    for dy, off in ((0, 0), (7, 6), (14, 14)):
        line(WHITE, (hx - 34, hy + 40 + dy // 2), (hx - 104, hy + 30 + off), 2)
        line(WHITE, (hx + 34, hy + 40 + dy // 2), (hx + 104, hy + 30 + off), 2)

    # лапка + колба (химик) на переднем плане слева
    _flask(poly, ell, circ, line, hx - 96, hy + 96)

    return pygame.transform.smoothscale(surf, (w, h))


def _flask(poly, ell, circ, line, x, y):
    glass = (223, 236, 240)
    liq = (120, 210, 150)
    # колба Эрленмейера
    poly(glass, [(x - 26, y + 40), (x - 8, y - 26), (x + 8, y - 26),
                 (x + 26, y + 40)])
    poly((208, 224, 228), [(x - 8, y - 34), (x + 8, y - 34),
                           (x + 8, y - 26), (x - 8, y - 26)])  # горлышко
    poly(liq, [(x - 20, y + 34), (x - 3, y + 4), (x + 3, y + 4), (x + 20, y + 34)])
    circ((150, 235, 180), x - 6, y + 20, 3)
    circ((150, 235, 180), x + 7, y + 26, 2)
    # лапка держит колбу
    circ((236, 166, 84), x + 30, y + 30, 20)
    circ((212, 140, 60), x + 20, y + 20, 7)


def draw(surface: pygame.Surface, cx: int, bottom_y: int, mood: str = "neutral",
         scale: float = 1.0):
    """Рисует котика; низ фигуры — на уровне `bottom_y`, центр по x — `cx`.
    Правый край обрезается краем экрана."""
    w, h = int(W * scale), int(H * scale)
    cat = _render(mood, w, h)
    surface.blit(cat, cat.get_rect(midbottom=(cx, bottom_y)))
