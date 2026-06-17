"""Тесты логики сцены (headless): автомат, drop-зона, скоринг, 5 раундов."""

import random

import pytest

from game import animations, config
from game.scene import (
    DRAGGING, FINISHED, IDLE, POURING, RESULT, VERDICTS, WRONG, SceneLogic,
)


def _logic(seed=0):
    return SceneLogic(random.Random(seed))


def _answer(L, correct=True):
    """Один полный ответ: захват → сброс → переливание → результат."""
    idx = L.round.correct_index if correct else (L.round.correct_index + 1) % 3
    assert L.begin_drag(L.option_rects[idx].center)
    assert L.try_drop(L.main_rect.center) is True
    out = L.finish_pour()
    L.finish_result()
    return out


# --- хит-тест ---
def test_option_hit_test():
    L = _logic()
    for i, r in enumerate(L.option_rects):
        assert L.option_at(r.center) == i
    assert L.option_at((0, 0)) is None
    assert L.option_at(L.main_rect.center) is None


# --- конечный автомат одного раунда ---
def test_correct_flow_states():
    L = _logic()
    assert L.state == IDLE
    L.begin_drag(L.option_rects[L.round.correct_index].center)
    assert L.state == DRAGGING
    assert L.try_drop(L.main_rect.center) is True
    assert L.state == POURING
    assert L.finish_pour() == L.round.effect
    assert L.state == RESULT


def test_drop_outside_cancels():
    L = _logic()
    L.begin_drag(L.option_rects[0].center)
    assert L.try_drop((5, 5)) is False
    assert L.state == IDLE and L.dragging_index is None


def test_drop_zone():
    L = _logic()
    assert L.drop_zone.collidepoint(L.main_rect.center)
    assert L.drop_zone.contains(L.main_rect)


def test_begin_drag_only_from_idle():
    L = _logic()
    L.begin_drag(L.option_rects[0].center)
    assert L.begin_drag(L.option_rects[1].center) is False


# --- скоринг ---
def test_score_correct_and_wrong():
    L = _logic()
    _answer(L, correct=True)
    assert L.score == 1 and L.total == 1
    _answer(L, correct=False)
    assert L.score == 1 and L.total == 2


# --- 5 раундов и финал ---
def test_five_round_game_all_correct():
    L = _logic()
    for i in range(config.ROUNDS_TOTAL):
        assert L.state in (IDLE,)
        assert L.round_no == i + 1
        _answer(L, correct=True)
    assert L.state == FINISHED
    assert L.score == 5 and L.total == 5


def test_game_finishes_with_mixed_answers():
    L = _logic(1)
    pattern = [True, False, True, True, False]
    for c in pattern:
        _answer(L, correct=c)
    assert L.state == FINISHED
    assert L.score == sum(pattern)
    assert L.total == config.ROUNDS_TOTAL


def test_no_play_after_finished():
    L = _logic()
    for _ in range(config.ROUNDS_TOTAL):
        _answer(L, correct=True)
    assert L.state == FINISHED
    # в финале захват невозможен
    assert L.begin_drag(L.option_rects[0].center) is False


def test_restart():
    L = _logic()
    for _ in range(config.ROUNDS_TOTAL):
        _answer(L, correct=True)
    assert L.state == FINISHED
    L.restart()
    assert L.state == IDLE and L.score == 0 and L.total == 0
    assert L.round_no == 1


@pytest.mark.parametrize("score", list(range(6)))
def test_verdict_mapping(score):
    L = _logic()
    L.score = score
    assert L.verdict == VERDICTS[score]
    assert L.verdict  # непустой


# --- маппинг результата на анимацию ---
@pytest.mark.parametrize(
    "effect, cls",
    [
        ("GAS", animations.GasEffect),
        ("PRECIPITATE", animations.PrecipitateEffect),
        ("WATER", animations.WaterEffect),
    ],
)
def test_effect_mapping(effect, cls):
    eff = animations.make_effect(effect, "CO2", (0, 0, 255, 200))
    assert isinstance(eff, cls)
