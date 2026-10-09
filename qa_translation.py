#!/usr/bin/env python3
"""Check the Belarusian against the game's Russian.

  --review FILE [-n N] [--after ID]
                       next N unique Russian sources of FILE (needs the game
                       and .venv). Prints id, row count, Russian, English,
                       current be, termbase hints, and other be variants for
                       the same source. --after resumes after that id.
  --fix                repair tarask slips in place (needs no game)
  (default)            hard checks, exit 1: a digit swapped for another digit,
                       a `<format=..,N>` cell that overflows, a tarask slip, a
                       rejected termbase form in a row not in qa_baseline.txt

Reports (never fail): sources translated more than one way, and rows where
`be` is the Russian source copied unchanged (names stay Cyrillic on purpose).
The default run and --review read the Russian from the game, so they need the
game and `.venv`.
"""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys

from validate_corpus import CONTROL, ROOT, SLIPS, corpus_files, load, save

CELL = re.compile(r"<format=(?:left|center|right),(\d+)>(.*?)</format>", re.S)
LETTERS = "а-яёіўА-ЯЁІЎ'’"
BASELINE = ROOT / "qa_baseline.txt"
NAMES = ("/ShipName/", "/PlanetName/", "/Star/", "/RuinName/", "/Constellations/")


def visible(text: str) -> int:
    return len(CONTROL.sub("", text))


def digits(text: str) -> Counter:
    return Counter(re.findall(r"\d+", CONTROL.sub(" ", text)))


def check(row: dict[str, str]) -> list[str]:
    src, be = row["source_phrase"], row["be"]
    errors = []
    s, b = digits(src), digits(be)
    # ponytail: ordinals ("1-й") and spelled-out numbers are legitimate, so only
    # flag a digit swapped for a different digit (Gluki "1 колба" -> "2 колбы").
    if b and s and not s.keys() <= b.keys() and not b.keys() <= s.keys() and not re.search(r"\d-", src):
        errors.append(f"number {sorted(s)} -> {sorted(b)}")
    cells_s, cells_b = CELL.findall(src), CELL.findall(be)
    if len(cells_s) == len(cells_b):
        for (n, a), (_, z) in zip(cells_s, cells_b):
            if visible(z) > int(n) >= visible(a):
                errors.append(f"cell {n} overflows: {z!r}")
    for pattern, _ in SLIPS:
        if pattern.search(be):
            errors.append(f"spelling slip: {pattern.search(be).group(0)!r}")
    return errors


def termbase_rejects() -> list[tuple[str, str, list[re.Pattern]]]:
    """(Russian stem, failure label, rejected-form patterns) per lemma with rejects."""
    result = []
    with (ROOT / "TERMBASE.tsv").open(encoding="utf-8", newline="") as stream:
        for t in csv.DictReader(stream, dialect="excel-tab"):
            ru = t["ru"].strip().lower()
            if len(ru) < 4 or " " in ru:
                continue
            accepted = [a.strip().lower() for a in t["be_tarask"].split("/") if a.strip()]
            bad = [
                x.strip().lower()
                for x in re.split(r"[/;,]", t["rejected_calque"])
                if len(x.strip()) >= 4 and " " not in x.strip()
                and not any(x.strip().lower() in a or a in x.strip().lower() for a in accepted)
            ]
            if not bad:
                continue
            stem = ru[:-1] if len(ru) > 5 else ru
            result.append((
                stem,
                f"{t['ru']} -> {t['be_tarask'][:20]} (not {t['rejected_calque']})",
                [re.compile(rf"(?<![{LETTERS}]){re.escape(b)}[{LETTERS}]{{0,2}}(?![{LETTERS}])", re.I) for b in bad],
            ))
    return result


def termbase_hint_rows() -> list[tuple[re.Pattern, str]]:
    """(Russian-stem regex, hint text) for --review."""
    result = []
    with (ROOT / "TERMBASE.tsv").open(encoding="utf-8", newline="") as stream:
        for t in csv.DictReader(stream, dialect="excel-tab"):
            ru = t["ru"].strip().lower()
            if len(ru) < 4 or " " in ru:
                continue
            stem = ru[:-1] if len(ru) > 5 else ru
            label = f"{t['ru']}={t['be_tarask']}"
            if t["rejected_calque"].strip():
                label += f" (not {t['rejected_calque']})"
            result.append((re.compile(rf"(?<![{LETTERS}]){re.escape(stem)}", re.I), label))
    return result


def rejected_forms(rows: list[dict[str, str]]) -> dict[str, str]:
    """One pass per row: skip stems absent as substrings, then the same regex as before."""
    entries = termbase_rejects()
    rejected: dict[str, str] = {}
    for row in rows:
        src = row["source_phrase"]
        src_fold = src.casefold()
        be = row["be"]
        for stem, label, bad in entries:
            if stem not in src_fold:
                continue
            if not re.search(rf"(?<![{LETTERS}]){re.escape(stem)}", src, re.I):
                continue
            if any(pattern.search(be) for pattern in bad):
                rejected.setdefault(row["identifier"], label)
    return rejected


def fix(text: str) -> str:
    for pattern, repl in SLIPS:
        text = pattern.sub(repl, text)
    return text


