# Repository restructure plan

Status: draft for review; nothing is implemented. Numbers were measured on
`main` at `28aaae6`, before PR #37.

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

| Check | Russian from | Public CI | Game machine |
|---|---|---|---|
| JSON parses, no duplicate key, no empty `be`, tarask slips, termbase rows locked | not needed | yes | yes |
| Ids unchanged, tag parity, digits, `<format>` widths, rejected forms, reports | tag (2.3) | yes | yes |
| Ids match the game's classification (replaces `coverage.json`) | game | no | yes |
| Tag parity against the game; game Russian equals tag Russian (replaces stale-source check) | game, tag | no | yes |
| QMM and `robots.dat` round trips, build, in-game look | game | no | yes |

Without the tag, public CI keeps only the first row. `spell_check.py` reads
only `be` and stays local, because it needs hunspell. `--fix` keeps the tarask
slips but no longer copies translations into empty rows, since none are empty.

### 2.3 The Russian reference is a tag, not a copy

Tag the merge commit of PR #37 as `v1-first-pass`. Tools read Russian and
English with `git show v1-first-pass:corpus/<dir>/<file>.tsv` and join by id.
A prototype read the 159 TSVs of the current commit this way in 0.7 s. The ids
matched the JSON tree, and tag parity, digit, and width checks passed for all
61,571 rows. This reuses history the owner already keeps, and Cloud Agents get
it with a normal clone.

The trade-off: tools depend on one history object, frozen at game build
`2.1.2500` (open questions 1 and 2).

### 2.4 `coverage.json` is deleted

`coverage.json` (12.3 MB, 79,579 entries of id, kind, status, and reason, with
no game text) has two jobs. In CI, it proves that the corpus ids equal its
61,571 `translatable` entries; the tag's ids take over. On the game machine,
`check()` compares it with the game's string ids. That is redundant, because
`check()` already recomputes the translatable ids from the game, so a string
that an update adds or removes still fails. The 18,008 excluded entries are
documentation only.

## 3. Phases

Each phase is one PR. Phases 1, 2, and 4 must not change the built mod. The
build proof runs on the game machine after `build_test_mod.py`:

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
- On the game machine, at the merge commit, `corpus_data.py check` must pass.
- Run `corpus_data.py refresh` once; `git diff --ignore-cr-at-eol --stat` must
  print nothing. (`write_rows` turns the CRLF row ends of `Bomber` and `Ski`
  into LF.) Then run `git checkout -- corpus`. This proves the tag's Russian
  and English equal the game's, including the 44,138 quest rows that
  `check()` never compares.
- Build twice and save both hash lists; they must be identical, or the proof
  in later phases means nothing. Keep one as `build-0.sha256`, tag the commit
  `v1-first-pass`, and push the tag.

### Phase 1: Belarusian-only tree (three commits)

1. Add one stdlib loader and saver to `validate_corpus.py`, plus `source()`,
   which reads `{id: (ru, en)}` from the tag. The other scripts import them.
   The second `read_rows` and both TSV writers go; the writers disagreed on
   line endings.
2. A one-off converter, not committed, writes `corpus/**/*.json`, deletes the
   TSVs and `coverage.json`, and asserts the `id → be` map equals the tag's.
3. Checks and deletions:
   - `validate_corpus.py` runs the first two rows of the table in 2.2, and
     `corpus_data.py check` runs rows three and four.
   - From `corpus_data.py`, delete `refresh()`, `termbase_translations()`, the
     installed-mod `Lang.dat` harvest, the coverage code, `write_rows`, and
     `clean_generated`. The row builders stay for `check()`, and `ASSETS`
     keeps only the renderer.
   - Drop `qa_translation.py --batch`. It picks empty rows, so it prints
     nothing today.
   - Delete `audit_translation_scope.py` and `TRANSLATION-SCOPE.md`, which is
     stale (it says 44,625 translated).
   - `.gitattributes` treats `*.tsv` as normal text. CI checks out with
     `fetch-depth: 0`, which fetches tags; the pack is 17 MB, measured
     locally. In the docs, update only lines that name a changed path or
     command.

Proof: the converter assertion, the same `qa_translation.py` counts as on the
tag, and `build-1.sha256` equal to `build-0.sha256`.

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

### Phase 3: the fonts package (changes the build on purpose)

`AGENTS.md` contradicts itself. "PKG and manifests" says both manifests must
mount `belarusian_fonts.pkg`. "Font", like `FONT.md`, says a mod PKG of
`DATA/FONT` is ignored, so the build patches the game's `DATA/forms.pkg` in
place. Both came in commit `d5d3052`, and the build does both. Its self-check
inspects the package, not the `forms.pkg` the game reads.

