#!/usr/bin/env python3
"""Per-row QA for LLM-written `be` cells that validate_corpus.py does not cover.

Hard checks (exit 1): a number changed to another number, a `<format=..,N>`
cell that no longer fits, and tarask spelling slips that are always wrong.
`--fix` rewrites only the spelling slips. Reports (never fail): repeated
sources that were translated differently, untranslated rows a translation
memory could fill, and termbase `rejected_calque` forms used where the
Russian term is in the source. Stdlib only, so CI can run it.
"""

import argparse
import csv
from collections import Counter, defaultdict
import re

from validate_corpus import CONTROL, CORPUS_DIRS, CROWDIN, FIELDS, ROOT, read_rows

CELL = re.compile(r"<format=(?:left|center|right),(\d+)>(.*?)</format>", re.S)
SLIPS = (  # always wrong in be-tarask (hunspell rejects them; the prefix softens)
    (re.compile(r"(?<![А-Яа-яЁёІіЎў'])([зЗ])'(?=[яеёюі])"), r"\1ь"),
    (re.compile(r"\b([Вв])ашая\b"), r"\1аша"),
    (re.compile(r"\b([Вв])ашую\b"), r"\1ашу"),
)
LETTERS = "а-яёіўА-ЯЁІЎ'’"


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


def rejected_forms() -> list[tuple[re.Pattern, re.Pattern, str]]:
    result = []
    with (ROOT / "TERMBASE.tsv").open(encoding="utf-8", newline="") as stream:
        for t in csv.DictReader(stream, dialect="excel-tab"):
            ru = t["ru"].strip().lower()
            accepted = [a.strip().lower() for a in t["be_tarask"].split("/") if a.strip()]
            if len(ru) < 4 or " " in ru:
                continue
            for bad in (x.strip().lower() for x in re.split(r"[/;,]", t["rejected_calque"])):
                if len(bad) < 4 or " " in bad or any(bad in a or a in bad for a in accepted):
                    continue
                ru_stem = ru[:-1] if len(ru) > 5 else ru
                result.append((
                    re.compile(rf"(?<![{LETTERS}]){re.escape(ru_stem)}", re.I),
                    re.compile(rf"(?<![{LETTERS}]){re.escape(bad)}[{LETTERS}]{{0,2}}(?![{LETTERS}])", re.I),
                    f"{t['ru']} -> {t['be_tarask'][:20]} (not {bad})",
                ))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="rewrite spelling slips in the TSVs")
    parser.add_argument("--limit", type=int, default=10, help="examples per report")
    args = parser.parse_args()

    files = {p: read_rows(p) for d in CORPUS_DIRS for p in sorted((CROWDIN / d).glob("*.tsv"))}
    rows = [r for rs in files.values() for r in rs]
    done = [r for r in rows if r["be"]]

    failures = [(r["identifier"], e) for r in done for e in check(r)]
    for identifier, error in failures[: args.limit * 3]:
        print(f"FAIL {identifier}: {error}")
    print(f"hard failures: {len(failures)}")

    if args.fix:
        changed = 0
        for path, rs in files.items():
            dirty = False
            for r in rs:
                fixed = r["be"]
                for pattern, repl in SLIPS:
                    fixed = pattern.sub(repl, fixed)
                if fixed != r["be"]:
                    r["be"], dirty, changed = fixed, True, changed + 1
            if dirty:
                eol = "\r\n" if path.read_bytes().split(b"\n", 1)[0].endswith(b"\r") else "\n"
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, FIELDS, dialect="excel-tab", lineterminator=eol, quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    writer.writerows(rs)
        print(f"spelling slips fixed in {changed} rows")

    variants = defaultdict(Counter)
    for r in done:
        variants[r["source_phrase"]][r["be"]] += 1
    conflicts = {s: v for s, v in variants.items() if len(v) > 1}
    fillable = [r for r in rows if not r["be"] and len(variants.get(r["source_phrase"], ())) == 1]
    unique_empty = {r["source_phrase"] for r in rows if not r["be"]}
    print(f"report: {len(conflicts)} sources translated more than one way")
    for s, v in list(conflicts.items())[: args.limit]:
        print(f"  {s[:50]!r}: {[(b[:35], n) for b, n in v.most_common()]}")
    print(
        f"report: {len(fillable)} empty rows have a one-way translation elsewhere; "
        f"{len(unique_empty)} unique sources remain untranslated"
    )

    hits: Counter = Counter()
    for ru, bad, label in rejected_forms():
        hits[label] = sum(1 for r in done if ru.search(r["source_phrase"]) and bad.search(r["be"]))
    top = [(n, label) for label, n in hits.most_common() if n]
    print(f"report: {sum(n for n, _ in top)} rows use a rejected termbase form ({len(top)} terms)")
    for n, label in top[: args.limit]:
        print(f"  {n:4} {label}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
