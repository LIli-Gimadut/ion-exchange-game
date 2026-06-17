"""Общая настройка тестов: headless-pygame (без окна)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402


def pytest_configure(config):
    # pygame.Rect и логика сцены не требуют окна, но init() безопасен и нужен
    # для тестов, затрагивающих шрифты/поверхности.
    if not pygame.get_init():
        pygame.init()
