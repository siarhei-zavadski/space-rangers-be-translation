# Agent guide: Space Rangers HD Belarusian translation

This project builds a Belarusian localization mod for **Space Rangers HD: A War Apart**. The current test flow was confirmed working in-game on game build `2.1.2500` under Steam Proton.

## Read first

Authoritative project files:

- `build_test_mod.py` — proven DAT/GI/PKG build and structural checks.
- `crowdin/{lang_dat,quests,robots,assets}/*.tsv` — game-structured Crowdin
  source and build input.
- `crowdin/coverage.json` — exhaustive translatable/excluded source manifest.
- `crowdin_sync.py` / `CROWDIN.md` — regenerate, validate, and sync the corpus.
- `TERMBASE.tsv` — canonical terminology. Reuse exact terms.
- `STYLE.md` — language and presentation rules.
- `ORTHO.md` — classical Belarusian (`be-tarask`) spelling policy.
- `TRANSLATION.md` — per-line procedure and quest puzzles that break if rewritten.
- `FONT.md` — menu-image font and license.
- `PLAN.md` — wider project scope.

Do not infer the current workflow from old forum guides. Use the build script and this file.

## Environment

Expected game path:

```text
~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart
```

Python environment:

```text
.venv/bin/python
```

The venv contains Pillow and the vendored `denballakh/ranger-tools` package from `tools/ranger-tools/`. This library reads and writes the current `HDMain` DAT format and handles PKG/GI files natively on Linux.

BlockParEditor, SRResEditor, and TGE are not required for the current UI flow. They remain optional Windows/Wine tools for later work.

## Build

Run from project root:

```bash
.venv/bin/python crowdin_sync.py check
.venv/bin/python build_test_mod.py
```

The build:

1. Opens vanilla `CFG/Eng/Lang.dat` and `CFG/Rus/Lang.dat`.
2. Reads completed Belarusian rows from the split Crowdin corpus and patches
   both language files, translated quests, planetary-battle strings, and GI
   labels.
3. Reads Russian main-menu `.gi` assets from `DATA/russian.pkg`.
4. Removes baked Russian labels and renders Belarusian labels with Russo One.
5. Creates all normal/active/disabled (`N/A/D`) GI states.
6. Packs them into `DATA/belarusian.pkg`.
7. Writes `INSTALL_ENGLISH.TXT`, `INSTALL_RUSSIAN.TXT`, and UTF-16 `ModuleInfo.txt`.
8. Reopens generated DAT, PKG, and GI files and asserts expected values/dimensions.

Output is written directly to:

```text
<game>/Mods/Tweaks/BelTranslate/
```

Preview PNGs are regenerated under `build/preview/`.

## Enable and test

The build does not enable the mod. Use either the in-game Mods screen or, while the game is closed:

```bash
printf 'CurrentMod=Tweaks\\BelTranslate\r\n' \
  > "$HOME/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart/Mods/ModCFG.txt"
```

Fully restart the game after enabling.

Expected main-menu images (`FormMain2` + `FormMain3` Ach):

- `НОВАЯ ГУЛЬНЯ` / `ЗАГРУЗІЦЬ` / `ВЫЙСЬЦІ`
- `НАЛАДЫ` / `РЭКОРДЫ` / `ПРА АЎТАРАЎ`
- `ДАСЯГНЕНЬНІ`

Start/load a game and press `Esc`. Expected live DAT text includes:

- `Працягнуць` / `Захаваць` / `Загрузіць`
- `Налады` / `Даведка` / `Выхад`
- Save dialog: `Захаваць гульню`, `З А Г Р У З К А`, etc.

The user confirmed this combined DAT + PKG flow works.

## Important format facts

### Main-menu labels are images

`FormMain.New`, `FormMain.Load`, and `FormMain.Exit` exist in `Lang.dat`, but the visible main-menu buttons are baked images:

```text
Data/FormMain2/2But{New,Load,Exit,Settings,Records,About}{N,A,D}.gi
Data/FormMain3/2ButAch{N,A,D}.gi
```

Changing only `Lang.dat` will not change those visible buttons. A language package and install manifests are required.

### DAT

- Patch both `CFG/Eng/Lang.dat` and `CFG/Rus/Lang.dat`.
- Preserve control tags such as `<br>`, `<Value>`, `<clr>`, and placeholders.
- Write with `fmt="HDMain"` and `sign=True`.
- Prefer `DAT.to_dict()` / `DAT.from_dict()` for edits.
- Avoid full DAT-to-TXT round trips: one verified round trip truncated `Warning.WeRunOnWine` at `https://`.

