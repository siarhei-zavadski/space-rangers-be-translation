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
5. `qa_translation.py` — numbers, `<format>` cell widths, tarask slips
   (`з'яв-` is `зьяв-`, `вашая` is `ваша`), and rejected termbase forms in any
   row not listed in `qa_baseline.txt`. Fails CI. See "LLM batches".
6. `corpus_data.py check` — corpus ids, source text, and quest round-trip.
7. `build_test_mod.py` — only when the line is on a screen the build already ships.

`STYLE.md` and `ORTHO.md` are the language rules. Edit the `be` cell in
`corpus/`; that tree is the source of truth. Formulas are not in the TSV
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

The current `be` column keeps those first letters (`А В Е З М Р С`).
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

**`Piratesnest.qmm`** (empty). The wardrobe password is not typed. The NPC
says a URL and the jump text is the same URL. Keep both copies identical:
`gns://pelengessa.peleng/`, `gns://bombinhome.maloc/`,
`gns://riaskaportal.peleng/`, and the same host tokens
`createbomb`, `hammerthor`.

**`Easywork.qmm`** (empty). One status line is a letter grid,
`. а б в г`, over digits taken from `[p25]`–`[p28]`. Those four letters
are the alphabet the player reads. Leave them. The order tables lower in
the same file are ordinary fixed-width bills (see below).

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
| `Maze.qmm` | Corridor map of `#`, `^`, `\|` inside `<fix>` | empty |
| `Logic.qmm` | Grids `[ ]`, `[0]`, `[+]` | filled, grids intact |
| `Codebox.qmm` | Two keypads. Header was `Ключ` / `Образец`; digits come from `[p2]`–`[p5]` and `{n}` | filled; `Образец` is `Узор` padded back to 7 columns so the label sits on the sample grid |
| `Bomber.qmm` | Grid rows `A`–`E` in `<format=center, 40>` | filled; the Latin letters stayed, and the Cyrillic `А` stayed where the Russian cell used it |
| `Pilot.qmm` | Track `I . . o I`; the ticket price table in `<fix>` keeps its Russian column headers | filled |
| `Player.qmm` | 3×3 cells `1`–`9` | filled, grid intact |
| `Doomino.qmm` | Domino faces `[p40]<clr>=<clrEnd>[p41]` | empty; do not edit inside the brackets |
| `Edelweiss.qmm` | Badge number, one digit per cell, from `[p20]` | empty |
| `Testing.qmm` | Magic square `1`–`9` summing to 15 | empty; keep the digits, flavor text is free |
| `Xenolog.qmm` | Tiny map with `o` inside `<fix>` | filled; the `o` map is unchanged |
| `Elus.qmm` | Attribute grid. Widths are the Russian words: `<format=left,8>Большой</format><format=left,7>Синий</format><format=left,5>Круг</format>`, and the same for `Малый`, `Желтый`, `Ромб` | empty; a longer word smashes the columns and the logic puzzle cannot be read |
| `Shashki.qmm` | Checker cells `Б` and `Ч` (white / black) | filled; those two letters stayed, keep them |
| `Domoclan.qmm` | Machine line `ACCESS CARD; ID = 2111; OBJECT = LAB; … NAME = Аакси-Тоон` | empty; keep the tokens and the id |

`Losthero.qmm` shows the cabin code `195449` in prose. Keep the digits.
`Evidence.qmm`, `Sibolusovt.qmm`, and `Disk.qmm` teach a code in one line
and confirm it with a jump. Translate the sentence; the code characters
on both sides stay the same. `Disk.qmm` is filled. `Evidence.qmm` is filled;
`[p30]`, `[p31]`, `[p32]`, `[p1]`, `[p46]`, and the star masks stayed.

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

`validate_corpus.py` lists the incomplete files. Take them in this order,
one file at a time, until its `--batch` prints nothing:

1. Ordinary quests: `Prison`, `PirateClanPrison`, `Moi`, `Mafia` (filled), `Drugs` (filled).
2. Width-sensitive quests (`<format=..,N>` cells; `qa_translation.py` fails
   on overflow): `Amnesia` (filled), `Colonization` (filled), `Rvk` (filled), `Proprolog` (filled), `Kiberrazum` (filled).
3. Puzzle files, smallest first: `Elus` (filled), `Edelweiss` (filled), `Doomino` (filled), `Bomber` (filled),
   `Xenolog` (filled), `Evidence` (filled), `GLAVRED` (filled), `Maze`, `Easywork`, `Sibolusovt`,
   `Losthero`, `Testing`, `Piratesnest`, `Domoclan`. `--batch` prints the
   puzzle's table row to stderr; read its whole section above first, and
   edit every copy of a name (diary, statue, jump) in the same batch.

