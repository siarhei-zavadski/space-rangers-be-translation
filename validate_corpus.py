#!/usr/bin/env python3
"""CI-safe checks that do not require an installed copy of the game."""

from collections import Counter
import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
CONTROL = re.compile(r"<[^<>]+>|\{[^{}]*\}|\[p\d+\]|\r\n|\r|\n")
CORPUS_DIRS = ("lang_dat", "quests", "robots", "assets")
SLIPS = (  # always wrong in be-tarask (hunspell rejects them; the prefix softens)
    (re.compile(r"(?<![А-Яа-яЁёІіЎў'])([зЗ])'(?=[яеёюі])"), r"\1ь"),
    (re.compile(r"\b([Вв])ашая\b"), r"\1аша"),
    (re.compile(r"\b([Вв])ашую\b"), r"\1ашу"),
)


def corpus_files() -> list[Path]:
    return sorted(path for directory in CORPUS_DIRS for path in (CORPUS / directory).glob("*.json"))


def _unique(pairs: list[tuple[str, str]]) -> dict[str, str]:
    result = dict(pairs)
    if len(result) != len(pairs):
        repeated = [key for key, count in Counter(key for key, _ in pairs).items() if count > 1]
        raise ValueError(f"duplicate keys {repeated[:5]}")
    return result


def load(path: Path) -> dict[str, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error


def save(path: Path, data: dict[str, str]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0) + "\n", encoding="utf-8", newline="\n")


def head(path: Path) -> list[str]:
    stem = path.name.removesuffix(".json")
    return {"lang_dat": [stem], "quests": ["quests", stem], "robots": ["robots"], "assets": ["assets", stem]}[path.parent.name]


def main() -> None:
    files = corpus_files()
    if not files:
        raise ValueError("No corpus files")

    seen: set[str] = set()
    for path in files:
        prefix = head(path)
        for identifier, be in load(path).items():
            if identifier in seen:
                raise ValueError(f"{path}: duplicate identifier {identifier}")
            seen.add(identifier)
            parts = identifier[1:].split("/")
            if not identifier.startswith("/") or parts[:len(prefix)] != prefix or len(parts) == len(prefix):
                raise ValueError(f"{path}: identifier {identifier!r} does not belong in this file")
            if not isinstance(be, str) or not be.strip():
                raise ValueError(f"{path}: empty translation {identifier}")
            for pattern, _ in SLIPS:
                if slip := pattern.search(be):
                    raise ValueError(f"{path}: tarask slip {slip.group(0)!r} in {identifier}; run qa_translation.py --fix")

    with (ROOT / "TERMBASE.tsv").open(encoding="utf-8", newline="") as stream:
        unlocked = [
            row["id"] for row in csv.DictReader(stream, dialect="excel-tab")
            if not row["be_tarask"].strip() or not row["source"].strip()
        ]
    if unlocked:
        raise ValueError(f"TERMBASE.tsv rows without be_tarask or source (lemma not locked): {unlocked[:10]}")

    puzzles = ROOT / "puzzles.tsv"
    if puzzles.exists():
        by_file = {path.name: path for path in files}
        with puzzles.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream, dialect="excel-tab"):
                name, token = row["file"].strip(), row["token"]
                path = by_file.get(name)
                if path is None:
                    raise ValueError(f"puzzles.tsv: unknown file {name!r}")
                if token not in "\n".join(load(path).values()):
                    raise ValueError(f"puzzles.tsv: {name} is missing frozen token {token!r}")

    print(f"Valid repository corpus: {len(seen)} translations in {len(files)} files")


if __name__ == "__main__":
    main()
