"""Сцена: конечный автомат, drag-and-drop, отрисовка и игровой цикл.

`SceneLogic` — чистая логика состояний/скоринга/хит-теста (без окна, тестируется
headless). `Scene` — отрисовка и обработка событий pygame поверх этой логики.
"""

from __future__ import annotations

import random

import pygame

from game import cat, config, fonts
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
        self.results: list[bool] = []  # верно/неверно по раундам (для точек)
        self._plan: list = []
        self._plan_i = 0
        self._layout()
        self._build_plan()
        self.new_round()

    def _build_plan(self):
        """5 раундов игры: минимум два — с цветным (не белым) осадком и
        минимум один — с выделением газа."""
        plan = [generate(self.rng, colored_precipitate=True) for _ in range(2)]
        plan.append(generate(self.rng, effect="GAS"))
        plan += [generate(self.rng)
                 for _ in range(config.ROUNDS_TOTAL - len(plan))]
        self.rng.shuffle(plan)
        self._plan = plan
        self._plan_i = 0

    def _layout(self):
        self.main_rect = pygame.Rect(
            config.MAIN_POS, (config.TUBE_W, config.TUBE_H)
        )
        ow, oh = config.OPTION_TUBE_W, config.OPTION_TUBE_H
        # варианты — ряд справа от основной, по центру её высоты
        region_left = self.main_rect.right + 74
        region_right = config.WIDTH - config.PANEL_MARGIN
        total_w = 3 * ow + 2 * config.OPTION_GAP
        x0 = region_left + ((region_right - region_left) - total_w) // 2
        cy = self.main_rect.centery
        self.option_rects = [
            pygame.Rect(x0 + i * (ow + config.OPTION_GAP), cy - oh // 2, ow, oh)
            for i in range(3)
        ]
        # нижнее свободное поле под запись реакции и описание
        self.result_panel = pygame.Rect(
            config.PANEL_MARGIN, config.PANEL_TOP,
            config.WIDTH - 2 * config.PANEL_MARGIN,
            config.HEIGHT - config.PANEL_TOP - config.PANEL_BOTTOM,
        )

    @property
    def next_button_rect(self) -> pygame.Rect:
        bw, bh = 168, 50
        return pygame.Rect(self.result_panel.right - bw - 26,
                           self.result_panel.bottom - bh - 22, bw, bh)

    def click_next(self, pos) -> bool:
        """Клик по кнопке «Дальше» в состоянии результата → следующий раунд."""
        if self.state != RESULT or not self.next_button_rect.collidepoint(pos):
            return False
        self.finish_result()
        return True

    def new_round(self):
        if self._plan and self._plan_i < len(self._plan):
            self.round = self._plan[self._plan_i]
            self._plan_i += 1
        else:
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
        self.results.append(self.is_correct)
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
        self.results = []
        self._build_plan()
        self.new_round()

    @property
    def round_no(self) -> int:
        """Номер текущего раунда (1..ROUNDS_TOTAL)."""
        return min(self.total + 1, config.ROUNDS_TOTAL)

    @property
    def current_dot(self) -> int:
        """Индекс подсвеченной точки прогресса (текущий раунд)."""
        if self.state == RESULT:
            return self.total - 1        # показываем только что отвеченный
        return min(self.total, config.ROUNDS_TOTAL - 1)

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


def _glass_panel(surface, rect, *, radius=18, fill=config.GLASS_FILL,
                 border=config.GLASS_BORDER, border_w=1, shadow=True,
                 gloss_frac=1 / 3):
    """Матовая стеклянная панель: мягкая тень, полупрозрачная заливка,
    тонкая светлая рамка и верхний светлый блик (высота — `gloss_frac`)."""
    if shadow:
        sh = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sh, config.SHADOW, sh.get_rect(), border_radius=radius)
        surface.blit(sh, (rect.x, rect.y + 7))
    card = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(card, fill, card.get_rect(), border_radius=radius)
    # верхний светлый блок — имитация преломления стекла
    gloss = pygame.Rect(0, 0, rect.width, max(2, int(rect.height * gloss_frac)))
    pygame.draw.rect(card, (255, 255, 255, 26), gloss,
                     border_top_left_radius=radius, border_top_right_radius=radius)
    pygame.draw.rect(card, border, card.get_rect(), width=border_w,
                     border_radius=radius)
    surface.blit(card, rect.topleft)


