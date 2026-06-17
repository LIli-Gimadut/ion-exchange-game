"""Движок реакций ионного обмена (РИО).

`react(a, b)` определяет, идёт ли между двумя веществами реакция обмена
`AB + CD -> AD + CB`, и какой эффект наблюдается. Реакция идёт до конца, если
хотя бы один продукт обмена:

* осадок  — нерастворим по таблице растворимости ('Н'), включая H2SiO3↓;
* газ     — CO2↑ (из H2CO3), SO2↑ (из H2SO3), H2S↑, NH3↑ (из NH4OH);
* вода    — нейтрализация H⁺ + OH⁻.

Слабые электролиты без видимого эффекта (HF, HNO2, H3PO4) и малорастворимые
('М') продукты не считаются «видимой» реакцией, но и не дают «чистого отсутствия
реакции» — такие пары в раундах не используются. Несуществующие/гидролизующиеся
комбинации ('-') исключаются полностью.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd
from typing import Literal

from chemistry.ions import Ion
from chemistry.solubility import solubility
from chemistry.substances import Substance

Effect = Literal["GAS", "PRECIPITATE", "WATER"]
GAS: Effect = "GAS"
PRECIPITATE: Effect = "PRECIPITATE"
WATER: Effect = "WATER"

State = Literal[
    "soluble", "slight", "precipitate", "gas", "water", "weak", "excluded"
]

# Газы: (катион, анион) -> (формула газа, выделяется ли вода).
_GAS_FROM = {
    ("H", "CO3"): ("CO2", True),
    ("H", "SO3"): ("SO2", True),
    ("H", "S"): ("H2S", False),
    ("NH4", "OH"): ("NH3", True),
}
# Слабые электролиты без видимого эффекта.
_WEAK = {("H", "F"), ("H", "NO2"), ("H", "PO4")}


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def compound_formula(cation: Ion, anion: Ion) -> str:
    """Строит нейтральную формулу из катиона и аниона, напр. Al2(SO4)3."""
    c, a = cation.charge, -anion.charge
    total = _lcm(c, a)
    n_cat, n_an = total // c, total // a

    def part(ion: Ion, n: int) -> str:
        if n == 1:
            return ion.formula
        if ion.polyatomic:
            return f"({ion.formula}){n}"
        return f"{ion.formula}{n}"

    return part(cation, n_cat) + part(anion, n_an)


@dataclass(frozen=True)
class Product:
    cation: Ion
    anion: Ion
    state: State
    formula: str            # формула продукта (для газа — формула газа)
    releases_water: bool = False  # газ из нестойкой кислоты/основания


def _classify_product(cation: Ion, anion: Ion) -> Product:
    pair = (cation.key, anion.key)
    if pair == ("H", "OH"):
        return Product(cation, anion, "water", "H2O")
    if pair in _GAS_FROM:
        gas, water = _GAS_FROM[pair]
        return Product(cation, anion, "gas", gas, releases_water=water)
    if pair == ("H", "SiO3"):
        return Product(cation, anion, "precipitate", "H2SiO3")
    if pair in _WEAK:
        return Product(cation, anion, "weak", compound_formula(cation, anion))
    if cation.key == "H":
        # сильная кислота (HCl, HBr, HI, HNO3, H2SO4) — растворима, не движет РИО
        return Product(cation, anion, "soluble", compound_formula(cation, anion))
    s = solubility(cation.key, anion.key)
    state: State = {"Р": "soluble", "М": "slight", "Н": "precipitate",
                    "-": "excluded"}[s]
    return Product(cation, anion, state, compound_formula(cation, anion))


@dataclass(frozen=True)
class ReactionResult:
    effect: Effect
    star_formula: str
    equation: str
    equation_segments: tuple[tuple[str, bool], ...] = ()  # (текст, подсветка)
    products: tuple[Product, ...] = field(default_factory=tuple)

    @property
    def gas(self) -> bool:
        return any(p.state == "gas" for p in self.products)

    @property
    def precipitate(self) -> bool:
        return any(p.state == "precipitate" for p in self.products)

    @property
    def water(self) -> bool:
        return any(p.state == "water" for p in self.products)


def _evaluate(a: Substance, b: Substance):
    """Дешёвая оценка без построения уравнения.

    Возвращает (effect, star, products) либо None. Используется и для графа
    реакций (без затрат на балансировку коэффициентов).
    """
    if a.id == b.id:
        return None
    products = (
        _classify_product(a.cation, b.anion),
        _classify_product(b.cation, a.anion),
    )
    if any(p.state == "excluded" for p in products):
        return None

    has_gas = any(p.state == "gas" for p in products)
    has_precip = any(p.state == "precipitate" for p in products)
    has_water = any(p.state == "water" for p in products)
    if not (has_gas or has_precip or has_water):
        return None

    if has_gas:
        effect = GAS
        star = min(p.formula for p in products if p.state == "gas")
    elif has_precip:
        effect = PRECIPITATE
        star = min(p.formula for p in products if p.state == "precipitate")
    else:
        effect, star = WATER, "H2O"
    return effect, star, products


def reacts(a: Substance, b: Substance) -> Effect | None:
    """Дешёвая проверка: тип эффекта РИО или None (без уравнения)."""
    res = _evaluate(a, b)
    return res[0] if res else None


def react(a: Substance, b: Substance) -> ReactionResult | None:
    """Полный результат РИО (с уравнением) либо None если реакции нет."""
    res = _evaluate(a, b)
    if res is None:
        return None
    effect, star, products = res
    equation, segments = _equation(a, b, products)
    return ReactionResult(effect, star, equation, tuple(segments), products)


def is_clean_no_reaction(a: Substance, b: Substance) -> bool:
    """True, если все продукты обмена однозначно растворимы (нет реакции).

    Отсекает не только осадок/газ/воду, но и малорастворимые ('М'), слабые
    электролиты и несуществующие пары — такие варианты неоднозначны и не годятся
    как дистракторы.
    """
    if a.id == b.id:
        return False
    products = (
        _classify_product(a.cation, b.anion),
        _classify_product(b.cation, a.anion),
    )
    return all(p.state == "soluble" for p in products)


# --- Составление уравнения с коэффициентами --------------------------------
def _formula_counts(sub: Substance) -> tuple[int, int]:
    c, a = sub.cation.charge, -sub.anion.charge
    total = _lcm(c, a)
    return total // c, total // a


def _balance(a, b, products):
    na_c, na_a = _formula_counts(a)
    nb_c, nb_a = _formula_counts(b)

    def prod_counts(p: Product) -> tuple[int, int]:
        c, an = p.cation.charge, -p.anion.charge
        total = _lcm(c, an)
        return total // c, total // an

    p1c, p1a = prod_counts(products[0])   # катион a + анион b
    p2c, p2a = prod_counts(products[1])   # катион b + анион a

    for ka in range(1, 13):
        for kb in range(1, 13):
            for k1 in range(1, 13):
                for k2 in range(1, 13):
                    if (
                        ka * na_c == k1 * p1c
                        and ka * na_a == k2 * p2a
                        and kb * nb_c == k2 * p2c
                        and kb * nb_a == k1 * p1a
                    ):
                        if gcd(gcd(ka, kb), gcd(k1, k2)) == 1:
                            return ka, kb, k1, k2
    return None


def _equation(a, b, products):
    coeffs = _balance(a, b, products)
    ka, kb, k1, k2 = coeffs if coeffs else (1, 1, 1, 1)

    def term(coef: int, formula: str, mark: str = "") -> str:
        head = "" if coef == 1 else str(coef)
        return f"{head}{formula}{mark}"

    def product_segments(coef: int, p: Product) -> list[tuple[str, bool]]:
        if p.state == "gas":
            segs = [(term(coef, p.formula, "↑"), True)]
            if p.releases_water:
                segs.append((term(coef, "H2O"), False))
            return segs
        if p.state == "precipitate":
            return [(term(coef, p.formula, "↓"), True)]
        if p.state == "water":
            return [(term(coef, "H2O"), True)]
        return [(term(coef, p.formula), False)]

    left = [(term(ka, a.formula), False), (" + ", False),
            (term(kb, b.formula), False), (" → ", False)]
    # все продуктные термы (газ может дать два: CO2↑ и H2O) через « + »
    terms: list[tuple[str, bool]] = []
    for coef, p in ((k1, products[0]), (k2, products[1])):
        terms.extend(product_segments(coef, p))
    right: list[tuple[str, bool]] = []
    for i, seg in enumerate(terms):
        if i > 0:
            right.append((" + ", False))
        right.append(seg)

    segments = left + right
    string = "".join(text for text, _ in segments)
    return string, segments