def resolve_corpus_file(needle: str) -> Path:
    needle_l = needle.lower().removesuffix(".json")
    matches = [path for path in corpus_files() if needle_l in path.name.lower()]
    exact = [
        path for path in matches
        if path.name.lower() in {needle_l, f"{needle_l}.json"}
        or path.stem.lower() == needle_l
    ]
    if len(exact) == 1:
        return exact[0]
    if len(matches) == 1:
        return matches[0]
    names = [path.relative_to(ROOT / "corpus").as_posix() for path in matches]
    raise SystemExit(f"need exactly one corpus file matching {needle!r}, got {names}")


def review(needle: str, n: int, *, after: str = "") -> int:
    from corpus_data import corpus, game_rows, quest_english, translations_by_id, unpointer

    path = resolve_corpus_file(needle)
    key = path.relative_to(ROOT / "corpus").as_posix()
    rows_by_path = game_rows(translations_by_id(corpus()))
    rows = rows_by_path.get(path)
    if rows is None:
        raise SystemExit(f"{key}: no game rows (ids do not match the game?)")

    if path.parent.name == "quests":
        english = quest_english(path.name.removesuffix(".json"))
        for row in rows:
            parts = unpointer(row["identifier"])
            # /quests/Name.qmm/...
            field = tuple(parts[2:])
            row["english"] = english.get(field) or row.get("english") or ""

    all_be = defaultdict(Counter)
    for rs in rows_by_path.values():
        for row in rs:
            if row["be"]:
                all_be[row["source_phrase"]][row["be"]] += 1

    by_source: dict[str, list[dict[str, str]]] = {}
    order: list[str] = []
    for row in rows:
        source = row["source_phrase"]
        if source not in by_source:
            by_source[source] = []
            order.append(source)
        by_source[source].append(row)

    if after:
        try:
            start = next(
                i for i, source in enumerate(order)
                if any(r["identifier"] == after for r in by_source[source])
            ) + 1
        except StopIteration:
            raise SystemExit(f"{key}: --after id not in file: {after}") from None
    else:
        start = 0

    hints = termbase_hint_rows()
    batch = order[start : start + n]
    if not batch:
        print(f"{key}: review complete ({len(order)} unique sources)", file=sys.stderr)
        return 0

    print(f"PUZZLE: see TRANSLATION.md for {path.name}", file=sys.stderr)
    last_id = after
    for source in batch:
        group = by_source[source]
        first = group[0]
        last_id = first["identifier"]
        hint = "; ".join(label for pattern, label in hints if pattern.search(source))
        others = [
            f"{be!r}×{count}"
            for be, count in all_be[source].most_common()
            if be != first["be"]
        ]
        print(
            "\t".join([
                first["identifier"],
                str(len(group)),
                source.replace("\t", " ").replace("\n", "\\n").replace("\r", "\\r"),
                (first.get("english") or "").replace("\t", " ").replace("\n", "\\n").replace("\r", "\\r"),
                first["be"].replace("\t", " ").replace("\n", "\\n").replace("\r", "\\r"),
                hint,
                "; ".join(others),
            ])
        )

    print(
        f"next: --after {last_id!r} ({start + len(batch)}/{len(order)} unique sources)",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--review", metavar="FILE", help="substring of a corpus file name, e.g. Moi.qmm")
    parser.add_argument("-n", type=int, default=50, help="unique sources per --review batch")
    parser.add_argument("--after", metavar="ID", default="", help="with --review: start after this identifier")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--limit", type=int, default=10, help="examples per report")
    args = parser.parse_args()

    if args.review:
        return review(args.review, args.n, after=args.after)

    if args.fix:
        slips = 0
        for path in corpus_files():
            data = load(path)
            fixed = {identifier: fix(be) for identifier, be in data.items()}
            changed = sum(fixed[identifier] != be for identifier, be in data.items())
            if changed:
                save(path, fixed)
                slips += changed
        print(f"fixed {slips} spelling slips")
        return 0

    # Imported here: CI imports this module for check() and has no game or rangers.
    from corpus_data import corpus, game_rows, translations_by_id

    done = [r for rs in game_rows(translations_by_id(corpus())).values() for r in rs if r["be"]]
    failures = [(r["identifier"], e) for r in done for e in check(r)]

    rejected = rejected_forms(done)
    known = set(BASELINE.read_text(encoding="utf-8").split()) if BASELINE.exists() else set()
    failures += [(i, f"rejected form: {label}") for i, label in rejected.items() if i not in known]

    for identifier, error in failures[: args.limit * 3]:
        print(f"FAIL {identifier}: {error}")
    print(f"hard failures: {len(failures)} ({len(known & rejected.keys())} baselined rejected-form rows)")

    variants = defaultdict(Counter)
    for r in done:
        variants[r["source_phrase"]][r["be"]] += 1
    conflicts = {s: v for s, v in variants.items() if len(v) > 1}
    print(f"report: {len(conflicts)} sources translated more than one way")
    for s, v in list(conflicts.items())[: args.limit]:
        print(f"  {s[:50]!r}: {[(b[:35], n) for b, n in v.most_common()]}")
    copied = [
        r for r in done
        if r["be"] == r["source_phrase"] and not r["identifier"].startswith(NAMES)
        and len(re.findall(r"[а-яё]{3,}", r["source_phrase"])) >= 2
    ]
    print(f"report: {len(copied)} rows are the Russian source copied unchanged")
    for r in copied[: args.limit]:
        print(f"  {r['identifier']}: {r['be'][:60]!r}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
