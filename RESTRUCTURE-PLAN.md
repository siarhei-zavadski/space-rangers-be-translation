# Repository restructure plan

Status: phase 3's tests ran on 9 Oct 2026, and phase 0's checks passed on
PR #37's head (`162d0ba`). Next: merge PR #37 and tag it. Other numbers were
measured on `main` at `28aaae6`, before PR #37.

## 1. Goal and owner decisions

Goal: the public tree holds the Belarusian text, the tools, and the language
rules. The mod is built from that tree plus a locally installed game. Then
installing the mod gets simpler for players.

Decided by the owner:

1. Old git history keeps the Russian and English text. No history rewrite.
2. PR #37 (`cursor/adapt-copied-russian-8f02`) is merged before any
   restructuring starts.
3. Russian and English leave the tree, because the build does not need them
   (section 2.2). No private source repository, source pack, or CI secret.
4. The next step after the restructure is simpler installation (phase 5).
5. Every check that needs Russian or English, and the recheck itself, runs
   only on the owner's machine, which has the game installed. Those tools
   read Russian and English from the game files. Public CI and Cloud Agents
   see only Belarusian.
6. When a game update changes a Russian line, the owner updates the
   Belarusian line. New Russian text entering history then is fine.
7. No license request to ranger-tools' author. Keep using it as a dependency
   installed from GitHub; never copy it into this repository or a release.
   If that stops being possible, replace it (phase 5).

## 2. Target layout

### 2.1 Files and format

```text
corpus/lang_dat/<Section>.json   73 files
corpus/quests/<Quest>.qmm.json   80 files
corpus/robots/robots.json        931 strings
corpus/assets/<Form>.json        5 files, 17 labels
```

Each TSV becomes a JSON file at the same path. Each file is a flat object
keyed by today's full identifier, with one string per line in game order:

```json
{
"/quests/Ski.qmm/parameters/0/name": "Папулярнасьць",
"/quests/Ski.qmm/parameters/0/lines/0/content": "Курорт ненавідзяць"
}
```

I re-evaluated the format and kept JSON:

