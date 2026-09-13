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

## GitHub automation

`.github/workflows/crowdin-sync.yml`:

- uploads changed source files from trusted pushes to `main` using
  `crowdin_upload.py`, which explicitly configures new TSV schemas;
- imports checked-in Belarusian cells, including translations equal to source;
- downloads Crowdin daily and opens a reviewable pull request.

Add `CROWDIN_PERSONAL_TOKEN` as a GitHub Actions secret and allow Actions to
create pull requests. The workflow never stores the token in the repository.
See [`OPEN_SOURCE_READINESS.md`](OPEN_SOURCE_READINESS.md) before changing
repository visibility or applying for Crowdin's open-source plan.
