# Install BelTranslate (players)

Unofficial Belarusian translation for **Space Rangers HD: A War Apart**.
You need a legitimate game install. This zip has no game files — only the
Belarusian text, MIT scripts, and the OFL Russo One font. See `THIRD_PARTY.md`.

## Requirements

- Python 3.10+ ([python.org](https://www.python.org/downloads/) on Windows; tick
  “Add python.exe to PATH”)
- An installed copy of the game (Steam is fine; Proton on Linux works) with the
  game's Steam language set to **Russian** (Steam → Properties → Language). The
  mod shows Belarusian on top of the Russian files; English-only installs are
  not supported yet. If `CFG/Eng` is also present it is patched too
- Close the game before install or uninstall

Git is **not** required. `requirements-local.txt` installs
[ranger-tools](https://github.com/denballakh/ranger-tools) from a GitHub zip
(not bundled here) and pulls in Pillow.

## Windows (PowerShell)

Extract the zip (Explorer, or `Expand-Archive`), then:

```powershell
cd beltranslate
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-local.txt
.\.venv\Scripts\python install.py
```

Or double-click `install.bat` (same steps; it waits for a key press at the end so
you can read the result). From a terminal you can pass `--uninstall` or
`--game "..."` to it.

Default Steam path is used if you omit `--game`:

`C:\Program Files (x86)\Steam\steamapps\common\Space Rangers HD A War Apart`

Custom library:

```powershell
.\.venv\Scripts\python install.py --game "D:\SteamLibrary\steamapps\common\Space Rangers HD A War Apart"
```

## Linux

```bash
unzip beltranslate-patcher-*.zip
cd beltranslate
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
.venv/bin/python install.py
```

Default Steam/Proton path if you omit `--game`:

`~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart`

## After install

`install.py` adds **Belarusian** to the enabled mods in `Mods/ModCFG.txt`. Fully
restart the game. Steam verify may clear `ModCFG.txt`; run install again (or
enable the mod on the in-game Mods screen) afterwards.

After switching the Steam language to Russian, verify game files once so
`CFG/Rus/` and `DATA/russian.pkg` / `DATA/questsRus.pkg` are present, then
re-run install.

## What the installer writes

- `Mods/Tweaks/BelTranslate/` — packages, manifests, patched `Lang.dat` for
  each installed language (`Rus`, plus `Eng` if present)
- `Mods/ModCFG.txt` — appends `Tweaks\BelTranslate` to `CurrentMod=`, keeps
  your other mods, and drops `Tweaks\German` / `Tweaks\Spanish` (they conflict)
- `CFG/<lang>/robots.dat` for each installed language — MatrixGame reads these
  from the install, not from the mod folder. Vanilla copies are saved next to
  them as `*.vanilla` on first install

## Uninstall

Windows:

```powershell
.\.venv\Scripts\python install.py --uninstall
```

Linux:

```bash
.venv/bin/python install.py --uninstall
```

That restores `CFG/*/robots.dat` from `*.vanilla`, deletes
`Mods/Tweaks/BelTranslate/`, and removes only `Tweaks\BelTranslate` from
`ModCFG.txt`.