Rhythm: one batch (default 50 unique sources, at most 150) is one commit,
pushed straight away. Open a draft PR after the first commit of a file and
keep adding to it until the file is done. Branch `cursor/<file>-<suffix>`.

Before a puzzle file is called done: tags still match
(`validate_corpus.py`), and every `<fix>` line is the same width as the
Russian line.

## LLM batches

One batch is one file, about 50 unique sources:

```bash
python3 qa_translation.py --batch Moi.qmm -n 50   # input for the model
# model writes the be cells into corpus/quests/Moi.qmm.tsv
python3 qa_translation.py --fix                   # tarask slips + copy to rows with the same source
python3 qa_translation.py                         # hard checks, must print 0 failures
PYTHONPATH=. .venv/bin/python spell_check.py --file Moi --gate
```

- `--batch` prints `identifier, rows sharing it, ru, English reference,
  termbase hints` for each *unique* source, so a repeated label is
  translated once (`Отмена` was `Скасаваць` in 20 rows and `Адмена` in 7).
  Give the model those lines, not the whole `TERMBASE.tsv`.
- Never ask the model to count or renumber (`Gluki.qmm` `1 колба` once came
  back as `2 колбы`); `qa_translation.py` fails on a swapped digit.
- `qa_baseline.txt` holds rejected-form rows that predate the check. Fix a
  row and delete it from the file; never add rows. A real new exception goes
  into `TERMBASE.tsv` instead.
- `spell_check.py --gate` fails on any token not in `spell_allow.txt`. A hit
  is a question, not a patch: hunspell lacks some correct forms (`аб'екта`,
  genitive of a concrete noun, is fine). Check the form in Starnik and the
  sense in the Russian line before changing it; run `--accept` only for words
  that survive that, and review the diff. `SLIPS` in `qa_translation.py`
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
4. **Same label, different words (auto: `--fix` copies, the report lists).**
   `Отмена` was `Скасаваць` in 20 rows and `Адмена` in 7. Reuse the existing
   translation of an identical source; `--batch` already shows each source once.
5. **Rejected termbase forms (auto, against `qa_baseline.txt`).** `група`
   (`гурт`), `клян` (`клан`), `супернік` (`праціўнік`), `спадарожнік` (`папутнік`),
   `бруд` (`гразь`). The hints printed by `--batch` list the accepted form.
6. **Russian left in the cell (report).** `Броня корпуса: <bonHull> ед.` was
   copied unchanged into 19 `MicroModuls` rows. Proper names in `ShipName`,
   `PlanetName`, `Star`, `RuinName` and `Constellations` may stay Cyrillic;
   sentences and unit words may not. A joke built on broken Russian (`Pilot.qmm`
   `тибя чериз полчиса`) is translated by imitating the same kind of mistake in
   Belarusian, not left in Russian.
7. **Hunspell is not grammar.** It lacks correct forms (`аб'екта`, genitive of
   a concrete noun, is right) and proposes wrong ones. A hit means "look",
   never "replace". Form and endings: Starnik. Sense: the Russian line and
   the English `context`. Only a rule that is true in every context goes
   into `SLIPS`.
8. **Starnik from a shell.** `https://starnik.by/pravapis/<id>` is a static
   page showing the headword with its endings (`клан, -а`); the `TERMBASE.tsv`
   `source` column has such links. The search box runs in JavaScript, so
   `curl …?search=` returns nothing: use a browser tool, or an id already
   in `TERMBASE.tsv`.
9. **Editing the TSVs.** Rows are quoted with `QUOTE_ALL`, and a file uses
   either `\n` or `\r\n` for row ends (some files hold both inside cells).
   Rewriting one with the wrong terminator once produced a 454-line diff for
   a 32-row change. Edit through `read_rows`/`save` in `qa_translation.py`, or
   change the cell text in place. After any bulk edit, `git diff --stat` must
   match the rows you meant to touch, and
   `git diff --word-diff=porcelain --word-diff-regex='[^[:space:]]+'` must
   show only the intended tokens.
10. **Do not trust a first-pass "unused" or "empty" label.** `TRANSLATION.md`
    called Feipsycho, Kidnapped and Pilot "empty" while they were 100%
    translated. `validate_corpus.py` shows the real counts; update the puzzle
    table in the same commit that finishes a file.
