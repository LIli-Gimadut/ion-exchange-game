"""Набор веществ-реагентов (растворы в пробирках).

Каждая пробирка — это РАСТВОР, поэтому реагентами могут быть только растворимые
вещества: растворимые соли ('Р'), сильные/растворимые кислоты и щёлочи.
Нерастворимые соединения встречаются лишь как продукты (осадки).

Список генерируется из таблицы растворимости, чтобы исключить ручные ошибки и
несуществующие/гидролизующиеся вещества.
"""

from __future__ import annotations

from dataclasses import dataclass

from chemistry.ions import ION, Ion
from chemistry.solubility import ANIONS, SALT_CATIONS, solubility

# Тип вещества
SALT = "соль"
ACID = "кислота"
ALKALI = "щёлочь"

# Цвета растворов (RGBA). Большинство бесцветны — лёгкий «водный» оттенок.
_COLORLESS = (205, 228, 238, 160)
_CATION_COLOR = {
    "Cu": (40, 130, 210, 200),    # голубой
    "Ni": (70, 175, 95, 185),     # зелёный
    "Fe": (150, 190, 140, 175),   # бледно-зелёный
}

# Кислоты школьного курса (без неустойчивых H2CO3/H2SiO3 как реагентов).
_ACID_ANIONS = ["F", "Cl", "Br", "I", "S", "SO3", "SO4", "NO3", "NO2", "PO4"]

# Щёлочи — только растворимые основания (реальные реактивы-растворы).
_ALKALI_CATIONS = ["Na", "K", "Ba", "Li", "Ca"]


@dataclass(frozen=True)
class Substance:
    id: str
    formula: str
    cation_key: str
    anion_key: str
    kind: str
    color: tuple[int, int, int, int] = _COLORLESS

    @property
    def cation(self) -> Ion:
        return ION[self.cation_key]

    @property
    def anion(self) -> Ion:
        return ION[self.anion_key]


def _formula(cation_key: str, anion_key: str) -> str:
    from chemistry.reactions import compound_formula  # избегаем цикла импорта

    return compound_formula(ION[cation_key], ION[anion_key])


def _color(cation_key: str) -> tuple[int, int, int, int]:
    return _CATION_COLOR.get(cation_key, _COLORLESS)


def _build() -> list[Substance]:
    out: list[Substance] = []

    # Кислоты: H⁺ + кислотный остаток.
    for an in _ACID_ANIONS:
        f = _formula("H", an)
        out.append(Substance(f, f, "H", an, ACID))

    # Щёлочи: растворимые гидроксиды.
    for cat in _ALKALI_CATIONS:
        f = _formula(cat, "OH")
        out.append(Substance(f, f, cat, "OH", ALKALI))

    # Соли: растворимые комбинации металл/NH4 + кислотный остаток (без OH).
    for cat in SALT_CATIONS:
        for an in ANIONS:
            if an == "OH":
                continue
            if solubility(cat, an) != "Р":
                continue
            f = _formula(cat, an)
            out.append(Substance(f, f, cat, an, SALT, color=_color(cat)))

    return out


_SUBSTANCES = _build()
SUBSTANCES: list[Substance] = _SUBSTANCES
_BY_ID = {s.id: s for s in _SUBSTANCES}


def by_id(sid: str) -> Substance:
    return _BY_ID[sid]
