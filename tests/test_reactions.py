"""Тесты движка РИО — ядро корректности (расширенный набор)."""

from itertools import combinations

import pytest

from chemistry import by_id, react
from chemistry.reactions import is_clean_no_reaction, reacts
from chemistry.substances import SUBSTANCES

# Регрессионные якоря (меняются только при осознанном изменении химии).
N_REAGENTS = 104
N_REACTING_PAIRS = 1565
EFFECT_COUNTS = {"GAS": 165, "WATER": 41, "PRECIPITATE": 1359}


@pytest.mark.parametrize(
    "a, b, effect, star",
    [
        ("Na2CO3", "HCl", "GAS", "CO2"),
        ("Na2S", "HCl", "GAS", "H2S"),
        ("Na2SO3", "H2SO4", "GAS", "SO2"),
        ("NH4Cl", "NaOH", "GAS", "NH3"),
        ("BaCl2", "Na2SO4", "PRECIPITATE", "BaSO4"),
        ("AgNO3", "NaCl", "PRECIPITATE", "AgCl"),
        ("CuSO4", "NaOH", "PRECIPITATE", "Cu(OH)2"),
        ("CaCl2", "NaF", "PRECIPITATE", "CaF2"),
        ("Pb(NO3)2", "KI", "PRECIPITATE", "PbI2"),
        ("K2SiO3", "HCl", "PRECIPITATE", "H2SiO3"),
        ("Na3PO4", "CaCl2", "PRECIPITATE", "Ca3(PO4)2"),
        ("HCl", "NaOH", "WATER", "H2O"),
        ("H2SO4", "KOH", "WATER", "H2O"),
    ],
)
def test_positive(a, b, effect, star):
    r = react(by_id(a), by_id(b))
    assert r is not None
    assert r.effect == effect
    assert r.star_formula == star


@pytest.mark.parametrize(
    "a, b",
    [
        ("NaCl", "KNO3"),       # все продукты растворимы
        ("KNO3", "Na2SO4"),
        ("NaCl", "KOH"),
        ("BaCl2", "KNO3"),
    ],
)
def test_negative(a, b):
    assert react(by_id(a), by_id(b)) is None
    assert is_clean_no_reaction(by_id(a), by_id(b)) is True


@pytest.mark.parametrize(
    "a, b",
    [
        ("NaF", "HCl"),          # образуется слабая HF — не «чистое отсутствие»
        ("CaCl2", "Na2SO4"),     # CaSO4 малорастворим ('М')
        ("AgNO3", "Na2SO4"),     # Ag2SO4 'М'
        ("Cu(NO3)2", "KI"),      # CuI2 не существует ('-')
        ("AlCl3", "Na2CO3"),     # Al2(CO3)3 не существует
    ],
)
def test_no_visible_but_not_clean(a, b):
    """Нет видимой реакции, но и не «чистое отсутствие» — не дистрактор."""
    assert react(by_id(a), by_id(b)) is None
    assert is_clean_no_reaction(by_id(a), by_id(b)) is False


def test_no_self_reaction():
    for s in SUBSTANCES:
        assert react(s, s) is None
        assert reacts(s, s) is None


def test_symmetry():
    for a, b in combinations(SUBSTANCES, 2):
        r1 = react(a, b)
        r2 = react(b, a)
        assert (r1 is None) == (r2 is None), (a.id, b.id)
        if r1 is not None:
            assert r1.effect == r2.effect
            assert r1.star_formula == r2.star_formula


def test_no_excluded_product_leaks():
    for a, b in combinations(SUBSTANCES, 2):
        r = react(a, b)
        if r is not None:
            assert all(p.state != "excluded" for p in r.products), (a.id, b.id)


def test_is_clean_implies_no_reaction():
    for a, b in combinations(SUBSTANCES, 2):
        if is_clean_no_reaction(a, b):
            assert react(a, b) is None


def test_regression_anchors():
    assert len(SUBSTANCES) == N_REAGENTS
    counts = {"GAS": 0, "WATER": 0, "PRECIPITATE": 0}
    total = 0
    for a, b in combinations(SUBSTANCES, 2):
        e = reacts(a, b)
        if e is not None:
            counts[e] += 1
            total += 1
    assert total == N_REACTING_PAIRS
    assert counts == EFFECT_COUNTS


def test_reacts_matches_react():
    """Дешёвый reacts() согласован с полным react()."""
    for a, b in combinations(SUBSTANCES, 2):
        e = reacts(a, b)
        r = react(a, b)
        assert (e is None) == (r is None)
        if e is not None:
            assert e == r.effect
