# Style — Space Rangers BE (taraškievica)

- Orthography: classical 2005 (`ORTHO.md`). Language tag `be-tarask`.
- Mod display name: **Belarusian** (not “Classical” in UI).
- Source sense: Russian `Lang.dat`; rebuild wording; do not paste Soviet BE calques.
- Tone: dry humor, military + pirate slang OK; keep UI short.
- Address: stay consistent with source (вы/ты) per string family.
- Proper names (races, ships): lock in `TERMBASE.tsv`; no free synonym rotation.
- Main-menu labels are baked `.gi` images; update those assets as well as `Lang.dat`.
- Test flow: `build_test_mod.py`; details and format rules are in `AGENTS.md`.

## Sense check before lock

Hunspell only catches spelling. Before writing a new lemma to `TERMBASE.tsv`:

1. Name the **Russian sense in this UI** (not the first dictionary gloss).
2. Open **Starnik** (`https://starnik.by`) first: meaning, endings, and the Belarusian lemma. Do not lock a common word from memory or from the Russian shape (`корсар`→`карсар`).
3. Skarnik (`skarnik.by`) only if the RU→BE mapping is still unclear. Google/Wikipedia last.
4. Run `hunspell -d be_BY@tarask`. If Starnik and tarask hunspell disagree on **spelling**, hunspell wins (`шкіпэр`, `дэпазыт`). Starnik still wins on **meaning**.
5. Write the row with sense, endings, rejected calque, and the Starnik URL. Empty `notes`/`source` means the lemma is not locked yet.
