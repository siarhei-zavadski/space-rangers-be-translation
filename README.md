# Space Rangers HD — Belarusian translation

Working Linux-native translation pipeline for Space Rangers HD: A War Apart.
This is an unofficial, non-commercial fan project.

## Translate

Edit the Belarusian values in `corpus/`. The repository is the source of truth.
The Russian line in the game is the sense; the English line is the cross-check.
The corpus covers core DAT text, all 80 text quests, planetary-battle
strings, and known baked labels. The line procedure is in
[`TRANSLATION.md`](TRANSLATION.md).

## Translation tools

Daily lookup order is in [`STYLE.md`](STYLE.md); spelling lock is in
[`STYLE.md`](STYLE.md). Spelling check is `hunspell -d be_BY@tarask`
from the `hunspell-be-tarask-alt` 0.65 package.

| Tool | Website | Use |
|------|---------|-----|
| Starnik | https://starnik.by | Meaning, lemma, and endings first |
| Skarnik | https://www.skarnik.by | RU→BE only if Starnik is still unclear |
| spell-be-tarask | https://github.com/375gnu/spell-be-tarask | `hunspell -d be_BY@tarask`; spelling wins clashes |
| Kamputerm | https://github.com/quendimax/kamputerm | IT/UI terms; classical `be=` column |
| Беларускі клясычны правапіс (2005) | https://knihi.com/storage/pravapis2005.html | Orthography rules |

## Install the mod (players)

Download the **beltranslate-patcher** zip from a
[GitHub Release](https://github.com/siarhei-zavadski/space-rangers-be-translation/releases)
(or build one with `python3 pack_release.py`). Follow [`INSTALL.md`](INSTALL.md):
venv, `pip install -r requirements-local.txt`, then `install.py --game …`.

The zip ships Belarusian text, MIT scripts, and the OFL font only — not the
game. ranger-tools is installed from GitHub by the player.

## Rebuild test mod (developers)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-local.txt
.venv/bin/python corpus_data.py check
.venv/bin/python build_test_mod.py
```

The script writes `BelTranslate` directly into the installed game, builds Belarusian `.gi` menu assets and patched Eng/Rus `Lang.dat` files, then validates DAT/PKG/GI structure. Player-facing installs use `install.py` (same build, skips the git tag Russian check).

## Checks

GitHub Actions runs `Validate` on push and pull request. That workflow reads
the repository and uses no secrets.

Original project code is MIT-licensed. Game content remains subject to its
rights holders; see [`THIRD_PARTY.md`](THIRD_PARTY.md).

For future agent work, start with [`AGENTS.md`](AGENTS.md). Language policy lives in [`STYLE.md`](STYLE.md) and [`TERMBASE.tsv`](TERMBASE.tsv).
