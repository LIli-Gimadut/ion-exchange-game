"""Ионы: внутренний ключ, формульная запись, знак заряда.

Заряд хранится со знаком: катионы > 0, анионы < 0.
`polyatomic` отмечает многоатомные группы (OH, NH4, SO3, SO4, NO3, NO2, CO3,
SiO3, PO4), которые в формуле берутся в скобки, когда индекс > 1 (Ba(OH)2).
"""

from __future__ import annotations

from dataclasses import dataclass

_SUP = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻",
}
_SUB = {str(d): chr(0x2080 + d) for d in range(10)}


def to_superscript(text: str) -> str:
    return "".join(_SUP.get(ch, ch) for ch in text)


def to_subscript(text: str) -> str:
    return "".join(_SUB.get(ch, ch) for ch in text)


@dataclass(frozen=True)
class Ion:
    key: str           # внутренний id, напр. "Na", "SO4"
    formula: str       # запись атомов, напр. "Na", "SO4", "OH", "NH4"
    charge: int        # со знаком: +1, +2, +3, -1, -2, -3
    polyatomic: bool = False

    @property
    def is_cation(self) -> bool:
        return self.charge > 0

    @property
    def display(self) -> str:
        """Символ с зарядом в верхнем индексе, напр. 'Na⁺', 'SO₄²⁻'."""
        mag = abs(self.charge)
        sign = "+" if self.charge > 0 else "-"
        num = "" if mag == 1 else str(mag)
        return to_subscript_formula(self.formula) + to_superscript(num + sign)


def to_subscript_formula(formula: str) -> str:
    """'SO4' -> 'SO₄', 'NH4' -> 'NH₄' (цифры в нижний индекс)."""
    return "".join(to_subscript(ch) if ch.isdigit() else ch for ch in formula)


# --- Каталог ионов ---------------------------------------------------------
_IONS = [
    # катионы: H, NH4 и металлы ряда активности (без экзотики)
    Ion("H", "H", +1),
    Ion("NH4", "NH4", +1, polyatomic=True),
    Ion("K", "K", +1),
    Ion("Na", "Na", +1),
    Ion("Li", "Li", +1),
    Ion("Ag", "Ag", +1),
    Ion("Ba", "Ba", +2),
    Ion("Ca", "Ca", +2),
    Ion("Mg", "Mg", +2),
    Ion("Al", "Al", +3),
    Ion("Zn", "Zn", +2),
    Ion("Fe", "Fe", +2),
    Ion("Ni", "Ni", +2),
    Ion("Pb", "Pb", +2),
    Ion("Cu", "Cu", +2),
    # анионы: кислотные остатки школьного курса (без органических)
    Ion("OH", "OH", -1, polyatomic=True),
    Ion("F", "F", -1),
    Ion("Cl", "Cl", -1),
    Ion("Br", "Br", -1),
    Ion("I", "I", -1),
    Ion("S", "S", -2),
    Ion("SO3", "SO3", -2, polyatomic=True),
    Ion("SO4", "SO4", -2, polyatomic=True),
    Ion("NO3", "NO3", -1, polyatomic=True),
    Ion("NO2", "NO2", -1, polyatomic=True),
    Ion("CO3", "CO3", -2, polyatomic=True),
    Ion("SiO3", "SiO3", -2, polyatomic=True),
    Ion("PO4", "PO4", -3, polyatomic=True),
]

ION: dict[str, Ion] = {ion.key: ion for ion in _IONS}

CATIONS = [i for i in _IONS if i.is_cation]
ANIONS = [i for i in _IONS if not i.is_cation]
