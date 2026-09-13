"""Логика конструктора диссоциации (уровень 2, механика №1) — без pygame.

Ученик для каждого иона выставляет спиннерами/стрелками три величины:

* **коэффициент** перед ионом (бывший «внешний» индекс);
* **знак** заряда (+/−);
* **величину** заряда (1, 2, 3).

Формула иона (с внутренним индексом, напр. SO₄) дана — её менять нельзя, в этом и
смысл: ученик должен понять, что «4» внутри SO₄ остаётся в ионе, а «3» снаружи
становится коэффициентом. Каждое поле проверяется независимо (зелёное = верно),
ответ не выбирается из вариантов, а собирается с нуля.

`Level2Logic` секвенирует несколько веществ-раундов. Всё тестируется headless.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from chemistry.dissociation import IonTerm, dissociate
from chemistry.ionic import is_strong_electrolyte
from chemistry.substances import SUBSTANCES, Substance

COEFF_MIN, COEFF_MAX = 1, 6
MAG_MIN, MAG_MAX = 1, 3


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


@dataclass
class TermInput:
    """Поля, которые ученик выставляет для одного иона, и их проверка."""

    target: IonTerm
    coeff: int = 1
    charge_mag: int = 1
    charge_sign: int = 1  # +1 или -1

    @property
    def charge(self) -> int:
        return self.charge_sign * self.charge_mag

    @property
    def coeff_ok(self) -> bool:
        return self.coeff == self.target.coeff

    @property
    def charge_ok(self) -> bool:
        return self.charge == self.target.charge

    @property
    def solved(self) -> bool:
        return self.coeff_ok and self.charge_ok

    def bump_coeff(self, d: int) -> None:
        self.coeff = _clamp(self.coeff + d, COEFF_MIN, COEFF_MAX)

    def bump_mag(self, d: int) -> None:
        self.charge_mag = _clamp(self.charge_mag + d, MAG_MIN, MAG_MAX)

    def toggle_sign(self) -> None:
        self.charge_sign = -self.charge_sign


class DissociationBuilder:
    """Конструктор разложения одного вещества на катион- и анион-термы."""

    def __init__(self, sub: Substance):
        self.substance = sub
        self.diss = dissociate(sub)
        self.cation = TermInput(self.diss.cation_term)
        self.anion = TermInput(self.diss.anion_term)

    @property
    def terms(self) -> tuple[TermInput, TermInput]:
        return (self.cation, self.anion)

    @property
    def solved(self) -> bool:
        return all(t.solved for t in self.terms)

    @property
    def student_charge_balance(self) -> int:
        """Сумма зарядов по ТЕКУЩИМ значениям ученика (цель — 0)."""
        return sum(t.coeff * t.charge for t in self.terms)

    @property
    def charge_balanced(self) -> bool:
        return self.student_charge_balance == 0


def _interesting(sub: Substance) -> bool:
    """Вещество, где хотя бы один коэффициент > 1 — наглядно учит индекс↔коэф."""
    d = dissociate(sub)
    return max(d.cation_term.coeff, d.anion_term.coeff) > 1


class Level2Logic:
    """Последовательность раундов «разбери формулу на ионы»."""

    def __init__(self, rng: random.Random | None = None, rounds: int = 5):
        self.rng = rng or random.Random()
        self.rounds_total = rounds
        self.substances = self._pick(rounds)
        self.index = 0
        self.solved_count = 0
        self.builder = DissociationBuilder(self.substances[0])

    def _pick(self, n: int) -> list[Substance]:
        # только сильные электролиты: слабые кислоты на ионы не расписываются
        strong = [s for s in SUBSTANCES if is_strong_electrolyte(s)]
        pool = [s for s in strong if _interesting(s)]
        self.rng.shuffle(pool)
        chosen = pool[:n]
        # добиваем простыми сильными, если «интересных» не хватило
        if len(chosen) < n:
            rest = [s for s in strong if s not in chosen]
            self.rng.shuffle(rest)
            chosen += rest[: n - len(chosen)]
        return chosen

    @property
    def round_no(self) -> int:
        return min(self.index + 1, self.rounds_total)

    @property
    def finished(self) -> bool:
        return self.index >= len(self.substances)

    def confirm(self) -> bool:
        """Подтвердить разбор. True, если верно и перешли дальше."""
        if not self.builder.solved:
            return False
        self.solved_count += 1
        self.index += 1
        if not self.finished:
            self.builder = DissociationBuilder(self.substances[self.index])
        return True

    def restart(self) -> None:
        self.substances = self._pick(self.rounds_total)
        self.index = 0
        self.solved_count = 0
        self.builder = DissociationBuilder(self.substances[0])
