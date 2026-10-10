#!/usr/bin/env python3
"""Install BelTranslate into a Space Rangers HD game folder (player entry point)."""

import argparse
from pathlib import Path

MOD = "Tweaks\\BelTranslate"
CONFLICTS = {"tweaks\\german", "tweaks\\spanish"}


def require_game(game: Path) -> None:
    """Exit with a clear message if this is not a usable Space Rangers HD install."""
    from corpus_data import detect_langs

    try:
        detect_langs(game)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Game not found or incomplete at {game}\n"
            f"{exc}\n"
            "Pass --game with your Space Rangers HD: A War Apart install folder.\n"
            "The game's Steam language must be Russian (the mod shows Belarusian on top "
            "of it): set it in Steam > Properties > Language, verify game files, re-run."
        ) from exc


def set_mods(game: Path, change) -> None:
    """Rewrite the comma-separated CurrentMod= list in Mods/ModCFG.txt, keeping other mods."""
    cfg = game / "Mods/ModCFG.txt"
    # latin-1 round-trips any single-byte mod names unchanged.
    lines = cfg.read_text(encoding="latin-1").splitlines() if cfg.is_file() else []
    at = next((i for i, line in enumerate(lines) if line.startswith("CurrentMod=")), None)
    if at is None:
        lines.insert(0, "CurrentMod=")
        at = 0
    mods = [mod.strip() for mod in lines[at].removeprefix("CurrentMod=").split(",") if mod.strip()]
    lines[at] = "CurrentMod=" + ",".join(change(mods))
    cfg.parent.mkdir(parents=True, exist_ok=True)
    # newline="" so Windows does not turn \r\n into \r\r\n.
    cfg.write_text("".join(f"{line}\r\n" for line in lines), encoding="latin-1", newline="")
    print(f"{cfg}: {lines[at]}")


def enable_mod(game: Path) -> None:
    drop = CONFLICTS | {MOD.lower()}
    set_mods(game, lambda mods: [mod for mod in mods if mod.lower() not in drop] + [MOD])


def disable_mod(game: Path) -> None:
    if (game / "Mods/ModCFG.txt").is_file():
        set_mods(game, lambda mods: [mod for mod in mods if mod.lower() != MOD.lower()])


def main() -> None:
    from build_test_mod import build, uninstall
    from corpus_data import DEFAULT_GAME, configure_game

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
        disable_mod(game)
        return
    require_game(game)
    # Zip installs have no git tag history; still check ids and tags against the game.
    build(game, compare_tag=False)
    enable_mod(game)


if __name__ == "__main__":
    main()
