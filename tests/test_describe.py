"""Описание результата реакции для нижней панели итога."""

from chemistry import SUBSTANCES, describe_result, precipitate_color, react
from chemistry.describe import _COLOR_RGB, _PRECIP


def _first(pred):
    for a in SUBSTANCES:
        for b in SUBSTANCES:
            r = react(a, b)
            if r is not None and pred(r):
                return r
    raise AssertionError("подходящая реакция не найдена")


def _n_visible(r):
    return sum(1 for p in r.products
               if p.state in ("gas", "precipitate", "water"))


def test_water_phrase():
    r = _first(lambda r: r.effect == "WATER" and _n_visible(r) == 1)
    assert describe_result(r) == "Образовалась вода."


def test_gas_has_color_and_smell():
    text = describe_result(_first(lambda r: r.effect == "GAS"))
    assert text.startswith("Выделился ")
    assert "газ" in text and "запах" in text


def test_precipitate_has_color_and_texture():
    r = _first(lambda r: r.effect == "PRECIPITATE" and _n_visible(r) == 1)
    text = describe_result(r)
    assert text.startswith("Образовался ") and text.endswith("осадок.")


def test_two_precipitates_are_both_described():
    """Осадок + осадок: оба описаны через « и » под общим глаголом."""
    r = _first(lambda r: sum(p.state == "precipitate" for p in r.products) == 2)
    text = describe_result(r)
    assert text.startswith("Образовался ")
    assert " и " in text and text.count("осадок") == 2


def test_precipitate_plus_water_both_described():
    """Осадок + вода описываются оба (напр. H2SO4 + Ba(OH)2)."""
    r = _first(lambda r: any(p.state == "precipitate" for p in r.products)
               and any(p.state == "water" for p in r.products))
    text = describe_result(r)
    assert "осадок" in text and "вода" in text


def test_precipitate_color_is_known_and_bright():
    r = _first(lambda r: r.effect == "PRECIPITATE")
    col = precipitate_color(r)
    assert len(col) == 4 and all(0 <= c <= 255 for c in col)
    assert col[:3] in _COLOR_RGB.values()


def test_plan_has_at_least_two_colored_precipitates():
    """Каждая партия из 5 раундов содержит ≥2 раунда с цветным осадком."""
    import random

    from chemistry import precipitate_is_colored
    from game import config
    from game.scene import SceneLogic

    for seed in range(20):
        L = SceneLogic(random.Random(seed))
        colored = sum(
            1 for rnd in L._plan
            if rnd.effect == "PRECIPITATE" and precipitate_is_colored(rnd.result)
        )
        assert len(L._plan) == config.ROUNDS_TOTAL
        assert colored >= 2, f"seed={seed}: только {colored} цветных"


def test_plan_has_at_least_one_gas():
    """Каждая партия из 5 раундов содержит ≥1 раунд с выделением газа."""
    import random

    from game.scene import SceneLogic

    for seed in range(20):
        L = SceneLogic(random.Random(seed))
        gas = sum(1 for rnd in L._plan if rnd.effect == "GAS")
        assert gas >= 1, f"seed={seed}: газовых раундов нет"


def test_every_reaction_is_describable_without_fallback():
    """У всех достижимых осадков есть явная запись цвета и консистенции."""
    for a in SUBSTANCES:
        for b in SUBSTANCES:
            r = react(a, b)
            if r is None:
                continue
            assert describe_result(r)  # не падает, непустая строка
            if r.effect == "PRECIPITATE":
                p = next(p for p in r.products
                         if p.state == "precipitate" and p.formula == r.star_formula)
                assert (p.cation.key, p.anion.key) in _PRECIP
