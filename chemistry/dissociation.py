"""Диссоциация растворимого сильного электролита на ионы (уровень 2).

Чтобы записать ионное уравнение, формулу раскладывают на ионы. Ключевые правила,
которые тренирует уровень 2:

* индекс ВНЕ иона (число формульных единиц катиона/аниона, напр. 2 у Al и 3 у
  группы (SO4) в Al2(SO4)3) выносится в **коэффициент** перед ионом;
* индекс ВНУТРИ многоатомного иона (4 в SO4) остаётся частью **формулы иона** и
  коэффициентом не становится;
* каждому иону приписывается его **заряд** из каталога ионов.

Сумма зарядов всегда нулевая (электронейтральность), что и гарантирует
правильность подобранных коэффициентов.

Модуль чисто доменный — без pygame, тестируется headless.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from chemistry.ions import Ion
from chemistry.substances import Substance


def _counts(sub: Substance) -> tuple[int, int]:
    """(n_катион, n_анион): сколько ионов даёт одна формульная единица.

    Это ровно те «внешние» индексы, что становятся коэффициентами в записи
    диссоциации. Для NaCl → (1, 1); для Al2(SO4)3 → (2, 3); для Ca(OH)2 → (1, 2).
    """
    c, a = sub.cation.charge, -sub.anion.charge
    total = c * a // gcd(c, a)
    return total // c, total // a


@dataclass(frozen=True)
class IonTerm:
    """Один ион в записи диссоциации: коэффициент + ион (+ его заряд)."""

    coeff: int   # «внешний» индекс, ставший коэффициентом перед ионом
    ion: Ion

    @property
    def charge(self) -> int:
        return self.ion.charge

    @property
    def display(self) -> str:
        """Полная запись терма, напр. '2Al³⁺', '3SO₄²⁻', 'OH⁻'."""
        head = "" if self.coeff == 1 else str(self.coeff)
        return head + self.ion.display


@dataclass(frozen=True)
class Dissociation:
    """Разложение растворимого вещества на катион- и анион-термы."""

    substance: Substance
    cation_term: IonTerm
    anion_term: IonTerm

    @property
    def terms(self) -> tuple[IonTerm, IonTerm]:
        return (self.cation_term, self.anion_term)

    @property
    def charge_balance(self) -> int:
        """Сумма зарядов всех ионов (всегда 0 для корректной формулы)."""
        return sum(t.coeff * t.charge for t in self.terms)

    @property
    def display(self) -> str:
        """Запись диссоциации, напр. 'Al2(SO4)3 → 2Al³⁺ + 3SO₄²⁻'."""
        return (f"{self.substance.formula} → "
                f"{self.cation_term.display} + {self.anion_term.display}")


def dissociate(sub: Substance) -> Dissociation:
    """Эталонное разложение растворимого вещества на ионы."""
    n_cat, n_an = _counts(sub)
    return Dissociation(
        sub,
        IonTerm(n_cat, sub.cation),
        IonTerm(n_an, sub.anion),
    )