- The stdlib escapes the CRLF in 8,303 cells as `\r\n`. Every string is one
  physical line, so the line-ending trap ("Known LLM mistakes" #9) is gone.
- A two-column `id<TAB>be` TSV is only 2% smaller (18.75 MB against 19.13 MB),
  and it needs a homemade escape scheme. With csv quoting, the multi-line rows
  come back.
- Files are written only by `json.dumps(data, ensure_ascii=False, indent=0)`.
  They are read with an `object_pairs_hook` that rejects duplicate keys;
  plain `json.load` would silently keep only the last one.

A prototype shrank the tree from 56 MB to 19.13 MB, and the `id → be` maps
round-tripped identically.

### 2.2 The build needs only `identifier → be` and the game

`build_test_mod.py` gets its text through four functions:
`translations()`, `asset_translations()`, `write_translated_quests()`, and
`write_translated_robots()`. They read only `identifier` and `be`. Every
binary input comes from the game folder, and `ASSETS` is used only for its
renderer field. The build never reads `context` or `labels`. `source_phrase`
is read only in `check()`, which the build calls first, for the stale-source
checks and `validate_tags`.

Where the checks run afterwards:

| Check | Needs | Public CI | Owner's machine |
|---|---|---|---|
| JSON parses, no duplicate key, no empty `be`, identifier shape, tarask slips, termbase rows locked, puzzle tokens (phase 6) | Belarusian only | yes | yes |
| Tag parity, digits, `<format>` widths, rejected forms, reports | Russian from the game | no | yes |
| Ids match the game's classification (replaces `coverage.json`) | game | no | yes |
| Game Russian still equals the Russian at the tag (replaces the stale-source check) | game, tag (2.3) | no | yes |
| Spelling (`spell_check.py`, needs hunspell) | Belarusian only | no | yes |
| QMM and `robots.dat` round trips, build, in-game look | game | no | yes |

Two checks cannot move to CI by dropping their Russian half. Without the
Russian cell, the width check would flag 7 cells where the Russian line
already overflows, instead of 0 today. The rejected-form check would flag
3,584 rows instead of 398, because it could no longer require the Russian
term in the source. Both were measured on the current corpus.

Russian and English come from the game through the row builders that
`check()` already uses: `dat_rows`, `quest_rows`, and `robot_rows`. `--fix`
keeps the tarask slips but no longer copies translations into empty rows,
since none are empty.

### 2.3 A tag remembers which Russian was translated

Without Russian in the tree, nothing would notice a game update that rewords
a Russian line while keeping its id. The build would ship the old Belarusian.
Tag the merge commit of PR #37 as `v1-first-pass`. On the owner's machine,
`corpus_data.py check` reads that Russian with
`git show v1-first-pass:corpus/<dir>/<file>.tsv`, which took 0.7 s for all 159
files in a prototype. It then lists every id whose game Russian differs. The
owner updates those Belarusian lines and moves the tag to the new commit.
Only this check reads the tag; CI and the recheck do not.

### 2.4 `coverage.json` is deleted

`coverage.json` (12.3 MB, 79,579 entries of id, kind, status, and reason, with
no game text) has two jobs, and neither needs it anymore:

- In CI, it proves that the corpus ids equal its 61,571 `translatable`
  entries. After the change, a deleted or invented key shows up in the diff,
  and `check()` on the owner's machine fails on it.
- On the owner's machine, `check()` compares it with the game's string ids.
  That is redundant, because `check()` already recomputes the translatable
  ids from the game, so a string that an update adds or removes still fails.

The 18,008 excluded entries are documentation only.

## 3. Phases

Each phase is one PR. Phases 1, 2, and 4 must not change the built mod. The
build proof runs on the owner's machine after `build_test_mod.py`:

```bash
GAME="$HOME/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
MOD="$GAME/Mods/Tweaks/BelTranslate"
{ (cd build && find preview quests fonts -type f | sort | xargs -d '\n' sha256sum)
  (cd "$MOD" && sha256sum CFG/*/Lang.dat CFG/robots.dat INSTALL_*.TXT ModuleInfo.txt)
  sha256sum "$GAME/DATA/forms.pkg"; } > build-<phase>.sha256
```

Do not hash `belarusian.pkg`. `rangers` stamps each generated GI with
`[timestamp: <unix time>]` (confirmed by encoding one image twice). The
previews are the exact images the GIs are made from. The other packages are
hashed through their unpacked inputs, because `PKG.from_folder` packs in
`os.listdir` order.

### Phase 0: freeze (no PR)

- Merge PR #37.
- On the owner's machine, at the merge commit, `corpus_data.py check` must pass.
- Run `corpus_data.py refresh` once and compare every cell with the committed
  file, then run `git checkout -- corpus`. Only `labels` may differ: the
  committed quest rows say `Quest,<Name>`, and `quest_rows()` writes
  `quest,<Name>`, so `git diff --stat` lists all 80 quest files. Read the old
  file as bytes; text mode turns the cells' `\r\n` into `\n`. This proves the
  tag's Russian and English equal the game's, including the 44,138 quest rows
  that `check()` never compares.
- Build twice and save both hash lists; they must be identical, or the proof
  in later phases means nothing. Keep one as `build-0.sha256`, tag the commit
  `v1-first-pass`, and push the tag.

Done on 9 Oct 2026 at `162d0ba`, PR #37's head: `check` passed, `refresh`
changed only `labels`, and the two builds were identical. The hashes are in
`~/.cache/space-rangers-be-translation/build-0.sha256` on the owner's
machine. `main` is an ancestor of `162d0ba`, so a merge of the unchanged PR
has the same tree and these results hold for it. Left: merge PR #37, tag the
merge commit, push the tag.

### Phase 1: Belarusian-only tree (three commits)

1. Add one stdlib loader and saver to `validate_corpus.py`. The other scripts
   import them. The second `read_rows` and both TSV writers go; the writers
   disagreed on line endings. Russian and English for `qa_translation.py`
   come from `corpus_data`'s row builders, so the full QA run needs the game
   and `.venv`.
2. A one-off converter, not committed, writes `corpus/**/*.json`, deletes the
   TSVs and `coverage.json`, and asserts the `id → be` map equals the tag's.
3. Checks and deletions:
   - `validate_corpus.py` runs the first row of the table in 2.2.
     `qa_translation.py` and `corpus_data.py check` run the rest on the
     owner's machine.
   - From `corpus_data.py`, delete `refresh()`, `termbase_translations()`, the
     installed-mod `Lang.dat` harvest, the coverage code, `write_rows`, and
     `clean_generated`. The row builders stay for `check()`, and `ASSETS`
     keeps only the renderer.
   - Drop `qa_translation.py --batch`. It picks empty rows, so it prints
     nothing today.
   - Delete `audit_translation_scope.py` and `TRANSLATION-SCOPE.md`, which is
     stale (it says 44,625 translated).
   - `.gitattributes` treats `*.tsv` as normal text. CI keeps
     `py_compile`, the binary-file guard, `validate_corpus.py`,
     `test_qa_translation.py`, and actionlint. It drops the
     `qa_translation.py` run, which now needs the game. In the docs, update
     only lines that name a changed path or command.

Proof, on the owner's machine: the converter assertion, the same
`qa_translation.py` counts as before the change, and `build-1.sha256` equal
to `build-0.sha256`.

### Phase 2: speed and dead weight

- Index the rejected forms and Russian stems, and scan each row once instead
  of 553 regex passes. In my run that loop took about 82 s of the script's
  83 s. A prototype took 2.2 s and found the same 398 rows.
- Delete `--baseline`. It rewrites `qa_baseline.txt` from scratch, against the
  rule "never add rows".
- Delete the Crowdin leftovers: `.env.example` and the token regex.
- Delete the unused Jura font and `OFL-Jura.txt`. Also delete the
  `THIRD_PARTY.md` line, which names a nonexistent `Jura-Regular.ttf`.
- Give `CONTROL` one home, so `spell_check.py` stops needing `rangers`.

Proof: the same as in phase 1.

### Phase 3: three in-game tests, then the fonts and robots fixes

The tests ran on 9 Oct 2026 with the appendix steps: game build `2.1.2500`
(Steam build `20648864`), Proton Experimental `11.0-100`, Steam game language
English. The game then reads only the `Eng` files, so the `Rus` halves were
not exercised. Record the answers in `AGENTS.md` under "Important format
facts", and fix the font sections of `AGENTS.md` and `FONT.md`, which say a
mod font package is ignored.

1. **A mod font package is read.** `DATA/forms.pkg` was vanilla, and none of
   its 51 AFT fonts has `і` or `ў`. With `belarusian_fonts.pkg` mounted,
   `Гукі ў космасе:` in Settings and `Загрузіць (F3)` in the Esc menu
   rendered correctly.
   - Delete the in-place `forms.pkg` patch: `patch_game_forms()` and the
     assertion that ties it to the package. The build stops creating
     `forms.pkg.vanilla` but still reads fonts from one left by an old build,
     so they are not patched twice. A Steam verify restores vanilla
     `forms.pkg` on old installs.
   - Not yet checked: the one quest line with `’`, and Windows.
2. **The mod's `robots.dat` is not read.** The robot builder showed the
   vanilla English text. The game keeps `CFG/Eng/robots.dat` and
   `CFG/Rus/robots.dat` (the installed SR2LoadingScreen mod uses the same
   layout), but the build writes `CFG/robots.dat`. None of the 931 robot
   strings reach players.
   - Fix: write `CFG/Eng/robots.dat` and `CFG/Rus/robots.dat`, then repeat
     the test. The vanilla files differ (73,363 and 77,184 bytes), so compare
     their records before reusing the Russian-based output for English.
3. **A partial `Lang.dat` merges.** The appendix script dropped 10,482 of
   24,215 values, among them hull types, micromodules, robot maps, weapon
   data, and the planetary-battle maps. Menus and dialogs were Belarusian;
   the planet screen, galaxy map, ship screen, and item pictures were
   complete; nothing crashed.
   - CI can build the `Lang.dat` files from the JSON without game text.
     Repeat the test once with the game in Russian before relying on it for
     `CFG/Rus`.

Proof for the fixes: hashes are equal except `forms.pkg`, which stays
vanilla, and the robots files; then the robot builder shows Belarusian.

### Phase 4: one home per rule

- Fix stale text:
  - The puzzle table still calls `Doomino`, `Edelweiss`, and `Elus` "empty".
  - `AGENTS.md` says ranger-tools is vendored in `tools/ranger-tools/`, but it
    is pip-installed from the pin in `requirements-local.txt`.
- Rewrite "Known LLM mistakes" #9 for JSON.
- Merge `ORTHO.md` into `STYLE.md`. The Starnik rule lives only in `STYLE.md`
  and `starnik.mdc`; other files link to it.

### Phase 5: simpler installation (next step, outline)

Today `build_test_mod.py` runs on the owner's machine. It writes three packages
(buttons, fonts, quests) into `<game>/Mods/Tweaks/BelTranslate/`, along with
full patched `CFG/{Eng,Rus}/Lang.dat`, `CFG/robots.dat`, two manifests, and
`ModuleInfo.txt`. It also rewrites the game's own `forms.pkg`. The player
enables the mod on the Mods screen.

Four things block players:

- The Linux Steam path is hard-coded in three modules.
- The build needs Python 3.10+, Pillow, and ranger-tools.
- ranger-tools is not this project's code. It belongs to `denballakh`, who
  made 234 of its 260 commits; `volchonokilli` made the other 26. It has no
  license file, `setup.py` declares none, and the README names none. Without a
  license the author keeps all rights. A player can install it from GitHub
  the way `requirements-local.txt` does now, but the project cannot bundle it
  into a release or an executable. The project uses five of its modules:
  `rangers.dat`, `rangers.pkg`, `rangers.qm`, `rangers.std.buffer`, and
  `rangers.graphics.gi`.
- The `forms.pkg` patch survives disabling the mod, and nothing undoes it.
  Phase 3 deletes it.
- On Windows, `write_utf16` would write `\r\r\n` line ends (reproduced with
  `newline="\r\n"`).

The outputs are game files with Belarusian swapped in. The full `Lang.dat`
keeps 10,879 excluded values; a partial one (phase 3) drops them.
`robots.dat` keeps 7,129. The quests keep their logic, the buttons keep the
game's art, and the fonts are the game's bitmaps. `THIRD_PARTY.md` says the
game is not redistributed.

- **Option A, a prebuilt download.** The owner attaches the built mod to a
  release; the player unzips it and enables it. Ceiling: it redistributes the
  game content above, and every release needs the owner's machine.
- **Option B, a patcher the player runs.** CI zips the scripts, `corpus/`, and
  the Russo One font, with no game files. The player runs one command on their
  game folder, which builds the mod inside `Mods/Tweaks/BelTranslate/` only;
  uninstalling is deleting that folder. The player then enables the mod on the
  Mods screen, because writing `ModCFG.txt` would replace their mod choice.
  Only Belarusian text, MIT code, and an OFL font are distributed. ranger-tools
  is installed by the player from GitHub, not shipped. Ceiling: players need
  Python and one `pip install`. A Steam verify resets `Mods/ModCFG.txt` to
  `CurrentMod=`, so the player enables the mod again afterwards.

If reusing ranger-tools stops working, there are two fallbacks:

- **The repository disappears:** fork it on GitHub, which GitHub's terms allow
  for any public repository, and pin the same commit in the fork.
- **A single executable is wanted:** write the project's own readers and
  writers for the formats it touches:
  - signed `HDMain` DAT;
  - PKG;
  - QMM;
  - GI, for the 21 button images.

  `robots_storage.py` already does this for `robots.dat`. This is the only
  large piece of new code in the plan, so do it only if a single executable is
  truly wanted.

Recommendation: B. The first PRs are a game-path argument with the newline
fix, and a release workflow. The phase 3 answers settle the rest:

- A mod font package works, so the patcher writes only inside
  `Mods/Tweaks/BelTranslate/`.
- A partial `Lang.dat` merges, so CI can build both `Lang.dat` files from the
  JSON with no game text; the DAT writer needs no game file and is
  deterministic (measured).

Quests, `robots.dat`, and buttons always start from game files.

### Phase 6: the recheck (later; can run alongside phase 5)

- `qa_translation.py --review FILE -n 50` prints the next 50 unique Russian
  sources after the file's cursor. Each line shows the id, the row count, the
  Russian and English from the game, the current `be`, termbase hints, and
  the other translations. It runs on the owner's machine, which can also host
  a local Cursor agent; Cloud Agents have no game and cannot recheck meaning.
- `review.tsv` holds one row per file with the last reviewed id. It is bumped
  in each batch commit and deleted when the pass ends. It replaces the first
  pass's cursor, the empty `be` cell.
- `puzzles.tsv` (`file`, `token`) lists frozen tokens such as `Арес`,
  `16, 13, 18, 1, 17, 30`, `VIGENERE`, and `195449`, and CI checks they are
  still present. This is the first pass that edits filled puzzle lines.

Order, machine-found problems first:

1. The 168 sources translated more than one way (3,134 rows) and the 67 rows
   equal to the Russian, minus PR #37's fixes.
2. `qa_baseline.txt`: 37 of 435 rows no longer trigger and go now; fix the
   other 398.
3. `TERMBASE.tsv`: the 114 duplicated `ru` keys, and Starnik URLs for the 1,011
   rows sourced from a quest or TSV name. Also the 77 UI-string rows, which
   nothing reads once `refresh()` is gone.
4. UI sections, narrative sections, then quests, with puzzle files last. One
   batch per commit, one PR per file.

## 4. Risks

| Risk | Guard |
|---|---|
| Lossy conversion of multi-line or quoted cells | Converter assertion; build hashes |
| Broken JSON or a duplicated key from an edit | CI parses every file; the loader rejects duplicate keys |
| Tag missing on the owner's machine | `check()` stops and says to run `git fetch --tags` |
| A game update changes Russian strings | `check()` lists ids whose game Russian differs from the tag; the owner updates them and moves the tag |
| A Belarusian-only CI misses a broken `<tag>`, a digit, or a width | Those checks run on the owner's machine before every build and before merging a recheck PR |

## 5. Open questions for the owner

1. Is option A, a prebuilt download, acceptable even as a stopgap? The plan
   recommends against it.

## Appendix: clean test run on the owner's machine

Run these on the Linux PC with Steam, from the repository folder, with the
game closed. They remove every earlier build, restore vanilla game files, and
make a fresh build before the phase 3 tests.

```bash
GAME="$HOME/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
MOD="$GAME/Mods/Tweaks/BelTranslate"
```

### Step 1: see what is left from earlier work

```bash
ls "$GAME/Mods/Tweaks"
ls -l "$GAME/DATA" | grep -v '\.pkg$'
git status --ignored --short
```

The first command lists installed mods. The second shows anything that is not
a game package, such as `forms.pkg.vanilla` or an old backup. The third lists
local files that git ignores: `build/`, `.venv/`, and old tool downloads.

### Step 2: restore vanilla game files

In Steam, right-click the game in the Library, then **Properties → Installed
Files → Verify integrity of game files**. From a shell, the same is
`steam steam://validate/214730`.

Verification restores `DATA/forms.pkg` and any other edited game file. It
does not delete files Steam did not install, which is why step 3 exists. It
also resets `Mods/ModCFG.txt` to `CurrentMod=`, which disables every mod.

Check that it ran before step 3 deletes the backup:

```bash
cmp "$GAME/DATA/forms.pkg" "$GAME/DATA/forms.pkg.vanilla" && echo vanilla
```

On 9 Oct 2026 the first verify from the Library logged nothing in
`~/.local/share/Steam/logs/content_log.txt`, and `forms.pkg` stayed patched;
`steam steam://validate/214730` then worked.

### Step 3: delete the old files

```bash
rm -rf "$MOD"
rm -f "$GAME/DATA/forms.pkg.vanilla"
rm -rf build .venv
```

- `$MOD` is the old mod.
- The font backup may predate the verified file, so the next build makes a
  fresh one.
- `build/` holds the old previews, and `.venv/` is the old Python environment.

Delete anything else from step 1 by hand, keeping your save games. Old tool
folders (`tools/BlockParEditor/`, `tools/SRResEditor/`, `tools/TGE/`,
`tools/ranger-tools/`) are no longer used.

### Step 4: fresh build

```bash
git checkout main && git pull
python3 -m venv .venv && .venv/bin/pip install -r requirements-local.txt
.venv/bin/python corpus_data.py check
.venv/bin/python build_test_mod.py
ls -l "$MOD/DATA" "$MOD/CFG" "$MOD/CFG/Rus" "$MOD/CFG/Eng" "$GAME/DATA/forms.pkg.vanilla"
```

Every listed file must carry today's time. Then enable the mod on the in-game
Mods screen. Alternatively, with the game closed, run
`printf 'CurrentMod=Tweaks\\BelTranslate\r\n' > "$GAME/Mods/ModCFG.txt"`;
this replaces any other enabled mod. Start the game and check the main-menu
buttons listed in `AGENTS.md` (`НОВАЯ ГУЛЬНЯ`, `ЗАГРУЗІЦЬ`, …).

### Step 5: the three tests

The game reads only the files of its language (Steam: Properties → General →
Language), so each run tests either the `Eng` or the `Rus` files.

**Test 1: is the mod font package read?** With the game closed:

```bash
cp "$GAME/DATA/forms.pkg.vanilla" "$GAME/DATA/forms.pkg"
```

Start the game and check `Загрузіць (F3)` in the Esc menu and `Гукі ў космасе:`
in Settings. Vanilla fonts have no `і` or `ў`, so if those letters show, they
came from `belarusian_fonts.pkg`. Afterwards, run `build_test_mod.py` again to
put the patched `forms.pkg` back.

**Test 2: is the mod's `robots.dat` read?** With the normal build, start any
planetary battle: `Плянэтарныя баі` from the main menu, or one in a campaign.
Then open the robot builder. Belarusian (`канструктар робатаў`, `Пабудаваць`) means the file is
read; Russian means it is not.

**Test 3: does the engine merge a partial `Lang.dat`?** With the game closed:

```bash
cp "$MOD/CFG/Rus/Lang.dat" /tmp/Lang.Rus.dat
cp "$MOD/CFG/Eng/Lang.dat" /tmp/Lang.Eng.dat
PYTHONPATH=. .venv/bin/python - "$MOD/CFG/Rus/Lang.dat" "$MOD/CFG/Eng/Lang.dat" <<'EOF'
import sys
from pathlib import Path
from rangers.dat import DAT
from corpus_data import translations

def partial(full, paths):
    part = {}
    for path in paths:
        src, dst = full, part
        for key in path[:-1]:
            value = src.get(key)
            if isinstance(value, list):
                dst[key] = value
                break
            if not isinstance(value, dict):
                break
            src, dst = value, dst.setdefault(key, {})
        else:
            if path[-1] in src:
                dst[path[-1]] = src[path[-1]]
    return part

for name in sys.argv[1:]:
    file = Path(name)
    DAT.from_dict(partial(DAT.from_dat(file).to_dict(), translations())).to_dat(file, fmt="HDMain", sign=True)
    print(file, file.stat().st_size, "bytes")
EOF
```

The script keeps only the translated keys (16,485 in the Russian file).
Repeated keys are lists in the DAT, so a list is copied whole. Start the game, then open a dialog, a
planet screen, the galaxy map, and the ship screen. The merge works if the
text is Belarusian and no picture, map, or other text is missing. Afterwards,
restore the full files:

```bash
cp /tmp/Lang.Rus.dat "$MOD/CFG/Rus/Lang.dat"
cp /tmp/Lang.Eng.dat "$MOD/CFG/Eng/Lang.dat"
```

The script was tested on a synthetic signed DAT here, without the game.
