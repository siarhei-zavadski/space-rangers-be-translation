# Tools install plan — Linux (Ubuntu 22.04)

For Space Rangers HD Belarusian (`be-tarask`) translation workflow.

## Correct order

| # | Tool | Why this order | Status (2026-09-13) |
|---|------|----------------|---------------------|
| 0 | Backup vanilla `Lang.dat` | Safe before any edits | **DONE** → `backup/Lang.{Rus,Eng}.vanilla.dat` |
| 1 | **Wine** (`wine64` + `wine32`) | Needed later for Windows-only GUIs (SRResEditor, TGE, optional BlockParEditor) | **DONE** — `wine-6.0.3` |
| 2 | **ranger-tools** (Python, Linux-native) | Opens current HD `Lang.dat`; export/edit/repack without Windows GUI | **DONE** — venv + verified export |
| 3 | **spell-be-tarask** | Classical orthography QA | **DONE** — v0.65 `be_BY@tarask` |
| 4 | Smoke-export `Lang.dat` → txt | Prove text pipeline | **DONE** — `tools/Lang.Rus.export.txt` (~3.8 MB, 16k+ Cyrillic lines) |
| 5 | **BlockParEditor** under Wine | Optional GUI fallback; official editor | **BLOCKED** — mirrors down / need manual download |
| 6 | **SRResEditor** | `.pkg` UI art | **DEFERRED** (Phase 3) |
| 7 | **TGE** | Text quests | **DEFERRED** (Phase 3) |

**Primary Lang.dat path on Linux = ranger-tools, not BlockParEditor.**

---

## Verified installs

### Wine
```
wine-6.0.3 (Ubuntu 6.0.3~repack-1)
packages: wine, wine32:i386, wine64, winetricks
```

### ranger-tools (denballakh fork — works on this game build)
```
Project venv:  .venv/
Install:       .venv/bin/pip install -r requirements-local.txt
Export sample: tools/Lang.Rus.export.txt
Detected fmt:  HDMain
```

The dependency is pinned to an upstream revision and is not vendored into the
future repository.

Roundtrip note: `dat → txt → dat` reloads cleanly; leaf count matches (27364). One long string (`Warning.WeRunOnWine`) truncates on txt round-trip — avoid editing that key until fixed, or patch via dict/json API.

Usage:
```bash
cd ~/Projects/space-rangers-be-translation
.venv/bin/python - <<'PY'
from pathlib import Path
from rangers.dat import DAT
src = Path("/home/siarhei/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart/CFG/Rus/Lang.dat")
dat = DAT.from_dat(src)
dat.to_txt(Path("tools/Lang.Rus.export.txt"))
# after edits:
# dat = DAT.from_txt(Path("tools/Lang.Rus.export.txt"))
# dat.to_dat(Path("Mods/.../Lang.dat"), fmt="HDMain")
PY
```

### spell-be-tarask v0.65
```
/usr/share/hunspell/be_BY@tarask.{aff,dic}
deb kept at: tools/hunspell-be-tarask-alt_0.65_all.deb
LibreOffice oxt: tools/dict-be-tarask-0.65.oxt
```
Check: `echo мова | hunspell -d be_BY@tarask -a` → `*`

School `hunspell-be` remains installed alongside (alt package).

---

## Still blocked / manual

### BlockParEditor
Tried and failed:
- `snk-games.net` → Cloudflare **521** (origin down)
- Playground file id `284549` → download API needs login / not public CDN
- Old Dropbox shared folder → no machine-parseable file list

When available, put zip under `tools/BlockParEditor/` and run:
```bash
export WINEPREFIX="$HOME/.wine-sr-tools"
wineboot -u
wine tools/BlockParEditor/*.exe
```

Manual sources to try in browser:
1. https://www.playground.ru/space_rangers_2_dominators/file/space_rangers_hd_a_war_apart_redaktor_dat_fajlov-1622253  
2. https://www.dropbox.com/sh/3kdy45sgdzn9w50/AAC7SGfgB2DxMTLxbk-XZfiba?dl=0  
3. Discord `discord.gg/WZfx4K` modding channel  

### Deferred Windows tools
- SRResEditor toolset: https://www.dropbox.com/sh/spxo4l8ado7v1gj/AAC_b7dsWyazRLEbKbhPfaCNa?dl=0  
- TGE: snk-games / playground Windows builds  

---

## Paths

| What | Path |
|------|------|
| Game | `~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart` |
| Project | `~/Projects/space-rangers-be-translation/` |
| Tools | `…/tools/` |
| Backup | `…/backup/` |
| Python | `…/.venv/bin/python` |

---

## Current proven flow

Use the Linux-native build:

```bash
cd ~/Projects/space-rangers-be-translation
.venv/bin/python build_test_mod.py
```

This creates patched Eng/Rus DAT files, Belarusian GI menu assets, `belarusian.pkg`, manifests, and UTF-16 module metadata. The user confirmed the resulting mod works in-game.

See `AGENTS.md` for the authoritative build, format, and test instructions. BlockParEditor remains optional.