def _gradient_rounded(size, c1, c2, radius, border=None, border_w=0) -> pygame.Surface:
    """Скруглённая плашка, залитая горизонтальным градиентом c1→c2.

    Рисуется с 3× сглаживанием (суперсэмплинг) и уменьшается smoothscale, чтобы
    края и обводка были ровными, без «рваных» пикселей.
    """
    ss = 3
    w, h = size
    W, H = w * ss, h * ss
    grad = pygame.Surface((W, H)).convert_alpha()
    for x in range(W):
        t = x / max(1, W - 1)
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        pygame.draw.line(grad, col, (x, 0), (x, H))
    # обрезка по скруглённому прямоугольнику через альфа-маску
    mask = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=radius * ss)
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if border and border_w:
        pygame.draw.rect(grad, border, grad.get_rect(),
                         width=border_w * ss, border_radius=radius * ss)
    return pygame.transform.smoothscale(grad, size)


class Scene:
    def __init__(self, logic: SceneLogic | None = None):
        from game import animations
        from game.tube import Tube

        self._anim = animations
        self._Tube = Tube
        self.logic = logic or SceneLogic()

        self.bg = _gradient((config.WIDTH, config.HEIGHT),
                            config.BG_TOP, config.BG_BOTTOM)
        self.font_title = fonts.get(30, bold=True)
        self.font_big = fonts.get(30, bold=True)
        self.font_small = fonts.get(19, bold=True)
        self.font_hud = fonts.get(22, bold=True)
        self.font_hint = fonts.get(18)
        self.font_desc = fonts.get(24, bold=True)
        self.font_btn = fonts.get(22, bold=True)
        # компактные шрифты для подписей вариантов (пробирки меньше)
        self.font_lbl_big = fonts.get(22, bold=True)
        self.font_lbl_small = fonts.get(14, bold=True)
        # шрифты вводной подписи (с индексами в формуле)
        self.font_instr = fonts.get(17)        # обе строки подписи — одним размером
        self.font_instr_small = fonts.get(11)  # индексы в формуле

        self.pour = None
        self.effect = None
        self.drag_offset = (0, 0)
        self.mouse = (0, 0)
        self._build_tubes()

    def _build_tubes(self):
        r = self.logic.round
        self.main_tube = self._Tube(r.main, *config.MAIN_POS, level=0.5)
        self.option_tubes = [
            self._Tube(r.options[i], rect.x, rect.y, level=0.62,
                       scale=config.OPTION_SCALE)
            for i, rect in enumerate(self.logic.option_rects)
        ]

    # --- события ---
    def handle_event(self, e):
        L = self.logic
        if e.type == pygame.MOUSEMOTION:
            self.mouse = e.pos
        if L.state == FINISHED:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                L.restart()
                self._build_tubes()
            return
        if L.state == RESULT:
            # переход только по кнопке «Дальше»
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and L.click_next(e.pos):
                self.effect = None
                if L.state != FINISHED:
                    self._build_tubes()
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if L.begin_drag(e.pos):
                t = self.option_tubes[L.dragging_index]
                self.drag_offset = (e.pos[0] - t.x, e.pos[1] - t.y)
        elif e.type == pygame.MOUSEMOTION:
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
                if outcome == "WATER":
                    # образовалась вода — раствор голубоватый
                    self.main_tube.color_override = config.WATER_TINT + (200,)
                self.pour = None
        elif L.state == RESULT and self.effect:
            # анимация продолжается; переход к следующему раунду — по кнопке «Дальше»
            self.effect.update(dt)

    def _spawn_effect(self, outcome):
        if outcome == WRONG:
            self.effect = self._anim.WrongEffect()
        else:
            result = self.logic.round.result
            star = result.star_formula
            if outcome == "PRECIPITATE":
                from chemistry import precipitate_color
                color = precipitate_color(result)   # реальный цвет осадка
            else:
                color = self.logic.round.correct.color
            self.effect = self._anim.make_effect(outcome, star, color)

    # --- отрисовка ---
    def _draw_cat(self, surface):
        """Котик-химик выглядывает из правого края (за пробирками и панелью)."""
        L = self.logic
        if L.state == RESULT:
            mood = "sad" if L.last_outcome == WRONG else "happy"
        elif L.state == FINISHED:
            mood = "happy" if L.score >= 3 else "sad"
        else:
            mood = "neutral"
        # низ котика — на уровне начала ТЁМНОЙ части нижней рамки (под светлым блоком)
        panel = L.result_panel
        dark_start = panel.top + int(panel.height * config.PANEL_GLOSS)
        cat.draw(surface, config.WIDTH - 34, dark_start, mood, scale=0.9)

    def draw(self, surface):
        L = self.logic
        surface.blit(self.bg, (0, 0))
        self._draw_cat(surface)
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

        # варианты (кроме перелитого — он «влит» в основную)
        for i, t in enumerate(self.option_tubes):
            if L.state in (POURING, RESULT) and i == L.dragging_index:
                continue
            t.draw(surface)
            t.draw_label(surface, self.font_lbl_big, self.font_lbl_small)

        # эффект результата поверх основной
        if L.state == RESULT and self.effect:
            self.effect.draw(surface, self.main_tube,
                             self.font_big, self.font_small)

        # нижнее свободное поле: запись реакции и описание
        self._draw_result_panel(surface)

    # --- нижняя панель результата ------------------------------------------
    def _draw_result_panel(self, surface):
        L = self.logic
        panel = L.result_panel
        # небольшой верхний светлый блок — в нём заголовок итога
        _glass_panel(surface, panel, radius=20, fill=config.GLASS_DARK,
                     gloss_frac=config.PANEL_GLOSS)
        if L.state != RESULT:
            hint = self.font_hint.render(
                "Здесь появится запись реакции и описание результата",
                True, config.MUTED)
            surface.blit(hint, hint.get_rect(center=panel.center))
            return
        if L.last_outcome == WRONG:
            self._draw_wrong_panel(surface, panel)
        else:
            self._draw_correct_panel(surface, panel)
        self._draw_next_button(surface)

    def _equation_surface(self, panel):
        """Уравнение реакции, вписанное по ширине в панель (масштабируется, если
        не влезает)."""
        from game.formula import render_equation

        eq = render_equation(self.logic.round.result.equation_segments,
                             self.font_big, self.font_small,
                             config.INK, config.HIGHLIGHT)
        max_w = panel.width - 48
        if eq.get_width() > max_w:
            k = max_w / eq.get_width()
            eq = pygame.transform.smoothscale(
                eq, (max_w, max(1, int(eq.get_height() * k))))
        return eq

    def _draw_correct_panel(self, surface, panel):
        # заголовок в верхнем светлом блоке
        head = self.font_hud.render("Отлично, верный выбор!", True, config.INK)
        surface.blit(head, head.get_rect(midtop=(panel.centerx, panel.top + 22)))

        # ниже: описание осадка/газа + реакция
        from chemistry import describe_result
        desc = describe_result(self.logic.round.result)
        y = panel.top + 82
        for line in self._wrap(desc, self.font_desc, panel.width - 72):
            ds = self.font_desc.render(line, True, config.HIGHLIGHT)
            surface.blit(ds, ds.get_rect(midtop=(panel.centerx, y)))
            y += ds.get_height() + 2
        eq = self._equation_surface(panel)
        surface.blit(eq, eq.get_rect(midtop=(panel.centerx, y + 8)))

    def _draw_wrong_panel(self, surface, panel):
        # заголовок в светлом блоке — фиолетовым и шрифтом поменьше; со слов
        # «ни осадок…» перенос на новую строку
        y = panel.top + 20
        for line in ("В результате взаимодействия не образовался",
                     "ни осадок, ни газ, ни вода — реакция не идёт"):
            ls = self.font_instr.render(line, True, config.ACCENT)
            surface.blit(ls, ls.get_rect(midtop=(panel.centerx, y)))
            y += ls.get_height() + 2

        # ниже: «Вот правильный ответ:» + реакция
        y += 16
        hint = self.font_hud.render("Вот правильный ответ:", True, config.INK)
        surface.blit(hint, hint.get_rect(midtop=(panel.centerx, y)))
        eq = self._equation_surface(panel)
        surface.blit(eq, eq.get_rect(
            midtop=(panel.centerx, y + hint.get_height() + 12)))

    def _draw_next_button(self, surface):
        rect = self.logic.next_button_rect
        hover = rect.collidepoint(self.mouse)
        radius = rect.height // 2
        # мягкая тень
        sh = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(sh, config.SHADOW, sh.get_rect(), border_radius=radius)
        surface.blit(sh, (rect.x, rect.y + 6))
        # полная градиентная заливка #BC96E6 → #FFD166 с ровной обводкой
        grad = _gradient_rounded(rect.size, config.BTN_GRAD_A,
                                 config.BTN_GRAD_B, radius,
                                 border=(255, 255, 255, 200), border_w=2)
        if hover:
            gloss = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(gloss, (255, 255, 255, 55), gloss.get_rect(),
                             border_radius=radius)
            grad.blit(gloss, (0, 0))
        surface.blit(grad, rect.topleft)
        lbl = self.font_btn.render("Дальше →", True, config.BTN_TEXT)
        surface.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_end(self, surface):
        L = self.logic
        cx = config.WIDTH // 2
        panel = pygame.Rect(0, 0, 640, 320)
        panel.center = (cx, config.HEIGHT // 2)
        _glass_panel(surface, panel, radius=22, fill=config.GLASS_DARK,
                     border=config.ACCENT + (180,), border_w=2)

        big = fonts.get(30, bold=True)
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
        surface.blit(title, (24, 20))
        self._draw_progress_dots(surface)
        self._draw_bottom_hint(surface)
        if self.logic.state in (IDLE, DRAGGING):
            self._draw_instruction(surface)

    def _draw_instruction(self, surface):
        """Пояснение сверху: что делать в этом раунде (с формулой основной).

        Формула рисуется через render_formula, чтобы индексы были настоящими
        подстрочными, а не «квадратиками» шрифта.
        """
        from game.formula import render_formula

        x, y = 24, 66
        white = config.INK
        # строка 1: текст + формула вещества с индексами
        pre = self.font_instr.render(
            "Из трёх вариантов выберите одну пробирку, "
            "с содержимым которой прореагирует ", True, white)
        formula = render_formula(self.logic.round.main.formula,
                                 self.font_instr, self.font_instr_small, white)
        dot = self.font_instr.render(".", True, white)
        surface.blit(pre, (x, y))
        fx = x + pre.get_width()
        surface.blit(formula, (fx, y))
        surface.blit(dot, (fx + formula.get_width(), y))
        # строка 2 — с новой строки, тем же размером
        y2 = y + self.font_instr.get_linesize() + 4
        line2 = self.font_instr.render(
            "Перетащите выбранную пробирку к основной, чтобы смешать "
            "вещества и узнать, что получится!", True, white)
        surface.blit(line2, (x, y2))

    def _draw_progress_dots(self, surface):
        """Пять точек прогресса: зелёная — верно, красная — неверно,
        текущий раунд обведён золотым кольцом, будущие — тусклые."""
        L = self.logic
        n = config.ROUNDS_TOTAL
        r = 9
        gap = 30
        cy = 36
        right = config.WIDTH - 30
        for i in range(n):
            cx = right - (n - 1 - i) * gap
            if i < len(L.results):
                col = config.DROP_OK if L.results[i] else config.RED
                pygame.draw.circle(surface, col, (cx, cy), r)
            else:
                # тусклая незаполненная точка
                dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(dot, (255, 255, 255, 55), (r, r), r)
                surface.blit(dot, (cx - r, cy - r))
            if i == L.current_dot:
                pygame.draw.circle(surface, config.HIGHLIGHT, (cx, cy), r + 5, 3)

    def _draw_bottom_hint(self, surface):
        hint = {
            DRAGGING: "Отпустите над основной пробиркой",
            POURING: "Переливание…",
        }.get(self.logic.state, "")
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
