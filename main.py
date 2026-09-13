# /// script
# dependencies = ["pygame-ce"]
# ///

"""Точка входа.

Уровень 1 (по умолчанию) — «Реакции ионного обмена» (drag-and-drop пробирок).
Уровень 2 — «Разбор формулы на ионы» (`--level 2`).
Уровень 3 — «Сокращённое ионное уравнение» (`--level 3`).
"""

import argparse
import asyncio
import sys


async def main():
    parser = argparse.ArgumentParser(description="Реакции ионного обмена")
    parser.add_argument("--level", type=int, default=1, choices=(1, 2, 3),
                        help="1 — РИО (пробирки); 2 — разбор формулы на ионы; "
                             "3 — сокращение ионов-зрителей")
    # The browser runtime supplies its own command-line arguments.  The web
    # build starts the default game, while desktop users keep the level flag.
    args = parser.parse_args([] if sys.platform == "emscripten" else None)

    if args.level == 2:
        from game.level2 import run
    elif args.level == 3:
        from game.cancel_scene import run
    else:
        from game.scene import run
    await run()


if __name__ == "__main__":
    asyncio.run(main())
