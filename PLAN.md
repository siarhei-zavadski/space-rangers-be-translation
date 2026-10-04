# Belarusian translation plan — Space Rangers HD: A War Apart

**Goal:** ship a proper Belarusian fan localization mod (UI + quests + UI art where needed), in **classical / pre-Soviet orthography (тарашкевіца)**, with consistent anti-russified terminology.

**Status (2026-09-13):** plan revised for classical Belarusian (`be-tarask`).  
**Game install verified:** `~/.local/share/Steam/steamapps/common/Space Rangers HD A War Apart` has `Rangers.exe`, `CFG/{Rus,Eng}/Lang.dat`, quest pkgs, and built-in DE/ES language mods under `Mods/Tweaks/`.

**Orthography lock:** see [`ORTHO.md`](ORTHO.md) — **клясычны правапіс 2005**, not narkamaŭka.

### Install recheck (verified)

| Item | Status | Evidence |
|------|--------|----------|
| Game binaries | OK | `Rangers.exe` (~5 MB) |
| Rus/Eng `Lang.dat` | OK | `CFG/Rus/Lang.dat` 887K, `CFG/Eng/Lang.dat` 847K |
| Quest packs | OK | `DATA/questsRus.pkg` 3.8M, `questsEng.pkg` 3.7M |
| UI pkgs (text-in-art later) | OK | `mainmenu.pkg` 198M, `forms.pkg` 181M, `russian.pkg`/`english.pkg` |
| Mod system | OK | `Mods/ModCFG.txt` (`CurrentMod=` empty); Tweaks include **German** + **Spanish** |
| Language-mod template | OK | German: `CFG/{Rus,Eng}/Lang.dat` + `DATA/*.pkg` + `ModuleInfo.txt` + `INSTALL_*.TXT`; conflicts with Spanish |
| Project docs | OK | `PLAN.md`, `ORTHO.md` |
| Wine (for later Win GUIs) | **OK** | `wine-6.0.3` + wine32/wine64 |
| Lang.dat editor (Linux) | **OK** | `tools/ranger-tools` + `.venv` (`DAT` fmt `HDMain`); export `tools/Lang.Rus.export.txt` |
| BlockParEditor (Win GUI) | **BLOCKED** | snk/playground mirrors unavailable; optional now |
| Hunspell classical | **OK** | `spell-be-tarask` v0.65 → `be_BY@tarask` |
| Vanilla Lang backup | **OK** | `backup/Lang.{Rus,Eng}.vanilla.dat` |
| SRResEditor / TGE | **DEFERRED** | After UI text pipeline |
| Mod skeleton `BelTranslate` | **OK** | `Mods/Tweaks/BelTranslate/` + UTF-16 `ModuleInfo.txt` |
| `STYLE.md` / `TERMBASE.tsv` | **OK (seed)** | Test menu terms recorded |
| DAT + GI + PKG flow | **VERIFIED IN GAME** | User confirmed generated Belarusian buttons and live text work |

---

## 0. Decisions to lock first

| Decision | Choice | Why |
|----------|--------|-----|
| Orthography | **Taraškievica / classical 2005** (`be-tarask`) | Matches user preference for pre-1933 / non-Soviet tradition; has modern rulebook + Hunspell |
| Lexicon | Prefer **native / historical** terms over Soviet RU calques | Same anti-russification line as Fantasy Translators’ Guide + Historical Dictionary |
| Source language | Translate meaning from **Russian `CFG/Rus/Lang.dat`**; **never** copy Soviet BE game phrasing blindly | Sense from RU, wording rebuilt in classical BE |
| Mod model | Overlay `Mods/BelTranslate/` (German-style) | Update-safe |
| Scope v1 | Menus + galaxy UI + items/races + main dialogue | Quests + button art later |
| Community | Ask SNK Discord early for Bel locale vs Rus overwrite | Hardcodes / achievements packaging |

---

## 1. What must be translated (technical map)

### Layer A — `Lang.dat` (core)

- Path base: `CFG/Rus/Lang.dat` (and/or Eng).
- Tool: Linux-native `ranger-tools` through `build_test_mod.py`; BlockParEditor is optional.
- Patch both Eng and Rus DATs through dictionaries; avoid lossy full-text round trips.
- Ship as: `Mods/Tweaks/BelTranslate/CFG/{Eng,Rus}/Lang.dat`.
- All human-readable strings in **classical orthography**.

### Layer B — UI graphics in `.pkg`

- Buttons and panels with burned-in text.
- Tool: Linux-native `ranger-tools` GI/PKG support; SRResEditor is optional.
- Only remake assets that show human-readable text (also classical spelling).

### Layer C — text quests

- Archives: `DATA/questsRus.pkg` / `questsEng.pkg`.
- Unpack → edit `.qmm` in **TGE** → repack.
- Largest volume; do after UI termbase is stable in tarask.

