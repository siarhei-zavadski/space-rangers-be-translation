#!/usr/bin/env python3
"""Both ends of an LLM translation batch, stdlib only (CI runs it).

  --batch FILE [-n N]  the next N untranslated *unique* sources of FILE, with
                       English reference and the termbase rows they mention
  --fix                after the batch: repair tarask slips, then copy a
                       translation to every empty row with the same source
  (default)            hard checks, exit 1: a digit swapped for another digit,
                       a `<format=..,N>` cell that overflows, a tarask slip, a
                       rejected termbase form in a row not in qa_baseline.txt,
                       a TERMBASE.tsv row with no be_tarask or source
  --baseline           accept every rejected-form row that exists today

Reports (never fail): sources translated more than one way.
"""

import argparse
import csv
from collections import Counter, defaultdict
import re
import sys

from validate_corpus import CONTROL, CORPUS, CORPUS_DIRS, FIELDS, ROOT, read_rows

CELL = re.compile(r"<format=(?:left|center|right),(\d+)>(.*?)</format>", re.S)
SLIPS = (  # always wrong in be-tarask (hunspell rejects them; the prefix softens)
    (re.compile(r"(?<![А-Яа-яЁёІіЎў'])([зЗ])'(?=[яеёюі])"), r"\1ь"),
    (re.compile(r"\b([Вв])ашая\b"), r"\1аша"),
    (re.compile(r"\b([Вв])ашую\b"), r"\1ашу"),
)
LETTERS = "а-яёіўА-ЯЁІЎ'’"
BASELINE = ROOT / "qa_baseline.txt"


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


def termbase() -> list[tuple[re.Pattern, dict[str, str], list[re.Pattern]]]:
    """(Russian-stem pattern, row, rejected-form patterns) per single-word lemma."""
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
            stem = ru[:-1] if len(ru) > 5 else ru
            result.append((
                re.compile(rf"(?<![{LETTERS}]){re.escape(stem)}", re.I),
                t,
                [re.compile(rf"(?<![{LETTERS}]){re.escape(b)}[{LETTERS}]{{0,2}}(?![{LETTERS}])", re.I) for b in bad],
            ))
    return result


def save(path, rows) -> None:
    eol = "\r\n" if path.read_bytes().split(b"\n", 1)[0].endswith(b"\r") else "\n"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, dialect="excel-tab", lineterminator=eol, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def batch(files, needle: str, n: int) -> None:
    terms = termbase()
    guide = (ROOT / "TRANSLATION.md").read_text(encoding="utf-8").splitlines()
    for path in files:
        stem = path.name.removesuffix(".tsv")
        if needle.lower() in path.name.lower():
            for line in (l for l in guide if f"`{stem}`" in l):
                print(f"PUZZLE (read its section in TRANSLATION.md): {line.strip()[:160]}", file=sys.stderr)
    seen: dict[str, list[str]] = {}
    for path, rs in files.items():
        if needle.lower() in path.name.lower():
            for r in rs:
                if not r["be"]:
                    seen.setdefault(r["source_phrase"], []).append(r)
    for source, rs in list(seen.items())[:n]:
        english = rs[0]["context"].partition("English reference: ")[2]
        hints = [
            f"{t['ru']}={t['be_tarask']}" + (f" (not {t['rejected_calque']})" if t["rejected_calque"] else "")
            for ru, t, _ in terms
            if ru.search(source)
        ]
        print("\t".join([rs[0]["identifier"], str(len(rs)), source, english, "; ".join(hints)]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--batch", metavar="FILE", help="substring of a TSV name, e.g. Moi.qmm")
    parser.add_argument("-n", type=int, default=50, help="sources per batch")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--limit", type=int, default=10, help="examples per report")
    args = parser.parse_args()

    files = {p: read_rows(p) for d in CORPUS_DIRS for p in sorted((CORPUS / d).glob("*.tsv"))}
    if args.batch:
        batch(files, args.batch, args.n)
        return 0

    if args.fix:
        variants = defaultdict(set)
        for rs in files.values():
            for r in rs:
                if r["be"]:
                    variants[r["source_phrase"]].add(r["be"])
        slips = filled = 0
        for path, rs in files.items():
            dirty = False
            for r in rs:
                fixed = r["be"]
                for pattern, repl in SLIPS:
                    fixed = pattern.sub(repl, fixed)
                if fixed != r["be"]:
                    slips += 1
                if not fixed and len(variants[r["source_phrase"]]) == 1:
                    (fixed,) = variants[r["source_phrase"]]
                    filled += 1
                if fixed != r["be"]:
                    r["be"], dirty = fixed, True
            if dirty:
                save(path, rs)
        print(f"fixed {slips} spelling slips, filled {filled} empty rows from identical sources")

    rows = [r for rs in files.values() for r in rs]
    done = [r for r in rows if r["be"]]
    failures = [(r["identifier"], e) for r in done for e in check(r)]

    rejected: dict[str, str] = {}
    for ru, t, bad in termbase():
        if bad:
            for r in done:
                if ru.search(r["source_phrase"]) and any(b.search(r["be"]) for b in bad):
                    rejected.setdefault(r["identifier"], f"{t['ru']} -> {t['be_tarask'][:20]} (not {t['rejected_calque']})")
    if args.baseline:
        BASELINE.write_text("".join(f"{i}\n" for i in sorted(rejected)), encoding="utf-8")
        print(f"baseline: {len(rejected)} rows")
        return 0
    with (ROOT / "TERMBASE.tsv").open(encoding="utf-8", newline="") as stream:
        failures += [
            (t["id"], "termbase row without be_tarask or source (lemma not locked)")
            for t in csv.DictReader(stream, dialect="excel-tab")
            if not t["be_tarask"].strip() or not t["source"].strip()
        ]
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
    empty = {r["source_phrase"] for r in rows if not r["be"]}
    print(f"report: {len(empty)} unique sources remain untranslated")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
