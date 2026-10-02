# Translation plan — classical Belarusian, one line at a time

There is no Cursor skill that makes the agent a Belarusian translator.
The job is this file plus the tools the repo already runs.

Standing order: translate meaning from the Russian line, check the English
reference in the `context` column, write classical Belarusian (`be-tarask`).
Reuse a locked term. Do not invent a second pipeline.

## Tools, in this order

1. `TERMBASE.tsv` — if the lemma is already there, copy `be_tarask` exactly.
2. [Starnik](https://starnik.by) — sense, lemma, endings for this UI.
   Skarnik only when the Russian-to-Belarusian sense is still unclear.
3. `hunspell -d be_BY@tarask` through `spell_check.py`.
   Spelling clash: hunspell wins. Meaning clash: Starnik wins.
   Record the new lemma in `TERMBASE.tsv` (sense, endings, rejected calque, Starnik URL).
4. `validate_corpus.py` — placeholders, tags, and `{…}` / `[pN]` must match the source.
5. `crowdin_sync.py check` — corpus ids, source text, and quest round-trip.
6. `build_test_mod.py` — only when the line is on a screen the build already ships.

`STYLE.md` and `ORTHO.md` are the language rules. `CROWDIN.md` is where the
`be` cell is supposed to be edited once Crowdin is the source of truth.
Formulas are not in the TSV (`formula`, `expression`, `formula_to_pass` in
`crowdin_sync.py`). Leave them alone.

## What the quest engine actually checks

A text quest does not compare the sentence you wrote with a hidden answer.
The player picks a jump. The quest checks that jump’s id and its numeric
parameters. A translation breaks the quest only when the player can no longer
see which jump is right, or when a diagram stops lining up.

Copy every `<tag>`, `{…}`, `[pN]`, and line break. Inside a `<fix>` picture,
change a word only when the line is still the same width as the Russian line.

## Puzzles that break if the words change

### Letter identity — keep the letters that the puzzle reads

**`Pharaon.qmm`** (already filled). The tomb key is a letter puzzle, not a
glossary item.

- Gods, in the diary and on the jumps: `Арес`, `Вмаз`, `Звер`, `Зевс`, `Зема`, `Марс`, `Мерс`.
- Sons: `Анусптис`, `Вертепопес`, `Ептимат`, `Замполет`, `Мойхренес`, `Рамзец`, `Серемтут`.
- Rule, stated in the quest: a god patronizes a person when the first letter
  of the person’s name occurs in the god’s name. The worked example is
  `Арес` → `А`, `Р`, `Е`, `С`. Sons 1, 2, 4, and 6 (the set changes per
  visit) pick the statue. The box later is a separate order puzzle
  (`Весельчак`, `Красавчик`, `Толстячок`, `Очкарик`, `Грязнуля`, `Воин`,
  `Испуганный`): each nickname has to keep matching the description on its
  own jump.

The current `be` column keeps those first letters (`А В Е З М Р С`).
`Звер` is spelled `Зьвер`, which still contains `З В Е Р`. Do not “correct”
`Арес` to `Арэс`, and do not let `Ептимат` start with `Э`. Either change
drops the letter the diary names, while the quest still accepts only the
original jump.

**`Feipsycho.qmm`** (empty). Three separate gates:

- The steel door is an 8-strip clock. The `<fix>` drawing stays as drawn.
  The poem is the solution: press one, count eight the way a clock does,
  skip a strip already pressed, finish on one. The choices are the digits
  `1`–`8`. Translate the poem only if those quantities stay exact.
- Eight jumps are the single letters `М В Ж К Р С Т Ц`. The turnip clue
  (`Дедка`, `Бабка`, `Внучка`, `Жучка`, `Кошка`, `Репка`, then `Мышка`)
  points at the jump labeled `М`. Keep those initials, or rewrite the clue
  so it still selects that same jump. Do not relabel the jump.
- The patient’s riddle asks how many creatures he named. The success line
  says two: a horse and a human. The choice is the digit `2`. The riddle
  has to keep exactly those two, and the choice has to stay `2`.

**`Piratesnest.qmm`** (empty). The wardrobe password is not typed. The NPC
says a URL and the jump text is the same URL. Keep both copies identical:
`gns://pelengessa.peleng/`, `gns://bombinhome.maloc/`,
`gns://riaskaportal.peleng/`, and the same host tokens
`createbomb`, `hammerthor`.

**`Easywork.qmm`** (empty). One status line is a letter grid,
`. а б в г`, over digits taken from `[p25]`–`[p28]`. Those four letters
are the alphabet the player reads. Leave them. The order tables lower in
the same file are ordinary fixed-width bills (see below).

**`Kidnapped.qmm`**, location `210` (empty). Not a gate. The coin at the
end of the quest is a Vigenère easter egg. Leave these three tokens
unchanged: `VIGENERE`, `kiiltgjtfjph kqxwzr`, `virsle`. With key `virsle`
the longer string decrypts to “particolored pigeon”. Translate the
paragraph around them.

**`GLAVRED.qmm`** (empty). Not a gate. A newspaper joke expands `КВМ` as
`КиВи Ем` and names the prize `КИВИМ`. Translate it only if the
abbreviation still equals the expansion.

### Diagrams — the picture is the puzzle

Leave the drawing. Translate a label only when that line stays the same
width as the Russian line.

| Quest | What is stored | State |
|---|---|---|
| `Maze.qmm` | Corridor map of `#`, `^`, `\|` inside `<fix>` | empty |
| `Logic.qmm` | Grids `[ ]`, `[0]`, `[+]` | filled, grids intact |
| `Codebox.qmm` | Two keypads. Header was `Ключ` / `Образец`; digits come from `[p2]`–`[p5]` and `{n}` | filled; `Образец` is `Узор` padded back to 7 columns so the label sits on the sample grid |
| `Bomber.qmm` | Grid rows `A`–`E` in `<format=center, 40>` | empty; keep the Latin letters |
| `Pilot.qmm` | Track `I . . o I` | empty |
| `Player.qmm` | 3×3 cells `1`–`9` | filled, grid intact |
| `Doomino.qmm` | Domino faces `[p40]<clr>=<clrEnd>[p41]` | empty; do not edit inside the brackets |
| `Edelweiss.qmm` | Badge number, one digit per cell, from `[p20]` | empty |
| `Testing.qmm` | Magic square `1`–`9` summing to 15 | empty; keep the digits, flavor text is free |
| `Xenolog.qmm` | Tiny map with `o` inside `<fix>` | empty |
| `Elus.qmm` | Attribute grid. Widths are the Russian words: `<format=left,8>Большой</format><format=left,7>Синий</format><format=left,5>Круг</format>`, and the same for `Малый`, `Желтый`, `Ромб` | empty; a longer word smashes the columns and the logic puzzle cannot be read |
| `Shashki.qmm` | Checker cells `Б` and `Ч` (white / black) | filled; those two letters stayed, keep them |
| `Domoclan.qmm` | Machine line `ACCESS CARD; ID = 2111; OBJECT = LAB; … NAME = Аакси-Тоон` | empty; keep the tokens and the id |

`Losthero.qmm` shows the cabin code `195449` in prose. Keep the digits.
`Evidence.qmm`, `Sibolusovt.qmm`, and `Disk.qmm` teach a code in one line
and confirm it with a jump. Translate the sentence; the code characters
on both sides stay the same. `Disk.qmm` is already filled.

The same width trap, without being a puzzle, sits in `Election.qmm`,
`Rvk.qmm`, `Ski.qmm`, `Amnesia.qmm`, `SpaceLines.qmm`, `Olympiada.qmm`,
`Proprolog.qmm`, `Kiberrazum.qmm`, and `Colonization.qmm`: a
`<format=left,N>` or `<format=center,N>` cell clips when the Belarusian
word is longer than `N`.

Lines that only mention a puzzle (`головоломка`, a shipment, a failed guess
such as Mafia’s `Пассворд` / `Parol`) are ordinary prose.

## Order of work

UI and `crowdin/lang_dat/` first, until the termbase covers the words those
screens repeat. Quests after that. Puzzle files last, one file at a time,
so every copy of a name (diary, statue, jump) is edited together.

Before a puzzle file is called done: tags still match
(`validate_corpus.py`), and every `<fix>` line is the same width as the
Russian line.
