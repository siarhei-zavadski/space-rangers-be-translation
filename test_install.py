"""Smallest check that install.py edits Mods/ModCFG.txt without dropping the player's other mods."""

from pathlib import Path
from tempfile import TemporaryDirectory

from install import disable_mod, enable_mod

with TemporaryDirectory() as temporary:
    game = Path(temporary)
    cfg = game / "Mods/ModCFG.txt"
    disable_mod(game)
    assert not cfg.exists(), "uninstall created ModCFG.txt"
    enable_mod(game)
    assert cfg.read_bytes() == b"CurrentMod=Tweaks\\BelTranslate\r\n", cfg.read_bytes()
    cfg.write_bytes(b"CurrentMod=Tweaks\\SR2LoadingScreen,Tweaks\\German\r\nOther=1\r\n")
    enable_mod(game)
    enable_mod(game)
    assert cfg.read_bytes() == (
        b"CurrentMod=Tweaks\\SR2LoadingScreen,Tweaks\\BelTranslate\r\nOther=1\r\n"
    ), cfg.read_bytes()
    disable_mod(game)
    assert cfg.read_bytes() == b"CurrentMod=Tweaks\\SR2LoadingScreen\r\nOther=1\r\n", cfg.read_bytes()
print("ok")
