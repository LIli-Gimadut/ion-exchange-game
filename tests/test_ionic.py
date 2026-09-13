"""Тесты полного и сокращённого ионных уравнений (уровень 2)."""

import pytest

from chemistry import SUBSTANCES, by_id
from chemistry.ionic import full_ionic, net_ionic
from chemistry.reactions import reacts


@pytest.mark.parametrize(
    "a, b, full, net, spectators",
    [
        ("BaCl2", "Na2SO4",
         "Ba²⁺ + 2Cl⁻ + 2Na⁺ + SO₄²⁻ → BaSO₄↓ + 2Na⁺ + 2Cl⁻",
         "Ba²⁺ + SO₄²⁻ → BaSO₄↓", {"Na": 2, "Cl": 2}),
        ("AgNO3", "NaCl",
         "Ag⁺ + NO₃⁻ + Na⁺ + Cl⁻ → AgCl↓ + Na⁺ + NO₃⁻",
         "Ag⁺ + Cl⁻ → AgCl↓", {"Na": 1, "NO3": 1}),
        ("HCl", "NaOH",
         "H⁺ + Cl⁻ + Na⁺ + OH⁻ → H₂O + Na⁺ + Cl⁻",
         "H⁺ + OH⁻ → H₂O", {"Na": 1, "Cl": 1}),
        ("Na2CO3", "HCl",
         "2Na⁺ + CO₃²⁻ + 2H⁺ + 2Cl⁻ → 2Na⁺ + 2Cl⁻ + CO₂↑ + H₂O",
         "CO₃²⁻ + 2H⁺ → CO₂↑ + H₂O", {"Na": 2, "Cl": 2}),
        ("CaCl2", "Na3PO4",
         "3Ca²⁺ + 6Cl⁻ + 6Na⁺ + 2PO₄³⁻ → Ca₃(PO₄)₂↓ + 6Na⁺ + 6Cl⁻",
         "3Ca²⁺ + 2PO₄³⁻ → Ca₃(PO₄)₂↓", {"Na": 6, "Cl": 6}),
    ],
)
def test_known(a, b, full, net, spectators):
    f = full_ionic(by_id(a), by_id(b))
    assert f is not None
    assert f.equation == full
    n = net_ionic(f)
    assert n.equation == net
    assert n.spectators == spectators


def test_gcd_reduction():
    """Ba(OH)2 + HCl: коэффициенты сокращённого делятся на общий множитель."""
    n = net_ionic(full_ionic(by_id("Ba(OH)2"), by_id("HCl")))
    assert n.equation == "OH⁻ + H⁺ → H₂O"          # 2OH/2H/2H2O → /2


def test_calcium_hydroxide_is_strong_base():
    """Ca(OH)2 (известковая вода) расписывается на ионы как щёлочь."""
    from chemistry.dissociation import dissociate
    from chemistry.ionic import is_strong_electrolyte

    ca_oh = by_id("Ca(OH)2")
    assert is_strong_electrolyte(ca_oh)
    assert dissociate(ca_oh).display == "Ca(OH)2 → Ca²⁺ + 2OH⁻"
    # как реагент в полном ионном тоже идёт ионами
    f = full_ionic(ca_oh, by_id("Na2CO3"))
    assert any(s.as_ions and s.formula == "Ca(OH)2" for s in f.left)
    assert net_ionic(f).equation == "Ca²⁺ + CO₃²⁻ → CaCO₃↓"


def test_weak_acid_reactant_stays_molecular():
    """Слабая кислота-реагент (HF) не расписывается на ионы."""
    f = full_ionic(by_id("HF"), by_id("CaCl2"))
    assert f is not None
    # HF присутствует как молекула, а не как H⁺ + F⁻
    assert any(not s.as_ions and s.formula == "HF" for s in f.left)


def test_precipitate_and_water_are_molecular():
    f = full_ionic(by_id("BaCl2"), by_id("Na2SO4"))
    baso4 = [s for s in f.right if s.formula == "BaSO4"][0]
    assert not baso4.as_ions and baso4.mark == "↓"


def test_full_ionic_for_every_reacting_pair_builds():
    """Для любой идущей реакции полное и сокращённое строятся без ошибок."""
    from itertools import combinations
    built = 0
    for a, b in combinations(SUBSTANCES, 2):
        if reacts(a, b) is None:
            continue
        f = full_ionic(a, b)
        assert f is not None, (a.id, b.id)
        n = net_ionic(f)
        assert n.left and n.right, (a.id, b.id)
        # в сокращённом не должно остаться иона по обе стороны (всё сокращено)
        lkeys = {t.ion.key for s in n.left if s.as_ions for t in s.ions}
        rkeys = {t.ion.key for s in n.right if s.as_ions for t in s.ions}
        assert lkeys.isdisjoint(rkeys), (a.id, b.id, lkeys & rkeys)
        built += 1
    assert built > 1000
