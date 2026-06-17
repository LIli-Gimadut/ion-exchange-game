"""Тесты генерации раундов (ион-непересекающиеся варианты, баланс эффектов)."""

import collections
import random

from chemistry import react
from chemistry.reactions import is_clean_no_reaction
from game.round import N_OPTIONS, _ion_disjoint, generate


def _check(r):
    assert len(r.options) == N_OPTIONS
    ids = [r.main.id] + [o.id for o in r.options]
    assert len(set(ids)) == len(ids), ids
    # ровно один реагирует
    reacts = [react(r.main, o) is not None for o in r.options]
    assert sum(reacts) == 1
    assert reacts[r.correct_index]
    # эффект совпадает
    assert react(r.main, r.correct).effect == r.effect
    # требование #1: ни общего катиона, ни общего аниона с основной
    for o in r.options:
        assert _ion_disjoint(r.main, o), (r.main.id, o.id)
    # дистракторы — гарантированно без реакции
    for i, o in enumerate(r.options):
        if i != r.correct_index:
            assert is_clean_no_reaction(r.main, o)
            assert react(r.main, o) is None


def test_fuzz_invariants():
    for seed in range(1000):
        _check(generate(random.Random(seed)))


def test_determinism():
    assert generate(random.Random(42)) == generate(random.Random(42))


def test_effects_are_varied():
    """За много раундов встречаются все три типа эффекта."""
    eff = collections.Counter(generate(random.Random(s)).effect
                              for s in range(300))
    assert set(eff) == {"GAS", "PRECIPITATE", "WATER"}
    # ни один тип не доминирует подавляюще (равномерный выбор эффекта)
    assert min(eff.values()) > 40


def test_forced_effect():
    for eff in ("GAS", "PRECIPITATE", "WATER"):
        r = generate(random.Random(7), effect=eff)
        assert r.effect == eff
        _check(r)
