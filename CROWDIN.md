# Translating with Crowdin

Translate at
<https://crowdin.com/project/space-rangers-hd-belarusian>.

The project uses Russian as its source and Crowdin's built-in Belarusian (`be`)
as its target. Wording still follows [`ORTHO.md`](ORTHO.md); Crowdin does not
enforce the orthography.

## File layout

Crowdin mirrors the game instead of using one giant spreadsheet:

- `crowdin/lang_dat/<Section>.tsv` — one file per translatable `Lang.dat`
  top-level section.
- `crowdin/quests/<Quest>.qmm.tsv` — one file per text quest.
- `crowdin/robots/robots.tsv` — planetary-battle strings.
- `crowdin/assets/<Form>.tsv` — labels baked into GI images.

Every file uses the columns `identifier`, `source_phrase`, `context`, `labels`,
and `be`. The checked-in [`crowdin.yml`](crowdin.yml) configures those columns
and preserves the folder hierarchy.

## Source of truth

Translate in the Crowdin editor. Local `be` cells are only a seed. Upload
them with `crowdin_upload.py`, and download before a game build so git matches
Crowdin. Later wording changes belong on Crowdin. Do not treat an unsynced
local TSV as newer than Crowdin.

## Download translations and build

Install Crowdin CLI 5 once:

```bash
npm install -g @crowdin/cli
```

Use a newly generated token; never commit it:

```bash
export CROWDIN_PERSONAL_TOKEN='...'
crowdin download -l be
.venv/bin/python crowdin_sync.py check
.venv/bin/python build_test_mod.py
```

The Crowdin project has **Skip untranslated strings** enabled. Downloaded TSVs
therefore retain empty target cells, and the build falls back to Russian for
unfinished strings.

## Update game sources

After a game update, or after changing extraction rules:

```bash
.venv/bin/python crowdin_sync.py refresh
.venv/bin/python audit_translation_scope.py --write
.venv/bin/python crowdin_upload.py
crowdin upload translations -l be --import-eq-suggestions
```

`refresh` preserves existing Belarusian targets by stable identifier. The
checker rejects duplicate/unknown IDs, stale Russian source, changed
placeholders, incomplete source classification, unsafe QMM round-trips, and
invalid `robots.dat` structure.

Use `crowdin_upload.py --new-only` when only newly generated files need
creation. The dedicated uploader is intentional: Crowdin CLI 5 detects TSV as
CSV but does not apply a spreadsheet schema when it creates a brand-new TSV.

## Coverage

[`crowdin/coverage.json`](crowdin/coverage.json) classifies every inspected
`Lang.dat` value, QMM text field, `robots.dat` property, and known baked label.
[`TRANSLATION-SCOPE.md`](TRANSLATION-SCOPE.md) is the generated summary.

Binary GI/AFT files are not uploaded to Crowdin. Their source labels are in the
asset TSVs and the build renders supported labels into the mod package.

Keep `CROWDIN_PERSONAL_TOKEN` in the shell. Do not put it in the repository
or in GitHub Actions.
