"""Логика сокращения ионов-зрителей (уровень 2, механика №6) — без pygame.

На вход — пара реагентов. Строится полное ионное уравнение, разложенное на
кликабельные «плитки» (каждый ион-терм и каждая молекула — отдельная плитка).
Игрок кликает ионы-зрители (одинаковые слева и справа) — они зачёркиваются.
Клик по иону-участнику или молекуле — ошибка (плитка не зачёркивается).

Когда все зрители зачёркнуты, можно «раскрыть» сокращённое ионное уравнение,
которое вычисляется доменным `net_ionic`.
"""

from __future__ import annotations

from dataclasses import dataclass

from chemistry import react
from chemistry.ionic import NetIonic, full_ionic, net_ionic
from chemistry.substances import Substance


@dataclass
class Tile:
    tid: str
    side: str            # 'L' / 'R'
    text: str            # отображаемая запись (напр. '2Na⁺', 'BaSO₄↓')
    is_ion: bool
    ion_key: str | None
    is_spectator: bool
    struck: bool = False


class CancelGame:
    """Зачёркивание ионов-зрителей в полном ионном уравнении."""

    def __init__(self, a: Substance, b: Substance):
        self.a, self.b = a, b
        full = full_ionic(a, b)
        if full is None:
            raise ValueError(f"{a.id} и {b.id} не реагируют")
        self.full = full
        self.result = react(a, b)        # для показа молекулярного уравнения
        self.net: NetIonic = net_ionic(full)
        self.left = self._tiles(full.left, "L")
        self.right = self._tiles(full.right, "R")
        self.revealed = False

    def _tiles(self, species, side: str) -> list[Tile]:
        tiles: list[Tile] = []
        i = 0
        for s in species:
            if s.as_ions:
                for t in s.ions:
                    spec = t.ion.key in self.net.spectators
                    tiles.append(Tile(f"{side}{i}", side, t.display, True,
                                      t.ion.key, spec))
                    i += 1
            else:
                tiles.append(Tile(f"{side}{i}", side, s.text, False, None, False))
                i += 1
        return tiles

    @property
    def tiles(self) -> list[Tile]:
        return self.left + self.right

    def tile(self, tid: str) -> Tile:
        return next(t for t in self.tiles if t.tid == tid)

    def click(self, tid: str) -> bool:
        """Клик по плитке. True — зачёркнут зритель; False — ошибка/участник."""
        t = self.tile(tid)
        if t.is_spectator and not t.struck:
            t.struck = True
            return True
        return False

    @property
    def all_spectators_struck(self) -> bool:
        specs = [t for t in self.tiles if t.is_spectator]
        return bool(specs) and all(t.struck for t in specs)

    def reveal(self) -> bool:
        """Раскрыть сокращённое уравнение, если все зрители зачёркнуты."""
        if self.all_spectators_struck:
            self.revealed = True
        return self.revealed
