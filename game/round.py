"""Генерация игрового раунда.

Раунд: одна основная пробирка + 3 варианта, из которых ровно один даёт РИО с
основной, а два других — гарантированно без реакции (все продукты растворимы).
Дополнительно (требование #1): каждый вариант не делит с основной ни катион, ни
анион — иначе обмен заведомо не даёт нового вещества. Чисто доменный модуль.

Граф реакций строится один раз (ленивая инициализация) на дешёвой проверке
`reacts()` — без затрат на балансировку уравнений.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from chemistry import Effect, ReactionResult, Substance, SUBSTANCES, react
from chemistry.reactions import is_clean_no_reaction, reacts

N_OPTIONS = 3


@dataclass(frozen=True)
class Round:
    main: Substance
    options: tuple[Substance, Substance, Substance]
    correct_index: int
    effect: Effect
    result: ReactionResult

    @property
    def correct(self) -> Substance:
        return self.options[self.correct_index]


def _ion_disjoint(main: Substance, s: Substance) -> bool:
    """Вариант не делит с основной ни катион, ни анион."""
    return s.cation_key != main.cation_key and s.anion_key != main.anion_key


# Граф: main.id -> инертные (ион-непересекающиеся) партнёры для дистракторов.
_INERT: dict[str, list[Substance]] | None = None
# Допустимые пары (main, correct) по типам эффекта — у main есть ≥2 дистрактора.
_TRIPLES: dict[Effect, list[tuple[Substance, Substance]]] | None = None


def _build_graph():
    global _INERT, _TRIPLES
    inert_map: dict[str, list[Substance]] = {}
    reacting_map: dict[str, list[tuple[Substance, Effect]]] = {}
    for main in SUBSTANCES:
        reacting, inert = [], []
        for s in SUBSTANCES:
            if not _ion_disjoint(main, s):
                continue
            eff = reacts(main, s)
            if eff is not None:
                reacting.append((s, eff))
            elif is_clean_no_reaction(main, s):
                inert.append(s)
        inert_map[main.id] = inert
        reacting_map[main.id] = reacting

    triples: dict[Effect, list[tuple[Substance, Substance]]] = {
        "GAS": [], "PRECIPITATE": [], "WATER": []
    }
    for main in SUBSTANCES:
        if len(inert_map[main.id]) < N_OPTIONS - 1:
            continue  # не хватит дистракторов
        for partner, eff in reacting_map[main.id]:
            triples[eff].append((main, partner))

    _INERT, _TRIPLES = inert_map, triples


def _ensure_graph():
    if _TRIPLES is None:
        _build_graph()


def generate(rng: random.Random | None = None,
             effect: Effect | None = None) -> Round:
    """Случайный валидный раунд.

    Тип эффекта выбирается равномерно (газ/осадок/вода) для разнообразия анимаций;
    можно задать явно через `effect`. Передайте seeded Random для детерминизма.
    """
    _ensure_graph()
    rng = rng or random.Random()
    assert _TRIPLES is not None and _INERT is not None

    if effect is None:
        available = [e for e, lst in _TRIPLES.items() if lst]
        effect = rng.choice(available)
    main, correct = rng.choice(_TRIPLES[effect])
    distractors = rng.sample(_INERT[main.id], N_OPTIONS - 1)

    options = [correct, *distractors]
    rng.shuffle(options)
    correct_index = options.index(correct)

    result = react(main, correct)
    assert result is not None
    return Round(
        main=main,
        options=tuple(options),  # type: ignore[arg-type]
        correct_index=correct_index,
        effect=result.effect,
        result=result,
    )
