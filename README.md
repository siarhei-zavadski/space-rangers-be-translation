# Space Rangers HD — Belarusian translation

Working Linux-native translation pipeline for Space Rangers HD: A War Apart.
This is an unofficial, non-commercial fan project.

## Translate in Crowdin

Use the live
[Space Rangers HD Belarusian project](https://crowdin.com/project/space-rangers-hd-belarusian).
The game-structured corpus covers core DAT text, all 80 text quests,
planetary-battle strings, and known baked labels. Current counts and
download/build steps are in [`TRANSLATION-SCOPE.md`](TRANSLATION-SCOPE.md) and
[`CROWDIN.md`](CROWDIN.md).

## Translation tools

Daily lookup order is in [`STYLE.md`](STYLE.md); spelling lock is in
[`ORTHO.md`](ORTHO.md). Hunspell install is in
[`TOOLS-INSTALL.md`](TOOLS-INSTALL.md).

| Tool | Website | Use |
|------|---------|-----|
| Crowdin | https://crowdin.com/project/space-rangers-hd-belarusian | Translation editor and sync |
| Starnik | https://starnik.by | Meaning, lemma, and endings first |
| Skarnik | https://www.skarnik.by | RU→BE only if Starnik is still unclear |
| spell-be-tarask | https://github.com/375gnu/spell-be-tarask | `hunspell -d be_BY@tarask`; spelling wins clashes |
| Kamputerm | https://github.com/quendimax/kamputerm | IT/UI terms; classical `be=` column |
| Беларускі клясычны правапіс (2005) | https://knihi.com/storage/pravapis2005.html | Orthography rules |

## Rebuild test mod

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
.venv/bin/python crowdin_sync.py check
.venv/bin/python build_test_mod.py
```

The script writes `BelTranslate` directly into the installed game, builds Belarusian `.gi` menu assets and patched Eng/Rus `Lang.dat` files, then validates DAT/PKG/GI structure.

## Repository automation

GitHub preparation, CI/CD, secrets, and the current Crowdin open-source
eligibility blockers are documented in
[`OPEN_SOURCE_READINESS.md`](OPEN_SOURCE_READINESS.md). A private repository is
valid for staging, but it does not qualify for Crowdin's open-source license.

Original project code is MIT-licensed. Game content remains subject to its
rights holders; see [`THIRD_PARTY.md`](THIRD_PARTY.md).

For future agent work, start with [`AGENTS.md`](AGENTS.md). Language policy lives in [`ORTHO.md`](ORTHO.md), [`STYLE.md`](STYLE.md), and [`TERMBASE.tsv`](TERMBASE.tsv).
