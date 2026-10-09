#!/usr/bin/env python3
"""Build the player patcher zip (scripts + corpus + font; no game binaries)."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
PREFIX = "beltranslate"
FORBIDDEN = re.compile(r"\.(dat|gi|pkg|qmm|aft)$", re.I)

# Root files shipped to players. No translation tooling, no hunspell, no game files.
ROOT_FILES = (
    "INSTALL.md",
    "LICENSE",
    "THIRD_PARTY.md",
    "requirements-local.txt",
    "TERMBASE.tsv",
    "install.py",
    "build_test_mod.py",
    "corpus_data.py",
    "aft_font.py",
    "robots_storage.py",
    "validate_corpus.py",
)


def version() -> str:
    for key in ("VERSION", "GITHUB_REF_NAME"):
        if value := os.environ.get(key):
            return value.removeprefix("refs/tags/")
    result = subprocess.run(
        ["git", "-C", str(ROOT), "describe", "--tags", "--always"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout.strip() or "dev").removeprefix("refs/tags/")


def members() -> list[tuple[Path, str]]:
    """Local path → archive name under beltranslate/."""
    out: list[tuple[Path, str]] = []
    for name in ROOT_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        out.append((path, f"{PREFIX}/{name}"))
    for path in sorted((ROOT / "corpus").rglob("*.json")):
        out.append((path, f"{PREFIX}/{path.relative_to(ROOT).as_posix()}"))
    for name in ("RussoOne-Regular.ttf", "OFL-RussoOne.txt"):
        path = ROOT / "tools/fonts" / name
        if not path.is_file():
            raise FileNotFoundError(path)
        out.append((path, f"{PREFIX}/tools/fonts/{name}"))
    for path, arc in out:
        if FORBIDDEN.search(path.name):
            raise ValueError(f"refusing to pack game binary: {path}")
        if ".." in Path(arc).parts:
            raise ValueError(arc)
    return out


def pack(destination: Path | None = None) -> Path:
    ver = version()
    destination = destination or (DIST / f"beltranslate-patcher-{ver}.zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = members()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, arc in files:
            archive.write(path, arcname=arc)
        names = set(archive.namelist())
    assert f"{PREFIX}/install.py" in names
    assert f"{PREFIX}/corpus/robots/robots.json" in names
    assert f"{PREFIX}/tools/fonts/RussoOne-Regular.ttf" in names
    assert not any(FORBIDDEN.search(name) for name in names)
    print(f"Wrote {destination} ({len(files)} files)")
    return destination


def main() -> None:
    pack()


if __name__ == "__main__":
    main()
