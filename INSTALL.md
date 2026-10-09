# Install BelTranslate (players)

Unofficial Belarusian translation for **Space Rangers HD: A War Apart**.
You need a legitimate game install. This zip has no game files — only the
Belarusian text, MIT scripts, and the OFL Russo One font. See `THIRD_PARTY.md`.

## Requirements

- Python 3.10+
- An installed copy of the game (Steam is fine; Proton on Linux works)
- Close the game before install or uninstall

## One-time setup

```bash
unzip beltranslate-patcher-*.zip
cd beltranslate
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
```

`requirements-local.txt` installs
[ranger-tools](https://github.com/denballakh/ranger-tools) from GitHub (not
bundled here) and Pillow.

## Install

Linux Steam default path is used if you omit `--game`:

```bash
.venv/bin/python install.py
# Windows / custom path:
.venv/bin/python install.py --game "C:\Program Files (x86)\Steam\steamapps\common\Space Rangers HD A War Apart"
```

Then enable **Belarusian** on the in-game Mods screen (or set
`Mods/ModCFG.txt` to `CurrentMod=Tweaks\BelTranslate` while the game is
closed). Fully restart the game.

Steam verify may clear `ModCFG.txt`; enable the mod again afterwards.

## What the installer writes

- `Mods/Tweaks/BelTranslate/` — packages, manifests, patched `Lang.dat`
- `CFG/Eng/robots.dat` and `CFG/Rus/robots.dat` — MatrixGame reads these from
  the install, not from the mod folder. Vanilla copies are saved next to them
  as `*.vanilla` on first install.

## Uninstall

```bash
.venv/bin/python install.py --uninstall
```

That restores `CFG/*/robots.dat` from `*.vanilla` and deletes
`Mods/Tweaks/BelTranslate/`. Disable the mod in-game (or clear `ModCFG.txt`)
if it is still selected.
