# Contributing

## Translation changes

Translate in the
[Crowdin project](https://crowdin.com/project/space-rangers-hd-belarusian).
Follow `ORTHO.md`, `STYLE.md`, and `TERMBASE.tsv`. Preserve placeholders,
formulas, parameter references, and line breaks exactly.

Crowdin exports are proposed automatically as GitHub pull requests. Do not
edit Russian source cells or generated identifiers by hand.

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
.venv/bin/python crowdin_sync.py refresh
.venv/bin/python audit_translation_scope.py --write
.venv/bin/python crowdin_sync.py check
```

Do not commit game binaries, extracted packages, backups, build output,
credentials, or personal Crowdin tokens. See `THIRD_PARTY.md`.
