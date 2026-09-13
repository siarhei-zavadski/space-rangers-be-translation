#!/usr/bin/env python3
"""CI-safe checks that do not require an installed copy of the game."""

from collections import Counter
import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).parent
CROWDIN = ROOT / "crowdin"
FIELDS = ("identifier", "source_phrase", "context", "labels", "be")
CONTROL = re.compile(r"<[^<>]+>|\{[^{}]*\}|\[p\d+\]|\r\n|\r|\n")
CORPUS_DIRS = ("lang_dat", "quests", "robots", "assets")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, dialect="excel-tab")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: expected {FIELDS}")
        return list(reader)


def main() -> None:
    files = sorted(path for directory in CORPUS_DIRS for path in (CROWDIN / directory).glob("*.tsv"))
    if not files:
        raise ValueError("No Crowdin corpus files")

    rows = [(path, row) for path in files for row in read_rows(path)]
    ids = [row["identifier"] for _, row in rows]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate identifiers: {duplicates[:10]}")

    for path, row in rows:
        identifier = row["identifier"]
        if not identifier.startswith("/") or not row["source_phrase"] or not row["context"]:
            raise ValueError(f"{path}: incomplete row {identifier!r}")
        if row["be"] and Counter(CONTROL.findall(row["source_phrase"])) != Counter(CONTROL.findall(row["be"])):
            raise ValueError(f"{path}: control syntax differs in {identifier}")

    coverage = json.loads((CROWDIN / "coverage.json").read_text(encoding="utf-8"))
    entries = coverage["entries"]
    coverage_ids = [entry["identifier"] for entry in entries]
    if len(coverage_ids) != len(set(coverage_ids)):
        raise ValueError("Duplicate coverage identifiers")
    expected = {
        entry["identifier"] for entry in entries if entry["status"] == "translatable"
    }
    if set(ids) != expected:
        missing = sorted(expected - set(ids))
        extra = sorted(set(ids) - expected)
        raise ValueError(f"Corpus/coverage mismatch; missing={missing[:5]}, extra={extra[:5]}")
    if any(entry["status"] not in {"translatable", "excluded", "deferred"} for entry in entries):
        raise ValueError("Unknown coverage status")

    report = (ROOT / "TRANSLATION-SCOPE.md").read_text(encoding="utf-8")
    if f"**{len(rows):,}**" not in report or f"**{len(files)}**" not in report:
        raise ValueError("TRANSLATION-SCOPE.md is stale")

    sensitive = re.compile(
        r"CROWDIN_PERSONAL_TOKEN\s*[:=]\s*['\"][A-Za-z0-9_-]{20,}"
        r"|api_token\s*:\s*['\"][^$]"
    )
    for path in (
        *ROOT.glob("*.py"),
        *ROOT.glob("*.md"),
        *ROOT.glob("*.yml"),
        *(ROOT / ".github/workflows").glob("*.yml"),
    ):
        if sensitive.search(path.read_text(encoding="utf-8")):
            raise ValueError(f"Possible committed token in {path}")

    print(
        f"Valid repository corpus: {len(rows)} rows in {len(files)} files; "
        f"{sum(bool(row['be']) for _, row in rows)} translated"
    )


if __name__ == "__main__":
    main()
