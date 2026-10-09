# Contributing

## Translation changes

Edit the Belarusian values in `corpus/`. The repository is the source of truth.
Follow `STYLE.md` and `TERMBASE.tsv`. Preserve placeholders,
formulas, parameter references, and line breaks exactly.

Do not edit the identifiers (the keys) by hand.

## Code and corpus changes

Before opening a pull request:

```bash
python3 validate_corpus.py
python3 -m py_compile *.py
```

Checks against the Russian and the build additionally require a legitimate
local game installation:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
.venv/bin/python corpus_data.py check
.venv/bin/python qa_translation.py
```

Do not commit game binaries, extracted packages, backups, build output,
or credentials. See `THIRD_PARTY.md`.
