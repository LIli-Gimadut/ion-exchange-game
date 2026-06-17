"""Тесты таблицы растворимости (расширенная, со школьными ионами)."""

import pytest

from chemistry.solubility import ANIONS, SALT_CATIONS, exists, solubility


@pytest.mark.parametrize(
    "cat, an, expected",
    [
        ("Ag", "Cl", "Н"),
        ("Ag", "F", "Р"),     # AgF — исключение среди галогенидов серебра
        ("Ba", "SO4", "Н"),
        ("Ca", "OH", "М"),
        ("Pb", "Cl", "М"),
        ("Pb", "I", "Н"),
        ("Na", "PO4", "Р"),
        ("Cu", "I", "-"),     # CuI2 не существует (редокс)
        ("Ba", "S", "-"),     # BaS гидролизуется
        ("Al", "CO3", "-"),   # Al2(CO3)3 не существует
    ],
)
def test_known_values(cat, an, expected):
    assert solubility(cat, an) == expected


def test_table_complete():
    for cat in SALT_CATIONS:
        for an in ANIONS:
            solubility(cat, an)  # не должно бросать KeyError


def test_values_in_domain():
    for cat in SALT_CATIONS:
        for an in ANIONS:
            assert solubility(cat, an) in {"Р", "М", "Н", "-"}


def test_exists():
    assert exists("Na", "Cl") is True
    assert exists("Ag", "Cl") is True       # существует, хоть и нерастворим
    assert exists("Cu", "I") is False
    assert exists("Al", "S") is False


def test_unknown_pair_raises():
    with pytest.raises(KeyError):
        solubility("Au", "Cl")
