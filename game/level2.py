"""Уровень 2 — «Разбор формулы на ионы» (механика №1).

Сцена поверх `game.builder.Level2Logic`. Ученик спиннерами и стрелками собирает
для каждого иона коэффициент, знак и величину заряда. Каждое поле подсвечивается
зелёным, как только верно; формула иона (с внутренним индексом) дана и не
редактируется. Внизу — «весы заряда» (сумма зарядов слева/справа от нуля). Когда
оба иона собраны верно, активируется кнопка «Дальше».
"""

from __future__ import annotations

import pygame

from chemistry.ions import to_subscript_formula, to_superscript
from game import config
from game.builder import Level2Logic
from game.formula import render_formula

GREEN = config.DROP_OK
GREEN_BG = (224, 244, 230)
NEUTRAL_BG = (255, 255, 255)
ARROW = (90, 110, 130)
BTN_OFF = (188, 200, 212)

ARROW_W, ARROW_H = 30, 22
BOX_W = 52


def _charge_str(sign: int, mag: int) -> str:
    """'+1/+2/...' → '⁺ / ²⁺ ...' для верхнего индекса."""
    s = "+" if sign > 0 else "-"
    num = "" if mag == 1 else str(mag)
    return to_superscript(num + s)


class Level2Scene:
    def __init__(self, logic: Level2Logic | None = None):
        self.logic = logic or Level2Logic()
        self.bg = _gradient((config.WIDTH, config.HEIGHT),
                            config.BG_TOP, config.BG_BOTTOM)
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_formula = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_ion = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_ion_sub = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_sup = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_hint = pygame.font.SysFont("Arial", 18)
        self.font_btn = pygame.font.SysFont("Arial", 22, bold=True)
        self._hit: dict[str, pygame.Rect] = {}
        self._msg = ""

    # --- события ---
    def handle_event(self, e):
        L = self.logic
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if L.finished:
                L.restart()
                self._msg = ""
                return
            self._click(e.pos)

    def _click(self, pos):
        L = self.logic
        for name, rect in self._hit.items():
            if not rect.collidepoint(pos):
                continue
            if name == "confirm":
                if not L.confirm():
                    self._msg = "Не все поля зелёные — проверь коэффициенты и заряды"
                else:
                    self._msg = ""
                return
            term = L.builder.cation if name[1] == "0" else L.builder.anion
            action = name[3:]  # после префикса "t0_"/"t1_"
            if action == "coeff_up":
                term.bump_coeff(+1)
            elif action == "coeff_dn":
                term.bump_coeff(-1)
            elif action == "mag_up":
                term.bump_mag(+1)
            elif action == "mag_dn":
                term.bump_mag(-1)
            elif action == "sign":
                term.toggle_sign()
            self._msg = ""
            return

    def update(self, dt):  # без анимаций по времени — заглушка для общего цикла
        pass

    # --- отрисовка ---
    def draw(self, surface):
        surface.blit(self.bg, (0, 0))
        self._hit = {}
        self._draw_header(surface)
        if self.logic.finished:
            self._draw_end(surface)
            return
        self._draw_formula(surface)
        self._draw_builder(surface)
        self._draw_balance(surface)
        self._draw_confirm(surface)
        self._draw_footer(surface)

    def _draw_header(self, surface):
        L = self.logic
        title = self.font_title.render(
            "Уровень 2 · Разбор формулы на ионы", True, config.INK)
        surface.blit(title, (24, 18))
        if L.finished:
            return
        hud = self.font_hud.render(
            f"Решено: {L.solved_count}", True, config.ACCENT)
        surface.blit(hud, hud.get_rect(topright=(config.WIDTH - 24, 22)))
        rnd = self.font_hint.render(
            f"Вещество {L.round_no} / {L.rounds_total}", True, config.MUTED)
        surface.blit(rnd, rnd.get_rect(topright=(config.WIDTH - 24, 50)))

    def _draw_formula(self, surface):
        sub = self.logic.builder.substance
        surf = render_formula(sub.formula, self.font_formula, self.font_sub,
                              config.INK)
        rect = surf.get_rect(center=(config.WIDTH // 2, 150))
        surface.blit(surf, rect)
        arrow = self.font_formula.render("→", True, config.MUTED)
        surface.blit(arrow, arrow.get_rect(center=(config.WIDTH // 2, 210)))

    # --- блоки ионов ---
    def _draw_builder(self, surface):
        b = self.logic.builder
        cy = 320
        gap_plus = 56
        block_w = 230
        total_w = 2 * block_w + gap_plus
        x0 = config.WIDTH // 2 - total_w // 2
        centers = [x0 + block_w // 2, x0 + block_w + gap_plus + block_w // 2]
        self._draw_term(surface, "t0", b.cation, centers[0], cy)
        plus = self.font_formula.render("+", True, config.MUTED)
        surface.blit(plus, plus.get_rect(center=(config.WIDTH // 2, cy)))
        self._draw_term(surface, "t1", b.anion, centers[1], cy)

    def _draw_term(self, surface, key, term, cx, cy):
        # --- коэффициент (слева) ---
        coeff_x = cx - 78
        self._spinner(surface, key + "_coeff", coeff_x, cy,
                      str(term.coeff), term.coeff_ok)
        coeff_cap = self.font_hint.render("коэф.", True, config.MUTED)
        surface.blit(coeff_cap, coeff_cap.get_rect(
            center=(coeff_x, cy + 64)))

        # --- формула иона (центр) ---
        ion_formula = to_subscript_formula(term.target.ion.formula)
        ion_surf = render_formula(term.target.ion.formula, self.font_ion,
                                  self.font_ion_sub, config.INK)
        ion_x = cx + 4
        ion_rect = ion_surf.get_rect(midright=(ion_x, cy))
        surface.blit(ion_surf, ion_rect)

        # --- заряд (верхний индекс справа от иона) ---
        charge = _charge_str(term.charge_sign, term.charge_mag)
        chg_surf = self.font_sup.render(charge, True,
                                        GREEN if term.charge_ok else config.RED)
        chg_rect = chg_surf.get_rect(bottomleft=(ion_rect.right + 2,
                                                 cy - 4))
        # бокс заряда (подсветка)
        box = chg_rect.inflate(14, 10)
        bg = GREEN_BG if term.charge_ok else NEUTRAL_BG
        pygame.draw.rect(surface, bg, box, border_radius=8)
        pygame.draw.rect(surface, GREEN if term.charge_ok else BTN_OFF, box,
                         width=2, border_radius=8)
        surface.blit(chg_surf, chg_rect)

        # знак: кнопка ± под зарядом
        sign_rect = pygame.Rect(0, 0, ARROW_W, ARROW_H)
        sign_rect.midtop = (box.centerx, box.bottom + 8)
        self._button(surface, key + "_sign", sign_rect, "±")
        # величина заряда: стрелки ▲▼ правее
        mag_x = box.right + 22
        self._mag_arrows(surface, key, mag_x, box.centery)

        chg_cap = self.font_hint.render("заряд", True, config.MUTED)
        surface.blit(chg_cap, chg_cap.get_rect(center=(box.centerx, cy + 64)))
        _ = ion_formula  # (формула иона фиксирована — внутренний индекс остаётся)

    def _spinner(self, surface, key, cx, cy, value, ok):
        """Вертикальный спиннер: ▲ / значение / ▼. cx,cy — центр значения."""
        box = pygame.Rect(0, 0, BOX_W, 44)
        box.center = (cx, cy)
        bg = GREEN_BG if ok else NEUTRAL_BG
        pygame.draw.rect(surface, bg, box, border_radius=8)
        pygame.draw.rect(surface, GREEN if ok else BTN_OFF, box, width=2,
                         border_radius=8)
        val = self.font_ion.render(value, True,
                                   GREEN if ok else config.INK)
        surface.blit(val, val.get_rect(center=box.center))

        up = pygame.Rect(0, 0, BOX_W, ARROW_H)
        up.midbottom = (cx, box.top - 4)
        dn = pygame.Rect(0, 0, BOX_W, ARROW_H)
        dn.midtop = (cx, box.bottom + 4)
        self._button(surface, key + "_up", up, "▲", base=key + "_up")
        self._button(surface, key + "_dn", dn, "▼", base=key + "_dn")
        # перепривяжем имена к действиям bump
        self._hit[key.replace("_coeff", "") + "_coeff_up"] = up
        self._hit[key.replace("_coeff", "") + "_coeff_dn"] = dn

    def _mag_arrows(self, surface, key, cx, cy):
        up = pygame.Rect(0, 0, ARROW_W, ARROW_H)
        up.midbottom = (cx, cy - 2)
        dn = pygame.Rect(0, 0, ARROW_W, ARROW_H)
        dn.midtop = (cx, cy + 2)
        self._button(surface, key + "_magup", up, "▲")
        self._button(surface, key + "_magdn", dn, "▼")
        self._hit[key + "_mag_up"] = up
        self._hit[key + "_mag_dn"] = dn

    def _button(self, surface, name, rect, label, base=None):
        pygame.draw.rect(surface, NEUTRAL_BG, rect, border_radius=6)
        pygame.draw.rect(surface, BTN_OFF, rect, width=2, border_radius=6)
        t = self.font_hud.render(label, True, ARROW)
        surface.blit(t, t.get_rect(center=rect.center))
        # имена-«действия» назначаются вызывающим кодом через _hit напрямую;
        # сюда кладём только явные (sign).
        if name.endswith("_sign"):
            self._hit[name.replace("_sign", "") + "_sign"] = rect

    def _draw_balance(self, surface):
        b = self.logic.builder
        cx, y = config.WIDTH // 2, 470
        bal = b.student_charge_balance
        ok = bal == 0
        label = self.font_hud.render("Σ зарядов:", True, config.MUTED)
        surface.blit(label, label.get_rect(midright=(cx - 14, y)))
        text = f"{'+' if bal > 0 else ''}{bal}" if bal else "0 ✓"
        col = GREEN if ok else config.RED
        val = self.font_hud.render(text, True, col)
        surface.blit(val, val.get_rect(midleft=(cx + 14, y)))
        if not ok:
            hint = self.font_hint.render(
                "сумма зарядов ионов должна быть 0", True, config.MUTED)
            surface.blit(hint, hint.get_rect(center=(cx, y + 28)))

    def _draw_confirm(self, surface):
        solved = self.logic.builder.solved
        rect = pygame.Rect(0, 0, 280, 52)
        rect.center = (config.WIDTH // 2, 560)
        col = config.ACCENT if solved else BTN_OFF
        pygame.draw.rect(surface, col, rect, border_radius=12)
        t = self.font_btn.render("Дальше ▶", True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=rect.center))
        self._hit["confirm"] = rect

    def _draw_footer(self, surface):
        if self._msg:
            m = self.font_hint.render(self._msg, True, config.RED)
            surface.blit(m, m.get_rect(center=(config.WIDTH // 2, 624)))
        tip = self.font_hint.render(
            "Внешний индекс → коэффициент перед ионом; индекс внутри иона "
            "(напр. ₄ в SO₄) остаётся. Задай каждому иону заряд.",
            True, config.MUTED)
        surface.blit(tip, tip.get_rect(center=(config.WIDTH // 2,
                                               config.HEIGHT - 28)))

    def _draw_end(self, surface):
        L = self.logic
        cx = config.WIDTH // 2
        panel = pygame.Rect(0, 0, 600, 260)
        panel.center = (cx, config.HEIGHT // 2)
        card = pygame.Surface(panel.size, pygame.SRCALPHA)
        card.fill((255, 255, 255, 240))
        surface.blit(card, panel.topleft)
        pygame.draw.rect(surface, config.ACCENT, panel, width=3, border_radius=18)
        head = self.font_title.render("Уровень пройден!", True, config.INK)
        surface.blit(head, head.get_rect(center=(cx, panel.top + 60)))
        score = self.font_formula.render(
            f"{L.solved_count} / {L.rounds_total}", True, config.ACCENT)
        surface.blit(score, score.get_rect(center=(cx, panel.top + 130)))
        hint = self.font_hint.render(
            "Клик — сыграть заново", True, config.MUTED)
        surface.blit(hint, hint.get_rect(center=(cx, panel.bottom - 36)))


def _gradient(size, top, bottom) -> pygame.Surface:
    surf = pygame.Surface(size)
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (size[0], y))
    return surf


def run():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Уровень 2 — ионные уравнения")
    clock = pygame.time.Clock()
    scene = Level2Scene()
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
