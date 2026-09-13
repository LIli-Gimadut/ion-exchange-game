"""Тесты логики сокращения ионов-зрителей (уровень 2, headless)."""

import pytest

from chemistry import by_id
from game.cancel import CancelGame


def _game(a, b):
    return CancelGame(by_id(a), by_id(b))


def test_spectators_marked():
    g = _game("BaCl2", "Na2SO4")
    specs = {(t.side, t.ion_key) for t in g.tiles if t.is_spectator}
    # Na⁺ и Cl⁻ — зрители с обеих сторон
    assert specs == {("L", "Na"), ("L", "Cl"), ("R", "Na"), ("R", "Cl")}
    # Ba²⁺, SO₄²⁻ и осадок BaSO₄ — участники
    assert not any(t.is_spectator for t in g.tiles if t.ion_key in (None, "Ba", "SO4"))


def test_click_spectator_strikes():
    g = _game("AgNO3", "NaCl")
    spec = next(t for t in g.tiles if t.is_spectator)
    assert g.click(spec.tid) is True
    assert g.tile(spec.tid).struck


def test_click_participant_is_error():
    g = _game("BaCl2", "Na2SO4")
    part = next(t for t in g.tiles if not t.is_spectator and t.is_ion)
    assert g.click(part.tid) is False
    assert not g.tile(part.tid).struck


def test_click_molecule_is_error():
    g = _game("BaCl2", "Na2SO4")
    mol = next(t for t in g.tiles if not t.is_ion)   # BaSO₄↓
    assert g.click(mol.tid) is False


def test_reveal_requires_all_spectators():
    g = _game("BaCl2", "Na2SO4")
    specs = [t for t in g.tiles if t.is_spectator]
    for t in specs[:-1]:
        g.click(t.tid)
    assert not g.all_spectators_struck
    assert g.reveal() is False
    g.click(specs[-1].tid)
    assert g.all_spectators_struck
    assert g.reveal() is True
    assert g.revealed


def test_net_equation_available():
    g = _game("HCl", "NaOH")
    assert g.net.equation == "H⁺ + OH⁻ → H₂O"


def test_raises_when_no_reaction():
    with pytest.raises(ValueError):
        _game("NaCl", "KNO3")
