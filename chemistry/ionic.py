"""Полное и сокращённое ионные уравнения (уровень 2, механики №5/№6).

Из молекулярного уравнения РИО строится:

* **полное ионное** — сильные растворимые электролиты расписаны на ионы, а
  осадки (↓), газы (↑), вода и слабые электролиты остаются молекулами;
* **сокращённое ионное** — одинаковые ионы по обе стороны (ионы-зрители)
  сокращаются, оставшиеся коэффициенты делятся на общий множитель.

Правила «расписывать на ионы»:

* соли-реагенты — всегда (берутся только растворимые);
* кислоты — только сильные (Cl, Br, I, NO3, SO4); слабые (HF, H2S, H2SO3,
  HNO2, H3PO4) остаются молекулами;
* щёлочи — сильные растворимые (Na, K, Li, Ba); Ca(OH)2 малорастворима → молекула;
* продукты — растворимый сильный (state == 'soluble') расписывается; осадок/газ/
  вода/слабый/малорастворимый — молекула.

Модуль чисто доменный, без pygame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd

from chemistry.dissociation import IonTerm
from chemistry.ions import Ion, to_subscript_formula
from chemistry.reactions import Product, _balance, react
from chemistry.substances import ACID, ALKALI, SALT, Substance

STRONG_ACID_ANIONS = {"Cl", "Br", "I", "NO3", "SO4"}
# Щёлочи. Ca(OH)2 малорастворима ('М'), но в школьном курсе это щёлочь и в
# растворе (известковая вода) расписывается на ионы — поэтому Ca включён.
STRONG_BASE_CATIONS = {"Na", "K", "Li", "Ba", "Ca"}


def _counts(cation: Ion, anion: Ion) -> tuple[int, int]:
    """(n_катион, n_анион) на одну формульную единицу для пары ионов."""
    c, a = cation.charge, -anion.charge
    total = c * a // gcd(c, a)
    return total // c, total // a


def is_strong_electrolyte(sub: Substance) -> bool:
    """Расписывается ли реагент-раствор на ионы (сильный растворимый электролит).

    Соли-реагенты — да (берутся только растворимые); кислоты — только сильные
    (Cl, Br, I, NO3, SO4); щёлочи — Na, K, Li, Ba и Ca(OH)2 (известковая вода).
    Слабые кислоты (HF, H2S, H2SO3, HNO2, H3PO4) — нет (остаются молекулами).
    """
    if sub.kind == SALT:
        return True
    if sub.kind == ACID:
        return sub.anion_key in STRONG_ACID_ANIONS
    if sub.kind == ALKALI:
        return sub.cation_key in STRONG_BASE_CATIONS
    return False


# внутренний псевдоним для прежних вызовов
_reactant_as_ions = is_strong_electrolyte


@dataclass(frozen=True)
class Species:
    """Участник ионного уравнения: либо набор ионов, либо молекула."""

    coeff: int
    formula: str
    as_ions: bool
    ions: tuple[IonTerm, ...] = ()
    mark: str = ""          # ↓ / ↑ для молекулярной записи
    is_water: bool = False

    @property
    def text(self) -> str:
        """Текстовая запись (юникод-индексы). Для ионов — 'a + b'."""
        if self.as_ions:
            return " + ".join(t.display for t in self.ions)
        head = "" if self.coeff == 1 else str(self.coeff)
        return head + to_subscript_formula(self.formula) + self.mark


def _reactant_species(sub: Substance, coeff: int) -> Species:
    if _reactant_as_ions(sub):
        n_cat, n_an = _counts(sub.cation, sub.anion)
        ions = (IonTerm(coeff * n_cat, sub.cation),
                IonTerm(coeff * n_an, sub.anion))
        return Species(coeff, sub.formula, True, ions)
    return Species(coeff, sub.formula, False)


def _product_species(p: Product, coeff: int) -> list[Species]:
    if p.state == "soluble":
        n_cat, n_an = _counts(p.cation, p.anion)
        ions = (IonTerm(coeff * n_cat, p.cation),
                IonTerm(coeff * n_an, p.anion))
        return [Species(coeff, p.formula, True, ions)]
    if p.state == "gas":
        out = [Species(coeff, p.formula, False, mark="↑")]
        if p.releases_water:
            out.append(Species(coeff, "H2O", False, is_water=True))
        return out
    if p.state == "water":
        return [Species(coeff, "H2O", False, is_water=True)]
    if p.state == "precipitate":
        return [Species(coeff, p.formula, False, mark="↓")]
    # weak / slight — молекула без пометки
    return [Species(coeff, p.formula, False)]


@dataclass(frozen=True)
class FullIonic:
    left: tuple[Species, ...]
    right: tuple[Species, ...]

    @property
    def equation(self) -> str:
        L = " + ".join(s.text for s in self.left)
        R = " + ".join(s.text for s in self.right)
        return f"{L} → {R}"


def full_ionic(a: Substance, b: Substance) -> FullIonic | None:
    """Полное ионное уравнение для пары реагентов либо None (нет реакции)."""
    res = react(a, b)
    if res is None:
        return None
    coeffs = _balance(a, b, res.products)
    if coeffs is None:
        return None
    ka, kb, k1, k2 = coeffs
    left = (_reactant_species(a, ka), _reactant_species(b, kb))
    right: list[Species] = []
    right += _product_species(res.products[0], k1)
    right += _product_species(res.products[1], k2)
    return FullIonic(left, tuple(right))


@dataclass(frozen=True)
class NetIonic:
    left: tuple[Species, ...]
    right: tuple[Species, ...]
    spectators: dict[str, int]   # ключ иона -> сколько сокращено с каждой стороны

    @property
    def equation(self) -> str:
        L = " + ".join(s.text for s in self.left)
        R = " + ".join(s.text for s in self.right)
        return f"{L} → {R}"


def _ion_pool(species: tuple[Species, ...]) -> dict[str, list]:
    """key -> [Ion, суммарный коэффициент] по всем расписанным на ионы видам."""
    pool: dict[str, list] = {}
    for s in species:
        if not s.as_ions:
            continue
        for t in s.ions:
            entry = pool.setdefault(t.ion.key, [t.ion, 0])
            entry[1] += t.coeff
    return pool


def net_ionic(full: FullIonic) -> NetIonic:
    """Сокращённое ионное: убрать ионы-зрители и поделить на общий множитель."""
    left_pool = _ion_pool(full.left)
    right_pool = _ion_pool(full.right)

    spectators: dict[str, int] = {}
    for key in set(left_pool) & set(right_pool):
        m = min(left_pool[key][1], right_pool[key][1])
        if m:
            spectators[key] = m
            left_pool[key][1] -= m
            right_pool[key][1] -= m

    left: list[Species] = [s for s in full.left if not s.as_ions]
    left += [Species(c, ion.formula, True, (IonTerm(c, ion),))
             for ion, c in left_pool.values() if c > 0]
    right: list[Species] = [s for s in full.right if not s.as_ions]
    right += [Species(c, ion.formula, True, (IonTerm(c, ion),))
              for ion, c in right_pool.values() if c > 0]

    # сократить все коэффициенты на общий делитель
    coeffs = [s.coeff for s in left + right]
    g = 0
    for c in coeffs:
        g = gcd(g, c)
    if g > 1:
        left = [_scale(s, g) for s in left]
        right = [_scale(s, g) for s in right]

    return NetIonic(tuple(left), tuple(right), spectators)


def _scale(s: Species, g: int) -> Species:
    coeff = s.coeff // g
    if s.as_ions:
        ions = tuple(IonTerm(t.coeff // g, t.ion) for t in s.ions)
        return Species(coeff, s.formula, True, ions, s.mark, s.is_water)
    return Species(coeff, s.formula, False, (), s.mark, s.is_water)