### GI

- Current button assets are `316×45`, frame type `2`, three layers, 16-bit.
- Generate all three states: `N`, `A`, and `D`.
- Keep the exact resource paths and names.
- Review `build/preview/*.png` before testing.

### PKG and manifests

The button package must contain paths rooted at `Data/` only (never a sibling `DATA/`):

```text
Data/FormMain2/2ButNewN.gi
```

Patched AFT fonts go in a second package rooted at vanilla `DATA/FONT`. One archive cannot hold both `Data/` and `DATA/` — the engine keys folders by the uppercase name and the main-menu buttons vanish.

Both install manifests must mount them. Fonts PKG uses same-size AFT files (unused Latin slots retargeted to `і`/`ў`/`’`; `ў` gets a painted breve); do not append glyphs.

```text
Packages {
    Package=Mods\Tweaks\BelTranslate\data\belarusian.pkg
    Package=Mods\Tweaks\BelTranslate\data\belarusian_fonts.pkg
}
```

`ModuleInfo.txt` must be UTF-16 little-endian with BOM and CRLF. Display the mod as **Belarusian**, not “Belarusian Classical”. `German` and `Spanish` are conflicts.

## Language rules

- Internal orthography: Belarusian classical spelling (`be-tarask`, 2005 normalization).
- User-facing mod name: **Belarusian**.
- Translate meaning from Russian, cross-check English, and avoid Russian calques where a clear Belarusian term exists.
- Before locking a lemma: **Starnik** (`starnik.by`) first for the lemma, sense, and endings. Skarnik only if RU→BE is still unclear. Then `hunspell -d be_BY@tarask`. Spelling clashes: hunspell wins; meaning clashes: Starnik wins. See `STYLE.md`.
- Add every accepted term to `TERMBASE.tsv` with sense, endings, rejected calque, and the Starnik URL.
- Check prose with:

```bash
.venv/bin/python validate_corpus.py
PYTHONPATH=. .venv/bin/python crowdin_sync.py check
PYTHONPATH=. .venv/bin/python spell_check.py
PYTHONPATH=. .venv/bin/python spell_check.py --file Ski.qmm
```

- Do not translate placeholders, identifiers, markup, or shortcut keys.

## Font

Menu images use `tools/fonts/RussoOne-Regular.ttf`:

- readable square display style close to the game UI;
- includes Belarusian `І/і`, `Ў/ў`, and optional `Ґ/ґ`;
- licensed under SIL OFL 1.1;
- rasterized into GI images, not embedded in the package.

Runtime `Lang.dat` is UTF-16. Vanilla AFT has `'`, `i`, `у`, but not `і`/`ў`/`’`. The DAT writer folds typographic apostrophes to `'`. A mod PKG of `DATA/FONT` is ignored (AFont/ResEditor workflow edits `forms.pkg`). The build writes a same-size remap into `DATA/forms.pkg` from `forms.pkg.vanilla`: `і`←`i`, `ў` = `у` plus a painted breve. Do not append glyphs or bump sizes. Steam verify restores vanilla.

## Before claiming completion

1. Run `build_test_mod.py` without errors.
2. Confirm generated DAT values by reopening both files.
3. Unpack `belarusian.pkg`; verify expected paths.
4. Decode every generated GI; verify `316×45`.
5. Run tarask Hunspell on new translations.
6. Enable the mod and verify the relevant screen in-game.
7. Record accepted translations in `TERMBASE.tsv` (sense + endings + rejected + source).

## Cursor Cloud specific instructions

Cloud Agents do not have the Steam game install. `build_test_mod.py` and `crowdin_sync.py check` need `~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart` and cannot run here. Do not commit game binaries.

Without the game, prove the toolchain with:

```bash
python3 -m py_compile ./*.py
python3 validate_corpus.py
printf 'мова\n' | hunspell -d be_BY@tarask -a
.venv/bin/python spell_check.py
```

`validate_corpus.py` is the CI check and uses only the stdlib. Spell-check and DAT/GI work need `.venv` (`requirements-local.txt` pulls Pillow in with ranger-tools) and `hunspell -d be_BY@tarask` from the `hunspell-be-tarask-alt` 0.65 package. A signed `HDMain` DAT round trip through `rangers.dat.DAT` does not need the game files.