### Layer D — engine hardcodes

- Escalate leftovers to SNK via Discord (`discord.gg/WZfx4K`) or [snk-games.net English forum](https://snk-games.net/forums/viewforum.php?f=39).
- Precedent: German mod integrated into Steam 2.1.2400+.

### Precedents (structure only — not orthography)

| Lang | Notes |
|------|--------|
| **German** | Built-in Mods menu since 2.1.2400. [Nexus](https://www.nexusmods.com/spacerangersawarapart/mods/5) |
| **Polish (2025)** | Full fan pack; AI-assisted chunks. [Steam + Drive](https://steamcommunity.com/app/214730/discussions/1/601894733441163203/) |
| **Spanish** | Fan pack + mod translations |
| **PCGamingWiki** | https://www.pcgamingwiki.com/wiki/Space_Rangers_HD:_A_War_Apart |

Tools:

- BlockParEditor: [Dropbox](https://www.dropbox.com/sh/3kdy45sgdzn9w50/AAC7SGfgB2DxMTLxbk-XZfiba?dl=0) / [playground.ru](https://www.playground.ru/space_rangers_2_dominators/file/space_rangers_hd_a_war_apart_redaktor_dat_fajlov-1622253)
- Full toolset: [Dropbox](https://www.dropbox.com/sh/spxo4l8ado7v1gj/AAC_b7dsWyazRLEbKbhPfaCNa?dl=0)

---

## 2. Phased work plan

### Phase 0 — Setup (1–2 evenings)

Completed. `build_test_mod.py` now builds signed Eng/Rus DAT files, nine GI button states, `belarusian.pkg`, manifests, and metadata. The user confirmed the result in-game.

**Exit criteria met:** packaged menu images and live DAT text render in Belarusian; Hunspell tarask and structural self-checks pass.

### Phase 1 — Style + termbase (before mass translate)

| File | Purpose |
|------|---------|
| `ORTHO.md` | **Done** — classical 2005 lock |
| `STYLE.md` | Tone, address forms, race names, humor register |
| `TERMBASE.tsv` | `id`, `ru`, `en`, `be_tarask`, `rejected_calque`, `notes`, `source` |

Seed high-frequency terms first (races, hulls, weapons, Buy/Sell/Jump/Dock).  
Every `be_tarask` form must pass **spell-be-tarask** or cite an exception in `notes`.

**Exit criteria:** ≥150 core terms locked with classical spelling + source cites.

### Phase 2 — UI / Lang.dat v1

1. Order: main menu → options → galaxy → hangar/trade → combat → diplomacy → encyclopaedia.
2. Small chunks; human edit after any MT; MT often emits narkamaŭka — **re-spell to tarask**.
3. After each section: Hunspell tarask + 10 min play; log `QA.md`.
4. Unfinished keys → `#TODO` in termbase only.

**Exit criteria:** new game to first jump with classical BE UI.

### Phase 3 — Graphics + quests

Same as before; glossary must stay tarask-consistent.

### Phase 4 — Release

1. README must say **клясычны правапіс (тарашкевіца)** up front so players know.
2. Steam / Nexus / [belarusian.games](https://belarusian.games/).
3. Optional later: narkamaŭka conversion fork — **not** v1.

---

## 3. Dictionary & terminology sources (classical-first)

### A. Orthography & living classical corpora (primary)

| Source | URL | Use |
|--------|-----|-----|
| **Беларускі клясычны правапіс (2005)** | https://knihi.com/storage/pravapis2005.html · PDF https://archive.svaboda.org/info/pravapis2005.pdf | Rulebook for every spelling dispute |
| **be-tarask Wikipedia** | https://be-tarask.wikipedia.org/ | Living classical prose + terminology |
| **Taraškievič grammar** (historical root) | https://kamunikat.org/belaruskaya-gramatyka-tarashkevich-branislaw | Original classical school grammar |
| Overview articles | https://en.wikipedia.org/wiki/Tara%C5%A1kievica · https://www.svaboda.org/a/33663813.html | Context for 1933 split |

### B. Classical orthographic dictionaries

| Source | URL | Use |
|--------|-----|-----|
| **Naša Niva orthographic dictionary** (reconstructed CSV / web) | https://github.com/andreihar/nasa-niva-dict | Classical spelling lemmas (2001 NN editorial dict) |
| **spell-be-tarask** | https://github.com/375gnu/spell-be-tarask | Hunspell QA (2005 classical) |

### C. Historical / pre-russified lexicon (recover words, then re-spell)

| Source | URL | Use |
|--------|-----|-----|
| **Гістарычны слоўнік беларускай мовы** (XIV–XVIII; 37 vols) | https://archive.org/details/bel-enc-hsbm · https://knihi.com/none/Histarycny_slounik_bielaruskaj_movy_zip.html | Older native terms for ranks, crafts, war, law |
| Fantasy guide reliance on HSBM / folklore | https://nashaniva.com/403104 | Method: avoid RU-game calques |

### D. Game / fantasy terminology (aligns with anti-calque goal)

| Source | URL | Use |
|--------|-----|-----|
| **Дапаможнік для перакладчыкаў фэнтэзі** (v0.4, 2026; CC BY-SA 4.0) | https://heroes.by-reservation.com/dapamoznik-pierakladcyku-fentezi/ · https://boosty.to/by_reservation | Creatures, weapons, RPG lexicon without RU intermediary |
| **Belarusian Games** | https://belarusian.games/ | See which localizations ship tarask vs narkamaŭka; steal only matching orthography |

### E. IT / UI (classical column)

| Source | URL | Use |
|--------|-----|-----|
| **Kamputerm** | https://github.com/quendimax/kamputerm | Prefer attribute **`be`** (classical) over `by` (school) |
| Kamputerm history | https://devby.io/news/by-terms | One EN → one BE policy |

### F. Military

| Source | URL | Use |
|--------|-----|-----|
| **Вайсковы слоўнік** (Sudnik, Čyslaŭ) | https://slounik.org/data/vajskovy.txt · [PDF](https://knihi-online.com/assets/files/23/06/rasiejska-bielaruski-vajskovy-slounik-sudnik-cyslau.pdf) | Sense + terms; **re-spell to tarask** if source is school orthography |

### G. Narkamaŭka dictionaries — sense only, not final spelling

Use these to understand RU→BE meaning, then convert spelling via §A–B:

| Source | URL | Caveat |
|--------|-----|--------|
| Skarnik | https://www.skarnik.by/ | School/academic spelling; not final form |
| Slounik.org / SBM 2012 | https://slounik.org/ | Post-2008 official orthography |
| Verbum | https://verbum.by/ | Same — sense + morphology, then tarask rewrite |
| BNKorpus / corpus.by spell | https://bnkorpus.info/spell.html | **Not** the project spellgate |

### H. SRHD process refs

- https://steamcommunity.com/app/214730/discussions/1/1741140901902702464/
- https://steamcommunity.com/app/214730/discussions/1/613939294367754493/
- https://steamcommunity.com/app/214730/discussions/1/601894733441163203/

---

## 4. Suggested lookup order per string

1. `TERMBASE.tsv` hit → reuse exact `be_tarask`.
2. Fantasy guide / Kamputerm **`be=`** / Historical Dictionary if domain matches.
3. Skarnik for **sense** (RU→BE).
4. Rewrite spelling to **2005 classical**; check Naša Niva dict / pravapis2005.
5. Hunspell **spell-be-tarask**.
6. If ambiguous: keep RU temporarily, ticket `QA.md`; record rejected calque.

---

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Corrupt `Lang.dat` | Tiny edits + backup; no empty trailing lines |
| Accidental narkamaŭka from MT / Skarnik | Always run tarask Hunspell; termbase stores only `be_tarask` |
| “Too archaic / unreadable” complaints | Classical 2005 ≠ Middle Belarusian; README explains; keep sci-fi UI clear |
| Orthography flamewars | `ORTHO.md` + README; no dual orthography in one build |
| Synonym chaos | Termbase + rejected_calque column |
| Hardcoded leftovers | List + ask SNK |
| Burnout | UI first; ship playable incomplete |

---

## 6. Immediate next actions

1. Expand `TERMBASE.tsv` to the first 50 high-frequency terms.
2. Add image labels to `corpus/assets/`; translate live strings in the split
   `corpus/{lang_dat,quests,robots,assets}/` corpus.
3. Rebuild with `.venv/bin/python build_test_mod.py`.
4. Check `build/preview/`, Hunspell, then verify each changed screen in-game.
5. Test runtime AFT rendering for `ў` and optional `ґ`.

---

## 7. Deliverables checklist

### Prior planning goal
- [x] Technical map
- [x] Phased plan
- [x] Dictionary sources (initial, school-biased)
- [x] Precedent links

### This revision (classical Belarusian)
- [x] Orthography flipped to classical / taraškievica in plan
- [x] `ORTHO.md` lock with 2005 rulebook + rationale
- [x] Classical dictionaries, Hunspell, historical lexicon sources listed
- [x] Lookup order + risks updated for anti-russification / tarask QA
- [x] Game install rechecked (Lang.dat + DE/ES mod template present)
- [x] Tools install plan + Wine + ranger-tools + spell-be-tarask (see `TOOLS-INSTALL.md`)
- [ ] BlockParEditor optional manual download when mirrors up
- [ ] `Mods/Tweaks/BelTranslate` skeleton + one-string in-game smoke-test
- [ ] Living `TERMBASE.tsv` / `STYLE.md`
