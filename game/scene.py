"""Сцена: конечный автомат, drag-and-drop, отрисовка и игровой цикл.

`SceneLogic` — чистая логика состояний/скоринга/хит-теста (без окна, тестируется
headless). `Scene` — отрисовка и обработка событий pygame поверх этой логики.
"""

from __future__ import annotations

import random

import pygame

from game import config
from game.round import generate

# Состояния
IDLE = "IDLE"
DRAGGING = "DRAGGING"
POURING = "POURING"
RESULT = "RESULT"
FINISHED = "FINISHED"

# Итог раунда / тип анимации
WRONG = "WRONG"

# Вердикты по числу верных из 5.
VERDICTS = {
    0: "у тебя бесконечный потенциал для роста",
    1: "один раз не этот самый человек",
    2: "о, пошло дело",
    3: "намаано",
    4: "одна ошибка, и ты ошибся",
    5: "Гениально!",
}


class SceneLogic:
    """Состояние игры без отрисовки — пригодно для headless-тестов."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.score = 0
        self.total = 0
        self._layout()
        self.new_round()

    def _layout(self):
        self.main_rect = pygame.Rect(
            config.MAIN_POS, (config.TUBE_W, config.TUBE_H)
        )
        total_w = 3 * config.TUBE_W + 2 * config.OPTION_GAP
        x0 = config.WIDTH // 2 - total_w // 2
        self.option_rects = [
            pygame.Rect(
                x0 + i * (config.TUBE_W + config.OPTION_GAP),
                config.OPTION_Y, config.TUBE_W, config.TUBE_H,
            )
            for i in range(3)
        ]

    def new_round(self):
        self.round = generate(self.rng)
        self.state = IDLE
        self.dragging_index: int | None = None
        self.last_outcome: str | None = None  # GAS/PRECIPITATE/WATER/WRONG

    @property
    def drop_zone(self) -> pygame.Rect:
        return self.main_rect.inflate(config.DROP_PAD, config.DROP_PAD)

    # --- хит-тест и переходы ---
    def option_at(self, pos) -> int | None:
        for i, r in enumerate(self.option_rects):
            if r.collidepoint(pos):
                return i
        return None

    def begin_drag(self, pos) -> bool:
        if self.state != IDLE:
            return False
        idx = self.option_at(pos)
        if idx is None:
            return False
        self.state = DRAGGING
        self.dragging_index = idx
        return True

    def try_drop(self, pos) -> bool:
        """Сброс. В зоне основной → POURING (True); иначе отмена → IDLE."""
        if self.state != DRAGGING:
            return False
        if self.drop_zone.collidepoint(pos):
            self.state = POURING
            return True
        self.state = IDLE
        self.dragging_index = None
        return False

    @property
    def is_correct(self) -> bool:
        return self.dragging_index == self.round.correct_index

    def finish_pour(self) -> str:
        """Завершение переливания: фиксируем итог и счёт. Возвращает исход."""
        if self.state != POURING:
            return self.last_outcome or WRONG
        self.state = RESULT
        self.total += 1
        if self.is_correct:
            self.score += 1
            self.last_outcome = self.round.effect
        else:
            self.last_outcome = WRONG
        return self.last_outcome

    def finish_result(self):
        """Завершение анимации результата: новый раунд или конец игры."""
        if self.state != RESULT:
            return
        if self.total >= config.ROUNDS_TOTAL:
            self.state = FINISHED
        else:
            self.new_round()

    def restart(self):
        self.score = 0
        self.total = 0
        self.new_round()

    @property
    def round_no(self) -> int:
        """Номер текущего раунда (1..ROUNDS_TOTAL)."""
        return min(self.total + 1, config.ROUNDS_TOTAL)

    @property
    def verdict(self) -> str:
        return VERDICTS.get(self.score, "")


# --------------------------------------------------------------------------
# Отрисовка
# --------------------------------------------------------------------------
def _gradient(size, top, bottom) -> pygame.Surface:
    surf = pygame.Surface(size)
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (size[0], y))
    return surf


class Scene:
    def __init__(self, logic: SceneLogic | None = None):
        from game import animations
        from game.tube import Tube

        self._anim = animations
        self._Tube = Tube
        self.logic = logic or SceneLogic()

        self.bg = _gradient((config.WIDTH, config.HEIGHT),
                            config.BG_TOP, config.BG_BOTTOM)
        self.font_title = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 19, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_hint = pygame.font.SysFont("Arial", 18)

        self.pour = None
        self.effect = None
        self.drag_offset = (0, 0)
        self.mouse = (0, 0)
        self._build_tubes()

    def _build_tubes(self):
        r = self.logic.round
        self.main_tube = self._Tube(r.main, *config.MAIN_POS, level=0.5)
        self.option_tubes = [
            self._Tube(r.options[i], rect.x, rect.y, level=0.62)
            for i, rect in enumerate(self.logic.option_rects)
        ]

    # --- события ---
    def handle_event(self, e):
        L = self.logic
        if L.state == FINISHED:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                L.restart()
                self._build_tubes()
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if L.begin_drag(e.pos):
                t = self.option_tubes[L.dragging_index]
                self.drag_offset = (e.pos[0] - t.x, e.pos[1] - t.y)
        elif e.type == pygame.MOUSEMOTION:
            self.mouse = e.pos
            if L.state == DRAGGING:
                t = self.option_tubes[L.dragging_index]
                t.x = e.pos[0] - self.drag_offset[0]
                t.y = e.pos[1] - self.drag_offset[1]
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if L.state == DRAGGING:
                idx = L.dragging_index
                if L.try_drop(e.pos):
                    self._start_pour(idx)
                else:
                    self._reset_option(idx)

    def _reset_option(self, idx):
        rect = self.logic.option_rects[idx]
        self.option_tubes[idx].x = rect.x
        self.option_tubes[idx].y = rect.y

    def _start_pour(self, idx):
        src = self.option_tubes[idx]
        self.pour = self._anim.Pour(
            self.main_tube, src, (src.x, src.y), src.substance.color
        )

    # --- обновление ---
    def update(self, dt):
        L = self.logic
        if L.state == POURING and self.pour:
            self.pour.update(dt)
            if self.pour.done:
                outcome = L.finish_pour()
                self._spawn_effect(outcome)
                # зафиксировать поднятый уровень/смешанный цвет в основной
                self.main_tube.level = min(0.9, self.main_tube.level + 0.28)
                self.pour = None
        elif L.state == RESULT and self.effect:
            self.effect.update(dt)
            if self.effect.done:
                self.effect = None
                L.finish_result()
                if L.state != FINISHED:
                    self._build_tubes()

    def _spawn_effect(self, outcome):
        if outcome == WRONG:
            self.effect = self._anim.WrongEffect()
        else:
            star = self.logic.round.result.star_formula
            color = self.logic.round.correct.color
            self.effect = self._anim.make_effect(outcome, star, color)

    # --- отрисовка ---
    def draw(self, surface):
        L = self.logic
        surface.blit(self.bg, (0, 0))
        if L.state == FINISHED:
            self._draw_end(surface)
            return
        self._draw_header(surface)

        shake = (0, 0)
        if isinstance(self.effect, self._anim.WrongEffect):
            shake = self.effect.shake_offset()

        # основная пробирка / переливание
        if L.state == POURING and self.pour:
            self.pour.draw(surface, self.font_big, self.font_small)
        else:
            self.main_tube.draw(
                surface,
                pos=(self.main_tube.x + shake[0], self.main_tube.y + shake[1]),
            )
        self.main_tube.draw_label(
            surface, self.font_big, self.font_small,
            pos=(self.main_tube.x + shake[0], self.main_tube.y + shake[1]),
        )
        # подпись «основная» (прячем во время результата, чтобы не пересекалась
        # с формулой эффекта над пробиркой)
        if L.state in (IDLE, DRAGGING):
            cap = self.font_hint.render("основная", True, config.MUTED)
            surface.blit(cap, cap.get_rect(midbottom=(
                self.main_tube.x + config.TUBE_W // 2, self.main_tube.y - 6)))

        # варианты (кроме перелитого — он «влит» в основную)
        for i, t in enumerate(self.option_tubes):
            if L.state in (POURING, RESULT) and i == L.dragging_index:
                continue
            t.draw(surface)
            t.draw_label(surface, self.font_big, self.font_small)

        # подсветка зоны сброса
        if L.state == DRAGGING and L.drop_zone.collidepoint(self.mouse):
            pygame.draw.rect(surface, config.DROP_OK, L.drop_zone,
                             width=3, border_radius=14)

        # эффект результата поверх основной
        if L.state == RESULT and self.effect:
            self.effect.draw(surface, self.main_tube,
                             self.font_big, self.font_small)
            # при верном ответе — полное молекулярное уравнение с подсветкой
            if L.last_outcome != WRONG:
                self._draw_equation(surface)

    def _draw_equation(self, surface):
        """Молекулярное уравнение под основной с подсветкой продукта."""
        from game.formula import render_equation

        segments = self.logic.round.result.equation_segments
        surf = render_equation(segments, self.font_big, self.font_small,
                               config.INK, config.HIGHLIGHT)
        y = self.main_tube.y + config.TUBE_H + 44
        rect = surf.get_rect(midtop=(config.WIDTH // 2, y))
        # светлая подложка для читаемости
        pad = pygame.Rect(0, 0, rect.width + 24, rect.height + 14)
        pad.center = rect.center
        bg = pygame.Surface(pad.size, pygame.SRCALPHA)
        bg.fill((255, 255, 255, 205))
        surface.blit(bg, pad.topleft)
        surface.blit(surf, rect)

    def _draw_end(self, surface):
        L = self.logic
        cx = config.WIDTH // 2
        panel = pygame.Rect(0, 0, 640, 320)
        panel.center = (cx, config.HEIGHT // 2)
        card = pygame.Surface(panel.size, pygame.SRCALPHA)
        card.fill((255, 255, 255, 240))
        surface.blit(card, panel.topleft)
        pygame.draw.rect(surface, config.ACCENT, panel, width=3, border_radius=18)

        big = pygame.font.SysFont("Arial", 30, bold=True)
        head = self.font_title.render("Игра окончена", True, config.INK)
        surface.blit(head, head.get_rect(center=(cx, panel.top + 56)))
        score = big.render(f"Результат: {L.score} / {config.ROUNDS_TOTAL}",
                           True, config.ACCENT)
        surface.blit(score, score.get_rect(center=(cx, panel.top + 120)))

        verdict = self._wrap(L.verdict, self.font_hud, panel.width - 80)
        vy = panel.top + 168
        for line in verdict:
            ls = self.font_hud.render(line, True, config.INK)
            surface.blit(ls, ls.get_rect(center=(cx, vy)))
            vy += 30
        hint = self.font_hint.render(
            "Нажмите любую клавишу для новой игры", True, config.MUTED)
        surface.blit(hint, hint.get_rect(center=(cx, panel.bottom - 34)))

    @staticmethod
    def _wrap(text, font, max_w):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.size(trial)[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or [text]

    def _draw_header(self, surface):
        title = self.font_title.render(config.TITLE, True, config.INK)
        surface.blit(title, (24, 18))
        L = self.logic
        hud = self.font_hud.render(
            f"Верно: {L.score} / {L.total}", True, config.ACCENT)
        surface.blit(hud, hud.get_rect(topright=(config.WIDTH - 24, 22)))
        rnd = self.font_hint.render(
            f"Раунд {L.round_no} / {config.ROUNDS_TOTAL}", True, config.MUTED)
        surface.blit(rnd, rnd.get_rect(topright=(config.WIDTH - 24, 50)))
        hint = {
            IDLE: "Перетащите пробирку, дающую реакцию обмена, к основной",
            DRAGGING: "Отпустите над основной пробиркой",
            POURING: "Переливание…",
            RESULT: "",
        }[L.state]
        if hint:
            h = self.font_hint.render(hint, True, config.MUTED)
            surface.blit(h, h.get_rect(midbottom=(
                config.WIDTH // 2, config.HEIGHT - 16)))


def run():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption(config.TITLE)
    clock = pygame.time.Clock()
    scene = Scene()

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
