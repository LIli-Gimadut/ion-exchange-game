"""Сцена сокращения ионов-зрителей (уровень 2, механика №6).

Сверху — молекулярное уравнение. Ниже — полное ионное, разбитое на кликабельные
плитки. Игрок кликает ионы-зрители: верные зачёркиваются (анимация), клик по
участнику/молекуле — красная вспышка. Когда все зрители сокращены, кнопка
«Сократить» раскрывает внизу сокращённое ионное уравнение.
"""

from __future__ import annotations

import random

import pygame

from chemistry.ionic import is_strong_electrolyte
from game import config
from game.cancel import CancelGame
from game.formula import render_equation
from game.round import generate

GREEN = config.DROP_OK
TILE_BG = (255, 255, 255)
TILE_BORDER = (170, 186, 200)
ION_BORDER = (120, 170, 210)
STRUCK = (150, 160, 170)
BTN_OFF = (188, 200, 212)
ERR_TIME = 0.5


def _gradient(size, top, bottom) -> pygame.Surface:
    surf = pygame.Surface(size)
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (size[0], y))
    return surf


class CancelScene:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.bg = _gradient((config.WIDTH, config.HEIGHT),
                            config.BG_TOP, config.BG_BOTTOM)
        self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_eq = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_eq_sub = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_tile = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_tile_sm = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_hint = pygame.font.SysFont("Arial", 18)
        self.font_btn = pygame.font.SysFont("Arial", 22, bold=True)
        self._hit: dict[str, pygame.Rect] = {}
        self.err_tid: str | None = None
        self.err_t = 0.0
        self.msg = ""
        self.new_reaction()

    def new_reaction(self):
        # оба реагента — сильные электролиты: иначе движок уровня 1 допускает
        # химически некорректные «вытеснения» слабыми кислотами.
        for _ in range(200):
            r = generate(self.rng)
            if is_strong_electrolyte(r.main) and is_strong_electrolyte(r.correct):
                break
        self.game = CancelGame(r.main, r.correct)
        self.err_tid = None
        self.msg = "Зачеркни ионы-зрители (одинаковые слева и справа)"

    # --- события ---
    def handle_event(self, e):
        if e.type != pygame.MOUSEBUTTONDOWN or e.button != 1:
            return
        for name, rect in self._hit.items():
            if not rect.collidepoint(e.pos):
                continue
            if name == "reduce":
                if self.game.reveal():
                    self.msg = "Готово! Сокращённое ионное — внизу"
                else:
                    self.msg = "Сначала зачеркни всех зрителей"
                return
            if name == "new":
                self.new_reaction()
                return
            if name.startswith("tile:"):
                self._click_tile(name[5:])
                return

    def _click_tile(self, tid):
        if self.game.revealed:
            return
        if self.game.click(tid):
            t = self.game.tile(tid)
            self.msg = f"{t.text} — зритель, сокращаем"
        else:
            self.err_tid, self.err_t = tid, ERR_TIME
            t = self.game.tile(tid)
            kind = "молекула (осадок/газ/вода)" if not t.is_ion else "ион-участник"
            self.msg = f"{t.text} — это {kind}, он не сокращается"

    def update(self, dt):
        if self.err_t > 0:
            self.err_t -= dt
            if self.err_t <= 0:
                self.err_tid = None

    # --- отрисовка ---
    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        self._hit = {}
        title = self.font_title.render(
            "Уровень 2 · Сокращённое ионное уравнение", True, config.INK)
        surface.blit(title, (24, 18))

        self._draw_molecular(surface, y=96)
        lbl = self.font_hud.render("Полное ионное:", True, config.MUTED)
        surface.blit(lbl, (40, 150))
        self._draw_tiles(surface, y=205)
        self._draw_message(surface, y=300)
        self._draw_reduce_button(surface, y=360)
        if self.game.revealed:
            self._draw_net(surface, y=470)
        self._draw_new_button(surface)
        tip = self.font_hint.render(
            "Зрители — ионы, не изменившиеся в реакции (есть и слева, и справа). "
            "Осадок ↓, газ ↑, вода и участники остаются.", True, config.MUTED)
        surface.blit(tip, tip.get_rect(center=(config.WIDTH // 2,
                                               config.HEIGHT - 24)))

    def _draw_molecular(self, surface, y):
        segs = self.game.result.equation_segments
        surf = render_equation(segs, self.font_eq, self.font_eq_sub,
                               config.INK, config.HIGHLIGHT)
        rect = surf.get_rect(center=(config.WIDTH // 2, y))
        pad = pygame.Rect(0, 0, rect.width + 24, rect.height + 12)
        pad.center = rect.center
        bg = pygame.Surface(pad.size, pygame.SRCALPHA)
        bg.fill((255, 255, 255, 200))
        surface.blit(bg, pad.topleft)
        surface.blit(surf, rect)

    # --- плитки полного ионного ---
    def _sequence(self):
        seq = []
        for i, t in enumerate(self.game.left):
            if i:
                seq.append(("sep", "+"))
            seq.append(("tile", t))
        seq.append(("sep", "→"))
        for i, t in enumerate(self.game.right):
            if i:
                seq.append(("sep", "+"))
            seq.append(("tile", t))
        return seq

    def _draw_tiles(self, surface, y):
        seq = self._sequence()
        # выбрать шрифт, чтобы поместилось по ширине
        for font in (self.font_tile, self.font_tile_sm):
            widths, total = self._measure(seq, font)
            if total <= config.WIDTH - 48:
                break
        x = config.WIDTH // 2 - total // 2
        for (kind, item), w in zip(seq, widths):
            if kind == "sep":
                s = font.render(item, True, config.MUTED)
                surface.blit(s, s.get_rect(center=(x + w // 2, y)))
            else:
                self._draw_tile(surface, item, x, y, w, font)
            x += w

    def _measure(self, seq, font):
        widths = []
        total = 0
        for kind, item in seq:
            if kind == "sep":
                w = font.size(f" {item} ")[0]
            else:
                w = font.size(item.text)[0] + 26
            widths.append(w)
            total += w
        return widths, total

    def _draw_tile(self, surface, tile, x, y, w, font):
        h = font.get_height() + 16
        rect = pygame.Rect(x + 3, y - h // 2, w - 6, h)
        struck = tile.struck
        border = ION_BORDER if tile.is_ion else TILE_BORDER
        if self.err_tid == tile.tid:
            border = config.RED
        bg = (236, 244, 236) if struck else TILE_BG
        pygame.draw.rect(surface, bg, rect, border_radius=9)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=9)
        col = STRUCK if struck else config.INK
        s = font.render(tile.text, True, col)
        surface.blit(s, s.get_rect(center=rect.center))
        if struck:
            pygame.draw.line(surface, config.RED,
                             (rect.left + 6, rect.centery),
                             (rect.right - 6, rect.centery), 3)
        if tile.is_ion and not self.game.revealed:
            self._hit[f"tile:{tile.tid}"] = rect

    def _draw_message(self, surface, y):
        if not self.msg:
            return
        col = config.RED if self.err_tid else config.MUTED
        s = self.font_hint.render(self.msg, True, col)
        surface.blit(s, s.get_rect(center=(config.WIDTH // 2, y)))

    def _draw_reduce_button(self, surface, y):
        ready = self.game.all_spectators_struck and not self.game.revealed
        rect = pygame.Rect(0, 0, 300, 50)
        rect.center = (config.WIDTH // 2, y)
        col = config.ACCENT if ready else BTN_OFF
        pygame.draw.rect(surface, col, rect, border_radius=12)
        label = "Сокращённое готово ✓" if not self.game.revealed else "Сокращено"
        t = self.font_btn.render(label, True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=rect.center))
        if not self.game.revealed:
            self._hit["reduce"] = rect

    def _draw_net(self, surface, y):
        card = pygame.Rect(0, 0, config.WIDTH - 120, 110)
        card.center = (config.WIDTH // 2, y + 30)
        bg = pygame.Surface(card.size, pygame.SRCALPHA)
        bg.fill((232, 244, 235, 240))
        surface.blit(bg, card.topleft)
        pygame.draw.rect(surface, GREEN, card, width=3, border_radius=16)
        lbl = self.font_hud.render("Сокращённое ионное уравнение:", True,
                                   config.INK)
        surface.blit(lbl, lbl.get_rect(midtop=(card.centerx, card.top + 12)))
        eq = self.font_tile.render(self.game.net.equation, True, config.INK)
        if eq.get_width() > card.width - 30:
            eq = self.font_tile_sm.render(self.game.net.equation, True,
                                          config.INK)
        surface.blit(eq, eq.get_rect(center=(card.centerx, card.centery + 14)))

    def _draw_new_button(self, surface):
        rect = pygame.Rect(0, 0, 200, 42)
        rect.midbottom = (config.WIDTH // 2, config.HEIGHT - 54)
        pygame.draw.rect(surface, config.PANEL, rect, border_radius=10)
        pygame.draw.rect(surface, config.ACCENT, rect, width=2, border_radius=10)
        t = self.font_btn.render("Новая реакция", True, config.ACCENT)
        surface.blit(t, t.get_rect(center=rect.center))
        self._hit["new"] = rect


def run():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Уровень 2 — сокращённое ионное")
    clock = pygame.time.Clock()
    scene = CancelScene()
    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            else:
                scene.handle_event(e)
        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()
    pygame.quit()
