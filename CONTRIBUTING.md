# Contributing

## Translation changes

Edit the `be` column in `corpus/`. The repository is the source of truth.
Follow `ORTHO.md`, `STYLE.md`, and `TERMBASE.tsv`. Preserve placeholders,
formulas, parameter references, and line breaks exactly.

Do not edit Russian source cells or generated identifiers by hand.

## Code and corpus changes

Before opening a pull request:

```bash
python3 validate_corpus.py
python3 -m py_compile *.py
```

Changes that regenerate source data additionally require a legitimate local
game installation:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
.venv/bin/python corpus_data.py refresh
.venv/bin/python audit_translation_scope.py --write
.venv/bin/python corpus_data.py check
```

Do not commit game binaries, extracted packages, backups, build output,
or credentials. See `THIRD_PARTY.md`.
