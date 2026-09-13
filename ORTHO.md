# Orthography lock — classical Belarusian (тарашкевіца)

**Locked for this project.** Do not switch mid-translation.

## What we mean by “old Belarusian”

User intent: Belarusian **before the 1933 Soviet orthography reform** and the later russifying lexical pressure — not Middle Belarusian as everyday game UI language.

Practical standard for this mod:

| Layer | Choice |
|-------|--------|
| **Writing system** | **Belarusian Classical Orthography (тарашкевіца), 2005 modern normalization** — language tag `be-tarask` |
| **Lexicon preference** | Prefer native / pre-russified equivalents over Soviet calques from Russian (same spirit as the Fantasy Translators’ Guide) |
| **Deep historical lexicon** | Use *Гістарычны слоўнік* (XIV–XVIII) to **recover terms**, then normalize spelling to 2005 classical rules for UI |

We do **not** write quest UI in raw 16th-century chancellery Belarusian. We write modern literary Belarusian in classical orthography, with historically grounded vocabulary where it fits sci-fi/military register.

## Why 2005 classical, not “whatever looks old”

- Branisłaŭ Taraškievič’s school grammar (1918) is the root of the classical norm.
- 1933 reform created official **наркамаўка** (closer to Russian patterns).
- Diaspora + independent press kept classical spelling; 2005 book *Беларускі клясычны правапіс* is the living rulebook used by Naša Niva, Radio Liberty, `be-tarask` Wikipedia, etc.
- Spellcheckers and dictionaries exist for that 2005 norm.

## Canonical rule sources

1. **Беларускі клясычны правапіс (2005)**  
   - HTML: https://knihi.com/storage/pravapis2005.html  
   - PDF: https://archive.svaboda.org/info/pravapis2005.pdf  
2. Overview: https://be-tarask.wikipedia.org/wiki/Беларускі_клясычны_правапіс  
3. EN summary: https://en.wikipedia.org/wiki/Tara%C5%A1kievica  

## Spellcheck (must match this lock)

| Tool | Notes |
|------|--------|
| **spell-be-tarask** (Hunspell) | https://github.com/375gnu/spell-be-tarask — LibreOffice `.oxt`, Firefox `.xpi`, deb/rpm/zip |
| Prefer `hunspell-be-tarask-alt` if narkamaŭka hunspell also installed | Avoids `be_BY` alias clash |

**Do not** use BNKorpus / official 2008 school spellcheck as the final gate — those target narkamaŭka.

## Lexical policy (anti-russification)

When Skarnik / Soviet academic dicts offer a Russian calque first and a native synonym second:

1. Prefer the **native / older** synonym if it is understandable in context.
2. Cite the Fantasy Translators’ Guide / Historical Dictionary / Kamputerm `be=` form when they disagree with Soviet game localizations.
3. Record the rejected calque in `TERMBASE.tsv` `notes` so we never flip-flop.

Optional letter **ґ** (plosive /ɡ/) may be used per 2005 classical rules where needed; stay consistent once a lemma is locked.

## Out of scope for v1

- Parallel narkamaŭka release (can be a later conversion pass if someone asks).
- Mixing tarask and narkamaŭka strings in one build.
