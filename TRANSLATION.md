# Translation plan — classical Belarusian, one line at a time

There is no Cursor skill that makes the agent a Belarusian translator.
The job is this file plus the tools the repo already runs.

Standing order: translate meaning from the Russian line, check the English
line, write classical Belarusian (`be-tarask`).
Reuse a locked term. Do not invent a second pipeline.

## Tools, in this order

1. `TERMBASE.tsv` — if the lemma is already there, copy `be_tarask` exactly.
2. [Starnik](https://starnik.by) — sense, lemma, endings for this UI.
   Skarnik only when the Russian-to-Belarusian sense is still unclear.
3. `hunspell -d be_BY@tarask` through `spell_check.py`.
   Spelling clash: hunspell wins. Meaning clash: Starnik wins.
   Record the new lemma in `TERMBASE.tsv` (sense, endings, rejected calque, Starnik URL).
4. `validate_corpus.py` — JSON shape, empty values, tarask slips, and locked
   termbase rows. CI runs it.
5. `qa_translation.py` — numbers, `<format>` cell widths, tarask slips
   (`з'яв-` is `зьяв-`, `вашая` is `ваша`), and rejected termbase forms in any
   row not listed in `qa_baseline.txt`. Needs the game. See "LLM batches".
6. `corpus_data.py check` — corpus ids and `<tags>`, `{…}`, `[pN]` against the
   game's Russian, that Russian against the `v1-first-pass` tag, and the quest
   round-trip. Needs the game.
7. `build_test_mod.py` — only when the line is on a screen the build already ships.

`STYLE.md` is the language rules (including the orthography lock). Edit the values in
`corpus/`; that tree is the source of truth. Formulas are not in the corpus
(`formula`, `expression`, `formula_to_pass` in `corpus_data.py`). Leave them
alone.

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

The current Belarusian keeps those first letters (`А В Е З М Р С`).
`Звер` is spelled `Зьвер`, which still contains `З В Е Р`. Do not “correct”
`Арес` to `Арэс`, and do not let `Ептимат` start with `Э`. Either change
drops the letter the diary names, while the quest still accepts only the
original jump.

**`Feipsycho.qmm`** (filled; letters, digits and `<fix>` kept). Three separate gates:

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

**`Piratesnest.qmm`** (filled). The wardrobe password is not typed. The NPC
says a URL and the jump text is the same URL. Both copies stayed identical:
`gns://pelengessa.peleng/`, `gns://bombinhome.maloc/`,
`gns://riaskaportal.peleng/`, and the same host tokens
`createbomb`, `hammerthor`.

**`Easywork.qmm`** (filled). One status line is a letter grid,
`. а б в г`, over digits taken from `[p25]`–`[p28]`. Those four letters
stayed. The order tables lower in the same file are ordinary fixed-width
bills; they were translated.

**`Prison.qmm`** / **`PirateClanPrison.qmm`** (filled). Cockroach-race
status lines are letter tracks: `Я` (`Янычар`), `Р` (`Рысак`), `П`
(`Пэнчэкрак`), `Т` (`Тамерлан`). Keep those four initials and the grid
cells; renaming a racer so it starts with another letter breaks the track.

**`Kidnapped.qmm`**, location `210` (filled; the three tokens kept). Not a gate. The coin at the
end of the quest is a Vigenère easter egg. Leave these three tokens
unchanged: `VIGENERE`, `kiiltgjtfjph kqxwzr`, `virsle`. With key `virsle`
the longer string decrypts to “particolored pigeon”. Translate the
paragraph around them.

**`GLAVRED.qmm`** (filled). Not a gate. A newspaper joke expands `КВМ` as
`КіВі Ем` and names the prize `КІВІМ`. The abbreviation still equals the
expansion, so the joke is translated.

### Diagrams — the picture is the puzzle

Leave the drawing. Translate a label only when that line stays the same
width as the Russian line.

| Quest | What is stored | State |
|---|---|---|
| `Maze.qmm` | Corridor map of `#`, `^`, `\|` inside `<fix>` | filled; the maps were copied byte-identical |
| `Logic.qmm` | Grids `[ ]`, `[0]`, `[+]` | filled, grids intact |
| `Codebox.qmm` | Two keypads. Header was `Ключ` / `Образец`; digits come from `[p2]`–`[p5]` and `{n}` | filled; `Образец` is `Узор` padded back to 7 columns so the label sits on the sample grid |
| `Bomber.qmm` | Grid rows `A`–`E` in `<format=center, 40>` | filled; the Latin letters stayed, and the Cyrillic `А` stayed where the Russian cell used it |
| `Pilot.qmm` | Track `I . . o I`; the ticket price table in `<fix>` keeps its Russian column headers | filled |
| `Player.qmm` | 3×3 cells `1`–`9` | filled, grid intact |
| `Doomino.qmm` | Domino faces `[p40]<clr>=<clrEnd>[p41]` | filled; do not edit inside the brackets |
| `Edelweiss.qmm` | Badge number, one digit per cell, from `[p20]` | filled |
| `Testing.qmm` | Magic square `1`–`9` summing to 15 | filled; the digits stayed, and the square buttons stayed `5-9` and `1-4` |
| `Xenolog.qmm` | Tiny map with `o` inside `<fix>` | filled; the `o` map is unchanged |
| `Elus.qmm` | Attribute grid. Widths are the Russian words: `<format=left,8>Большой</format><format=left,7>Синий</format><format=left,5>Круг</format>`, and the same for `Малый`, `Желтый`, `Ромб` | filled; a longer word smashes the columns and the logic puzzle cannot be read |
| `Shashki.qmm` | Checker cells `Б` and `Ч` (white / black) | filled; those two letters stayed, keep them |
| `Domoclan.qmm` | Machine line `ACCESS CARD; ID = 2111; OBJECT = LAB; … NAME = Аакси-Тоон` | filled; the tokens and the id stayed identical |

`Losthero.qmm` is filled. The cabin code stayed `195449`.
`Testing.qmm` is filled. The magic-square digits `1`–`9` summing to 15 stayed, and the square buttons stayed `5-9` and `1-4`.
`Evidence.qmm`, `Sibolusovt.qmm`, and `Disk.qmm` teach a code in one line
and confirm it with a jump. Translate the sentence; the code characters
on both sides stay the same. `Disk.qmm` is filled. `Evidence.qmm` is filled;
`[p30]`, `[p31]`, `[p32]`, `[p1]`, `[p46]`, and the star masks stayed.
`Sibolusovt.qmm` is filled. The code characters stayed on the teaching line
and on the jump. The digit jumps stayed `Набраць 5`, `Набраць 10`,
`Набраць 20`, `Набраць 50`, `Набраць 100`, and `Набраць 200`. The lock
buttons stayed `0`–`5`. The cards kept `<clr>код - 504<clrEnd>` and
`<clr>код-325<clrEnd>`.

The same width trap, without being a puzzle, sits in `Election.qmm`,
`Rvk.qmm`, `Ski.qmm`, `Amnesia.qmm`, `SpaceLines.qmm`, `Olympiada.qmm`,
`Proprolog.qmm`, `Kiberrazum.qmm`, and `Colonization.qmm`: a
`<format=left,N>` or `<format=center,N>` cell clips when the Belarusian
word is longer than `N`.

Lines that only mention a puzzle (`головоломка`, a shipment, a failed guess
such as Mafia’s `Пассворд` / `Parol`) are ordinary prose.

**`Drugs.qmm`** (filled). Two locks, both already translated.

- The cipher the player enters stays `16, 13, 18, 1, 17, 30`. Those numbers are the Russian alphabet with ё, and they spell `Пароль`. The status line stays `Пароль: Пароль`. The Belarusian alphabet would yield a different letter.
- Door signs: `Два разумнікі`, `Чалавечае дзіцянё`, `Трое сяброў` with `казлоў` painted over `сяброў`, `Выхад`, `Малок, які выбухае`. The combined jump is `Трое сяброў-казлоў`. Suspects stay крамнік `Х-Люп`, прыбіральнік `Гразія`, кухар `Ці-На`.
- Locations `138.0` and `138.1` are the binary-lock diagram. The `{…}` formulas stay byte-identical. The suffix `[p11]<clr>-ю<clrEnd>` stays. The labels are `Табло` (5) and `Бакавая кнопка` (14, the same width as `Боковая кнопка`). The label line is 102 characters.

## Order of work

The first pass is done. The recheck (phase 6) goes machine-found problems
first, then files:

1. Sources translated more than one way, and rows equal to the Russian
   (minus proper-name paths). `qa_translation.py` reports both.
2. `qa_baseline.txt` rejected-form rows: fix the Belarusian and delete the id
   from the file; never add rows.
3. `TERMBASE.tsv` debt (duplicate `ru` keys, weak `source` values).
4. UI (`corpus/lang_dat/`), then narrative sections, then quests. Puzzle
   files last. Read a puzzle's section above before editing; keep the frozen
   tokens named there in place.

Rhythm: one batch (~50 unique sources) is one commit. Resume with
`--after <last id>` from the previous batch's stderr. Branch
`cursor/<file>-<suffix>`.

## LLM batches

One batch is one file, about 50 unique sources (owner's machine; needs the game):

```bash
.venv/bin/python qa_translation.py --review Moi.qmm -n 50   # input
# model edits the values in corpus/quests/Moi.qmm.json
python3 qa_translation.py --fix                            # tarask slips
.venv/bin/python qa_translation.py                         # hard checks, must print 0 failures
PYTHONPATH=. .venv/bin/python spell_check.py --file Moi --gate
# next batch: --review Moi.qmm -n 50 --after '<last id from stderr>'
```

- Translate a repeated label once (`Отмена` was `Скасаваць` in 20 rows and
  `Адмена` in 7); `qa_translation.py` reports every source translated more
  than one way.
- Never ask the model to count or renumber (`Gluki.qmm` `1 колба` once came
  back as `2 колбы`); `qa_translation.py` fails on a swapped digit.
- `qa_baseline.txt` holds rejected-form rows that predate the check. Fix a
  row and delete it from the file; never add rows. A real new exception goes
  into `TERMBASE.tsv` instead.
- `spell_check.py --gate` fails on any token not in `spell_allow.txt`. A hit
  is a question, not a patch: hunspell lacks some correct forms (`аб'екта`,
  genitive of a concrete noun, is fine). Check the form in Starnik and the
  sense in the Russian line before changing it; run `--accept` only for words
  that survive that, and review the diff. `SLIPS` in `validate_corpus.py`
  holds spelling rules that are true in every context, nothing else.

## Known LLM mistakes — read before the first batch

Each one happened in this corpus. `qa_translation.py` catches the ones marked
(auto); the rest only a careful read catches.

1. **Russian shapes in tarask spelling (auto for the first two).** Prefix
   `з-`/`с-` softens before я, е, ё, ю, і: `зьявіўся`, `зьяўляецца`, not
   `з'явіўся`. Apostrophe stays after other prefixes and labials:
   `аб'ява`, `пад'езд`, `п'еса`, `сур'ёзны`. `ваша`/`вашу`, not `вашая`/`вашую`.
   Verbal nouns take `-ньне`/`-ньня` (`дасягненьне`), not `-нне` (`паскарэнне`,
   `устаранення` slipped through; `начынне`, `ванне` are real words).
2. **Changed numbers (auto).** A model asked to "translate" `1 колба`, `2 колбы`
   returned `2 колбы`, `3 колбы`, so every flask count in `Gluki.qmm` was off by one.
   Digits, `[pN]`, `{…}` and `<tags>` are copied, never recomputed.
3. **Cell overflow (auto).** `<format=left,27> Прыбытак за ўчорашні дзень:` is 28
   characters with its leading space and clips. Count the whole cell, spaces
   included, against `N`.
4. **Same label, different words (report).**
   `Отмена` was `Скасаваць` in 20 rows and `Адмена` in 7. Reuse the existing
   translation of an identical source.
5. **Rejected termbase forms (auto, against `qa_baseline.txt`).** `група`
   (`гурт`), `клян` (`клан`), `супернік` (`праціўнік`), `спадарожнік` (`папутнік`),
   `бруд` (`гразь`). `TERMBASE.tsv` lists the accepted form.
6. **Russian left in the cell (report).** `Броня корпуса: <bonHull> ед.` was
   copied unchanged into 19 `MicroModuls` rows. Proper names in `ShipName`,
   `PlanetName`, `Star`, `RuinName` and `Constellations` may stay Cyrillic;
   sentences and unit words may not. A joke built on broken Russian (`Pilot.qmm`
   `тибя чериз полчиса`) is translated by imitating the same kind of mistake in
   Belarusian, not left in Russian.
7. **Hunspell is not grammar.** It lacks correct forms (`аб'екта`, genitive of
   a concrete noun, is right) and proposes wrong ones. A hit means "look",
   never "replace". Form and endings: Starnik. Sense: the Russian line and
   the English line. Only a rule that is true in every context goes
   into `SLIPS`.
8. **Starnik from a shell.** `https://starnik.by/pravapis/<id>` is a static
   page showing the headword with its endings (`клан, -а`); the `TERMBASE.tsv`
   `source` column has such links. The search box runs in JavaScript, so
   `curl …?search=` returns nothing: use a browser tool, or an id already
   in `TERMBASE.tsv`.
9. **Editing the JSON.** Each file is one `"identifier": "Belarusian"` pair
   per line. A line break inside a string is the escape `\r\n` or `\n`; keep
   the one the line already has. Edit the value in place, or through
   `load`/`save` in `validate_corpus.py`; a different JSON writer reflows the
   whole file. (In the old TSVs, the wrong row terminator once turned a
   32-row change into a 454-line diff.) After any bulk edit, `git diff --stat`
   must match the rows you meant to touch, and
   `git diff --word-diff=porcelain --word-diff-regex='[^[:space:]]+'` must
   show only the intended tokens.
10. **Keep the puzzle table honest.** An old "empty" label once hid finished
    files (`Feipsycho`, `Kidnapped`, `Pilot`, and later `Doomino` /
    `Edelweiss` / `Elus`). `validate_corpus.py` rejects an empty value, so no
    file is partly translated; update the table in the same commit that
    finishes a file.
