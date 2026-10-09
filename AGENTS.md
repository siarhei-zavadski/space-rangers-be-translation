# Agent guide: Space Rangers HD Belarusian translation

This project builds a Belarusian localization mod for **Space Rangers HD: A War Apart**. The current test flow was confirmed working in-game on game build `2.1.2500` under Steam Proton.

## Read first

Authoritative project files:

- `build_test_mod.py` — proven DAT/GI/PKG build and structural checks.
- `corpus/{lang_dat,quests,robots,assets}/*.json` — the Belarusian translation
  (one identifier-to-text object per file) and build input. The repository is
  the source of truth. Russian and English are read from the game.
- `corpus_data.py` — check the corpus against the game and the Russian at the
  `v1-first-pass` tag; feed it to the build.
- `TERMBASE.tsv` — canonical terminology. Reuse exact terms.
- `STYLE.md` — language, classical Belarusian (`be-tarask`) spelling, and presentation rules.
- `TRANSLATION.md` — per-line procedure and quest puzzles that break if rewritten.
- `puzzles.tsv` — frozen puzzle tokens; `validate_corpus.py` checks they stay present.
- `review.tsv` — recheck cursor (`file` → last reviewed id); bump with `qa_translation.py --review … --mark`.
- `FONT.md` — menu-image font and license.

Do not infer the current workflow from old forum guides. Use the build script and this file.

## Environment

Default game path (override with `--game`):

```text
~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart
```

Python environment:

```text
.venv/bin/python
```

The venv contains Pillow and `ranger-tools` from the pin in `requirements-local.txt` (`denballakh/ranger-tools`). That library reads and writes the current `HDMain` DAT format and handles PKG/GI files natively on Linux. Do not vendor a copy under `tools/`.

BlockParEditor, SRResEditor, and TGE are not required for the current UI flow. They remain optional Windows/Wine tools for later work.

## Build

Run from project root (game closed):

```bash
.venv/bin/python corpus_data.py check
.venv/bin/python build_test_mod.py
# optional: .venv/bin/python build_test_mod.py --game /path/to/Space\ Rangers\ HD\ A\ War\ Apart
```

To restore patched install files (`CFG/*/robots.dat` from `*.vanilla`, optional old `forms.pkg.vanilla`) and remove the mod folder:

```bash
.venv/bin/python build_test_mod.py --uninstall
# same: .venv/bin/python install.py --uninstall
```

Player zip (no game files): `python3 pack_release.py` → `dist/beltranslate-patcher-*.zip`.
CI workflow `Release patcher` builds that zip on `workflow_dispatch` and attaches it when a GitHub Release is published. Player steps are in `INSTALL.md`.

The build:

1. Opens vanilla `CFG/Eng/Lang.dat` and `CFG/Rus/Lang.dat`.
2. Reads completed Belarusian rows from the corpus and patches
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

Patched AFT fonts go in a second package rooted at vanilla `DATA/FONT`. One archive cannot hold both `Data/` and `DATA/` — the engine keys folders by the uppercase name and the main-menu buttons vanish. The engine reads that mod package (confirmed on game build `2.1.2500`, Proton Experimental `11.0-100`); the build does not patch the game's own `forms.pkg`.

Both install manifests must mount them. Fonts PKG uses same-size AFT files (unused Latin slots retargeted to `і`/`ў`/`’`; `ў` gets a painted breve); do not append glyphs.

`robots.dat`: MatrixGame opens the install's `CFG/Eng/robots.dat` and `CFG/Rus/robots.dat` on disk; a mod-folder copy is ignored (unlike `Lang.dat`). The build patches those game files from `*.vanilla` backups and also writes the mod copies (`CFG/robots.dat` plus `CFG/{Eng,Rus}/`). Steam verify restores vanilla.

```text
Packages {
    Package=Mods\Tweaks\BelTranslate\data\belarusian.pkg
    Package=Mods\Tweaks\BelTranslate\data\belarusian_fonts.pkg
}
```

`ModuleInfo.txt` must be UTF-16 little-endian with BOM and CRLF. `write_utf16` opens with `newline=""` so Windows does not turn `\r\n` into `\r\r\n`. Display the mod as **Belarusian**, not “Belarusian Classical”. `German` and `Spanish` are conflicts.

## Language rules

- Internal orthography: Belarusian classical spelling (`be-tarask`, 2005 normalization).
- User-facing mod name: **Belarusian**.
- Translate meaning from Russian, cross-check English, and avoid Russian calques where a clear Belarusian term exists.
- Before locking a lemma: **Starnik** (`starnik.by`) first for the lemma, sense, and endings. Skarnik only if RU→BE is still unclear. Then `hunspell -d be_BY@tarask`. Spelling clashes: hunspell wins; meaning clashes: Starnik wins. See `STYLE.md`.
- Add every accepted term to `TERMBASE.tsv` with sense, endings, rejected calque, and the Starnik URL.
- Check prose with:

```bash
.venv/bin/python validate_corpus.py
PYTHONPATH=. .venv/bin/python corpus_data.py check
PYTHONPATH=. .venv/bin/python spell_check.py
PYTHONPATH=. .venv/bin/python spell_check.py --file Ski.qmm --gate
python3 qa_translation.py --fix && .venv/bin/python qa_translation.py
```

- Do not translate placeholders, identifiers, markup, or shortcut keys.

## Font

Menu images use `tools/fonts/RussoOne-Regular.ttf`:

- readable square display style close to the game UI;
- includes Belarusian `І/і`, `Ў/ў`, and optional `Ґ/ґ`;
- licensed under SIL OFL 1.1;
- rasterized into GI images, not embedded in the package.

Runtime `Lang.dat` is UTF-16. Vanilla AFT has `'`, `i`, `у`, but not `і`/`ў`/`’`. The DAT writer folds typographic apostrophes to `'`. The mod's `belarusian_fonts.pkg` supplies a same-size remap (`і`←`i`, `ў` = `у` plus a painted breve). Do not append glyphs or bump sizes. A partial mod `Lang.dat` (translated keys only) merges with the vanilla file; menus stay Belarusian and excluded fields (maps, hull art, etc.) still appear.

## Before claiming completion

1. Run `build_test_mod.py` without errors.
2. Confirm generated DAT values by reopening both files.
3. Unpack `belarusian.pkg`; verify expected paths.
4. Decode every generated GI; verify `316×45`.
5. Run tarask Hunspell on new translations.
6. Enable the mod and verify the relevant screen in-game.
7. Record accepted translations in `TERMBASE.tsv` (sense + endings + rejected + source).

## Cursor Cloud specific instructions

Cloud Agents do not have the Steam game install. `build_test_mod.py` and `corpus_data.py check` need `~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart` and cannot run here. Do not commit game binaries.

Without the game, prove the toolchain with:

```bash
python3 -m py_compile ./*.py
python3 validate_corpus.py
printf 'мова\n' | hunspell -d be_BY@tarask -a
.venv/bin/python spell_check.py
```

`validate_corpus.py` is the CI check and uses only the stdlib. Spell-check and DAT/GI work need `.venv` (`requirements-local.txt` pulls Pillow in with ranger-tools) and `hunspell -d be_BY@tarask` from the `hunspell-be-tarask-alt` 0.65 package. A signed `HDMain` DAT round trip through `rangers.dat.DAT` does not need the game files.
