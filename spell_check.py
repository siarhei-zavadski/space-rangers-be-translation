#!/usr/bin/env python3
"""Spell-check every filled Crowdin `be` cell with local be_BY@tarask hunspell.

One hunspell process on unique tokens. Tags, formulas, and Latin are stripped.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from collections import Counter
from pathlib import Path

from crowdin_sync import CONTROL, PROJECT, all_rows

DICT = "be_BY@tarask"
WORD = re.compile(r"[А-Яа-яЁёІіЎўҐґ']+", re.UNICODE)
SKIP = {"cr", "CR"}


def tokenize(text: str) -> list[str]:
    cleaned = CONTROL.sub(" ", text)
    return [w for w in WORD.findall(cleaned) if w not in SKIP]


def termbase_words() -> set[str]:
    path = PROJECT / "TERMBASE.tsv"
    if not path.exists():
        return set()
    words: set[str] = set()
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, dialect="excel-tab"):
            for part in (row.get("be_tarask") or "").split("/"):
                words.update(tokenize(part))
    return words


def hunspell_miss(words: list[str]) -> set[str]:
    if not words:
        return set()
    proc = subprocess.run(
        ["hunspell", "-d", DICT, "-l"],
        input="\n".join(words) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="substring of TSV path (e.g. Ski, Quest.tsv)")
    parser.add_argument("--top", type=int, default=80, help="leftover rows to print")
    parser.add_argument(
        "--keep-termbase",
        action="store_true",
        help="do not drop tokens already in TERMBASE.tsv",
    )
    args = parser.parse_args()
    needle = (args.file or "").lower()

    counts: Counter[str] = Counter()
    sample: dict[str, str] = {}
    strings = 0
    for path, row in all_rows():
        be = (row.get("be") or "").strip()
        if not be:
            continue
        if needle and needle not in str(path).lower():
            continue
        strings += 1
        loc = f"{path.name}:{row['identifier']}"
        for word in tokenize(be):
            counts[word] += 1
            sample.setdefault(word, loc)

    unique = sorted(counts)
    bad = hunspell_miss(unique)
    if not args.keep_termbase:
        bad -= termbase_words()

    leftover = [(counts[w], w, sample[w]) for w in bad]
    leftover.sort(key=lambda row: (-row[0], row[1].casefold()))
    hits = sum(n for n, _, _ in leftover)
    print(
        f"Checked {strings} strings, {len(unique)} unique tokens, "
        f"{len(leftover)} leftover types, {hits} leftover hits ({DICT})"
    )
    for n, word, loc in leftover[: args.top]:
        print(f"{n:6}\t{word}\t{loc}")
    if len(leftover) > args.top:
        print(f"... {len(leftover) - args.top} more")


if __name__ == "__main__":
    main()
