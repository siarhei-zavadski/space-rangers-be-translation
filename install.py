#!/usr/bin/env python3
"""Install BelTranslate into a Space Rangers HD game folder (player entry point)."""

import argparse
from pathlib import Path

from build_test_mod import build, uninstall
from corpus_data import DEFAULT_GAME, configure_game


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game",
        type=Path,
        help=f"game install folder (default: {DEFAULT_GAME})",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="restore patched game CFG files and remove Mods/Tweaks/BelTranslate",
    )
    args = parser.parse_args()
    game = configure_game(args.game)
    if args.uninstall:
        uninstall(game)
        return
    # Zip installs have no git tag history; still check ids/tags against the game.
    build(game, compare_tag=False)


if __name__ == "__main__":
    main()
