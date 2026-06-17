"""Консистентность сгенерированного набора веществ-реагентов."""

from chemistry import SUBSTANCES, compound_formula
from chemistry.reactions import _formula_counts
from chemistry.solubility import solubility
from chemistry.substances import ACID, ALKALI, SALT


def test_charge_balance():
    for s in SUBSTANCES:
        n_cat, n_an = _formula_counts(s)
        assert s.cation.charge * n_cat + s.anion.charge * n_an == 0, s.id


def test_formula_matches_ions():
    for s in SUBSTANCES:
        assert compound_formula(s.cation, s.anion) == s.formula, s.id


def test_ids_unique():
    ids = [s.id for s in SUBSTANCES]
    assert len(ids) == len(set(ids))


def test_kind_valid():
    for s in SUBSTANCES:
        assert s.kind in {SALT, ACID, ALKALI}


def test_color_is_rgba():
    for s in SUBSTANCES:
        assert len(s.color) == 4
        assert all(0 <= c <= 255 for c in s.color)


def test_reagents_are_soluble():
    """Реагенты-растворы должны быть растворимы (соли 'Р', щёлочи 'Р')."""
    for s in SUBSTANCES:
        if s.kind == SALT:
            assert solubility(s.cation_key, s.anion_key) == "Р", s.id
        elif s.kind == ALKALI:
            assert s.anion_key == "OH"
            assert solubility(s.cation_key, "OH") == "Р", s.id
        else:  # кислота
            assert s.cation_key == "H"


def test_has_each_kind():
    kinds = {s.kind for s in SUBSTANCES}
    assert {SALT, ACID, ALKALI} <= kinds
