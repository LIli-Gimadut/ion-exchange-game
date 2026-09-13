"""Тесты логики конструктора диссоциации (уровень 2, headless)."""

import random

from chemistry import by_id
from game.builder import DissociationBuilder, Level2Logic


def _solve(b: DissociationBuilder) -> None:
    """Выставить все поля в эталон."""
    for ti in b.terms:
        ti.coeff = ti.target.coeff
        ti.charge_mag = abs(ti.target.charge)
        ti.charge_sign = 1 if ti.target.charge > 0 else -1


def test_starts_unsolved():
    b = DissociationBuilder(by_id("Al2(SO4)3"))
    assert not b.solved
    # дефолтные значения (1, +1 / 1, +1) почти всегда неверны
    assert not b.cation.coeff_ok or not b.cation.charge_ok or not b.anion.solved


def test_per_field_validation():
    b = DissociationBuilder(by_id("Al2(SO4)3"))
    cat = b.cation                       # цель: 2Al³⁺
    cat.coeff = 2
    assert cat.coeff_ok and not cat.charge_ok
    cat.charge_mag, cat.charge_sign = 3, 1
    assert cat.charge_ok and cat.solved
    assert not b.solved                  # анион ещё не собран


def test_full_solve():
    b = DissociationBuilder(by_id("Al2(SO4)3"))
    _solve(b)
    assert b.solved
    assert b.charge_balanced


def test_spinner_clamps():
    b = DissociationBuilder(by_id("NaCl"))
    ti = b.cation
    for _ in range(20):
        ti.bump_coeff(+1)
    assert ti.coeff == 6
    for _ in range(20):
        ti.bump_coeff(-1)
    assert ti.coeff == 1
    for _ in range(20):
        ti.bump_mag(+1)
    assert ti.charge_mag == 3


def test_toggle_sign():
    ti = DissociationBuilder(by_id("NaCl")).cation
    assert ti.charge_sign == 1
    ti.toggle_sign()
    assert ti.charge_sign == -1


def test_charge_balance_signal():
    b = DissociationBuilder(by_id("CaCl2"))   # 1 Ca²⁺ + 2 Cl⁻
    b.cation.coeff, b.cation.charge_mag, b.cation.charge_sign = 1, 2, 1
    b.anion.coeff, b.anion.charge_mag, b.anion.charge_sign = 1, 1, -1
    assert not b.charge_balanced              # +2 + (−1) = +1
    b.anion.coeff = 2
    assert b.charge_balanced                  # +2 + 2·(−1) = 0


def test_level_sequences_rounds():
    L = Level2Logic(random.Random(1), rounds=3)
    assert L.round_no == 1
    assert not L.finished
    for expected in (1, 2, 3):
        assert L.round_no == expected
        assert not L.confirm()      # ещё не решено → не двигаемся
        _solve(L.builder)
        assert L.confirm()          # решено → дальше
    assert L.finished
    assert L.solved_count == 3


def test_level_picks_distinct():
    L = Level2Logic(random.Random(2), rounds=5)
    assert len({s.id for s in L.substances}) == 5
