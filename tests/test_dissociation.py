"""Тесты диссоциации на ионы (уровень 2): коэффициенты, заряды, баланс."""

import pytest

from chemistry import by_id
from chemistry.dissociation import dissociate
from chemistry.substances import SUBSTANCES


@pytest.mark.parametrize(
    "sid, cat_coeff, cat_charge, an_coeff, an_charge",
    [
        ("NaCl", 1, +1, 1, -1),
        ("CaCl2", 1, +2, 2, -1),       # внешний 2 у Cl → коэффициент
        ("Ca(OH)2", 1, +2, 2, -1),
        ("Al2(SO4)3", 2, +3, 3, -2),   # классика: 2 и 3 в коэффициенты, 4 внутри
        ("Na3PO4", 3, +1, 1, -3),
        ("K2SO4", 2, +1, 1, -2),
        ("BaCl2", 1, +2, 2, -1),
        ("H2SO4", 2, +1, 1, -2),       # сильная кислота диссоциирует нацело
        ("Na2CO3", 2, +1, 1, -2),
    ],
)
def test_dissociation(sid, cat_coeff, cat_charge, an_coeff, an_charge):
    d = dissociate(by_id(sid))
    assert d.cation_term.coeff == cat_coeff
    assert d.cation_term.charge == cat_charge
    assert d.anion_term.coeff == an_coeff
    assert d.anion_term.charge == an_charge


def test_internal_index_stays_in_ion():
    """Внутренний индекс многоатомного иона остаётся в формуле иона."""
    d = dissociate(by_id("Al2(SO4)3"))
    assert d.anion_term.ion.formula == "SO4"   # 4 — часть иона, не коэффициент
    assert d.anion_term.coeff == 3             # «внешняя» тройка — коэффициент


def test_charge_balance_always_zero():
    """Для любого реагента сумма зарядов ионов нулевая (электронейтральность)."""
    for s in SUBSTANCES:
        assert dissociate(s).charge_balance == 0


def test_display():
    assert dissociate(by_id("Al2(SO4)3")).cation_term.display == "2Al³⁺"
    assert dissociate(by_id("Na3PO4")).anion_term.display == "PO₄³⁻"