Test by building without the package. Check `і` and `ў` on a text screen, plus
the one quest line with `’` (quest text is not apostrophe-folded). If they
render, delete the package, `write_patched_fonts()`, and the unused `bold`
parameter, and point the self-check at `forms.pkg`. Otherwise, document why
the package stays.

Proof: hashes are equal except `build/fonts` and the manifests, plus an
in-game screenshot.

### Phase 4: one home per rule

- Fix stale text:
  - The puzzle table still calls `Doomino`, `Edelweiss`, and `Elus` "empty".
  - `AGENTS.md` says ranger-tools is vendored in `tools/ranger-tools/`, but it
    is pip-installed from the pin in `requirements-local.txt`.
  - The font sections need to match phase 3.
- Rewrite "Known LLM mistakes" #9 for JSON.
- Merge `ORTHO.md` into `STYLE.md`. The Starnik rule lives only in `STYLE.md`
  and `starnik.mdc`; other files link to it.

### Phase 5: simpler installation (next step, outline)

Today `build_test_mod.py` runs on the game machine. It writes three packages
(buttons, fonts, quests) into `<game>/Mods/Tweaks/BelTranslate/`, along with
full patched `CFG/{Eng,Rus}/Lang.dat`, `CFG/robots.dat`, two manifests, and
`ModuleInfo.txt`. It also rewrites the game's own `forms.pkg`. The player
enables the mod on the Mods screen.

Four things block players:

- The Linux Steam path is hard-coded in three modules.
- The build needs Python 3.10+, Pillow, and ranger-tools. ranger-tools has no
  license (none on GitHub or in its README), so the project cannot bundle it.
- The `forms.pkg` patch survives disabling the mod and nothing undoes it. Per
  `AGENTS.md`, a Steam "verify files" removes it.
- On Windows, `write_utf16` would write `\r\r\n` line ends (reproduced with
  `newline="\r\n"`).

The outputs are game files with Belarusian swapped in. `Lang.dat` keeps
10,879 excluded values and `robots.dat` keeps 7,129. The quests keep their
logic, the buttons keep the game's art, and the fonts are the game's bitmaps.
`THIRD_PARTY.md` says the game is not redistributed.

- **Option A, a prebuilt download.** The owner attaches the built mod to a
  release; the player unzips it and enables it. Ceiling: it redistributes the
  game content above, a zip cannot patch `forms.pkg`, and every release needs
  the game machine.
- **Option B, a patcher the player runs.** CI zips the scripts, `corpus/`, and
  the Russo One font, with no game files. The player runs one command on their
  game folder, which builds the mod, patches `forms.pkg` with a backup, and
  can uninstall. The player then enables the mod on the Mods screen, because
  writing `ModCFG.txt` would replace their mod choice. Only Belarusian text,
  MIT code, and an OFL font are distributed. Ceiling: players need Python
  until a single executable exists, which needs a ranger-tools license. It
  must also rerun after a Steam verify.

Recommendation: B. The first PRs are a game-path argument with the newline
fix, an uninstall that restores `forms.pkg.vanilla`, and a release workflow.
Before designing more, test one thing in the game: does the engine merge a mod
`Lang.dat` that holds only the translated keys? If it does, CI can build both
`Lang.dat` files from the JSON without any game text. The DAT writer needs no
game file and is deterministic (measured). Quests, `robots.dat`, buttons, and
fonts always start from game files.

### Phase 6: the recheck (later; can run alongside phase 5)

- `qa_translation.py --review FILE -n 50` prints the next 50 unique Russian
  sources after the file's cursor. Each line shows the id, the row count, the
  Russian and English from the tag, the current `be`, termbase hints, and the
  other translations. Cloud Agents can run it without the game.
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
| Tag missing (fork, shallow clone) or moved | Tools say "fetch the tag"; CI fetches history; the game-machine check catches a moved tag |
| A game update changes Russian strings | `check()` lists ids whose game Russian differs from the tag |

## 5. Open questions for the owner

1. May tools read Russian and English from the `v1-first-pass` tag? The plan
   assumes yes. If not, public CI runs only the first row of the table in 2.2.
   The recheck then runs only on the game machine, from a gitignored view that
   the row builders write. Cloud Agents could not recheck.
2. If a game update changes the Russian, should a new tag record it? That adds
   the new text to history; the alternative is to review those ids only on the
   game machine.
3. Three engine behaviors need testing:
   - Does native Windows also ignore a mod `DATA/FONT` package? `FONT.md`
     records Proton only.
   - Does the engine read the mod's `CFG/robots.dat`, given the game keeps
     `Rus/` and `Eng/` copies?
   - Does the engine merge a partial mod `Lang.dat`?
4. Will you ask ranger-tools' author (denballakh) for a license? A bundled
   patcher depends on it.
5. Is option A acceptable even as a stopgap? The plan recommends against it.
