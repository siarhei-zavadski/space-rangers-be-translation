#!/usr/bin/env python3
"""Check the corpus against the installed game, and feed it to the build."""

from collections import Counter, defaultdict
import argparse
import csv
import io
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

from rangers.dat import DAT
from rangers.pkg import PKG
from rangers.qm import QuestObj
from rangers.std.buffer import IBuffer, OBuffer

from robots_storage import encode as encode_robots
from robots_storage import encode_raw as encode_robots_raw
from robots_storage import parse as parse_robots
from robots_storage import replace_array
from validate_corpus import CONTROL, CORPUS, ROOT as PROJECT, corpus_files, load


DEFAULT_GAME = Path.home() / ".local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
GAME = DEFAULT_GAME
SOURCE_DAT = GAME / "CFG/Rus/Lang.dat"
ENGLISH_DAT = GAME / "CFG/Eng/Lang.dat"
LANG_DIR = CORPUS / "lang_dat"
QUEST_DIR = CORPUS / "quests"
ASSET_DIR = CORPUS / "assets"
ROBOTS_DIR = CORPUS / "robots"
TAG = "v1-first-pass"


def configure_game(path: Path | str | None = None) -> Path:
    """Point GAME (and the Lang.dat paths) at an installed copy of the game."""
    global GAME, SOURCE_DAT, ENGLISH_DAT
    GAME = Path(path).expanduser().resolve() if path else DEFAULT_GAME
    SOURCE_DAT = GAME / "CFG/Rus/Lang.dat"
    ENGLISH_DAT = GAME / "CFG/Eng/Lang.dat"
    return GAME
RUSSIAN = re.compile(r"[А-Яа-яЁё]")
RESOURCE = re.compile(
    r"(?i)^[^<>\r\n]+\.(?:aft|dat|gi|jpg|map|mp3|ogg|pkg|png|qmm|scr|tga|txt|wav)$"
)
NON_TEXT_KEYS = {
    "code", "expression", "filename", "file", "formula", "formula_to_pass",
    "image", "img", "map", "model", "onusecode", "picture", "sound",
    "start_value", "text_select_formula", "texture", "track",
}
QUEST_TEXT_KEYS = {
    "content", "crit_text", "description", "name", "success_text",
    "task_text", "text", "unknown_text",
}
QUEST_LITERAL_KEYS = {
    "tostar": "<ToStar>",
    "toplanet": "<ToPlanet>",
    "fromplanet": "<FromPlanet>",
    "fromstar": "<FromStar>",
    "ranger": "<Ranger>",
}

# Baked GI labels in the corpus, and how the build renders each one.
ASSETS = {
    ("FormMain2", "New"): "button",
    ("FormMain2", "Load"): "button",
    ("FormMain2", "Exit"): "button",
    ("FormMain2", "Settings"): "button",
    ("FormMain2", "Records"): "button",
    ("FormMain2", "About"): "button",
    ("FormMain3", "Ach"): "button",
    ("FormMain3", "2Caption"): "deferred",
    ("FormMain3", "CaptionLarge"): "deferred",
    ("FormMain3", "CaptionBlur"): "deferred",
    ("FormMain3", "2CaptionLine"): "deferred",
    ("FormMain3", "Sub"): "deferred",
    ("FormMain3", "SubLarge"): "deferred",
    ("FormMain3", "2SubLarge"): "deferred",
    ("FormMenu2", "Achievements"): "deferred",
    ("FormLoad3", "LoadAnim"): "deferred",
    ("FormAbout2", "SubName"): "deferred",
}


def pointer(parts: tuple[str, ...]) -> str:
    return "/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in parts)


def unpointer(value: str) -> tuple[str, ...]:
    if not value.startswith("/"):
        raise ValueError(f"Invalid path: {value!r}")
    return tuple(part.replace("~1", "/").replace("~0", "~") for part in value[1:].split("/"))


def iter_strings(value, path: tuple[str, ...] = ()):
    children = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else ()
    for key, value in children:
        child_path = (*path, str(key))
        if isinstance(value, (dict, list)):
            yield from iter_strings(value, child_path)
        elif isinstance(value, str):
            yield child_path, value


def child(value, part: str):
    return value[int(part)] if isinstance(value, list) else value[part]


def value_at(value, path: tuple[str, ...]):
    for part in path:
        value = child(value, part)
    return value


def set_value(value, path: tuple[str, ...], replacement: str) -> None:
    for part in path[:-1]:
        value = child(value, part)
    key = int(path[-1]) if isinstance(value, list) else path[-1]
    value[key] = replacement


def corpus() -> dict[Path, dict[str, str]]:
    return {path: load(path) for path in corpus_files()}


def translations_by_id(files: dict[Path, dict[str, str]]) -> dict[str, str]:
    result = {}
    for path, values in files.items():
        for identifier, target in values.items():
            if identifier in result:
                raise ValueError(f"{path}: duplicate identifier {identifier}")
            result[identifier] = target
    return result


def exclusion_reason(
    path: tuple[str, ...],
    source: str,
    english: str | None,
    translated_ids: set[str],
) -> str | None:
    if pointer(path) in translated_ids:
        return None
    terminal = path[-1].lower()
    if terminal in NON_TEXT_KEYS:
        return f"internal {terminal} field"
    if not source:
        return "empty value"
    if source.startswith(("http://", "https://")):
        return "URL"
    if RESOURCE.fullmatch(source.strip()):
        return "resource path"
    if RUSSIAN.search(source):
        return None
    if english is not None and english != source:
        return None
    return "no Russian text or localization evidence"


def dat_rows(
    russian: dict,
    english: dict,
    translations: dict[str, str],
) -> dict[str, list[dict[str, str]]]:
    english_values = dict(iter_strings(english))
    by_section: dict[str, list[dict[str, str]]] = {}
    for path, source in iter_strings(russian):
        if exclusion_reason(path, source, english_values.get(path), translations.keys()):
            continue
        identifier = pointer(path)
        by_section.setdefault(path[0], []).append({
            "identifier": identifier,
            "source_phrase": source,
            "be": translations.get(identifier, ""),
        })
    return by_section


def parse_quest(raw: bytes) -> dict:
    return QuestObj.read_with_memo(IBuffer(raw))


def encode_quest(data: dict) -> bytes:
    output = OBuffer()
    QuestObj.write_with_memo(output, data)
    return bytes(output)


def iter_quest_text(value, path: tuple[str, ...] = (), key: str | None = None):
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            yield from iter_quest_text(child_value, (*path, str(child_key)), str(child_key))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from iter_quest_text(child_value, (*path, str(index)), key)
    elif isinstance(value, str) and (
        key in QUEST_TEXT_KEYS
        or key in QUEST_LITERAL_KEYS and value != QUEST_LITERAL_KEYS[key]
    ):
        yield path, value


def unpack_quests(package: Path, destination: Path) -> dict[str, Path]:
    PKG.from_file(package).to_folder(destination)
    return {path.name: path for path in destination.rglob("*.qmm")}


def quest_rows(translations: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    by_quest = {}
    writer_checked = False
    with TemporaryDirectory() as rus_tmp:
        russian = unpack_quests(GAME / "DATA/questsRus.pkg", Path(rus_tmp))
        for name, path in sorted(russian.items()):
            raw = path.read_bytes()
            data = parse_quest(raw)
            assert encode_quest(data) == raw, f"Non-identical QMM no-op round-trip: {name}"
            if not writer_checked:
                first_path, first_value = next(
                    (field_path, value)
                    for field_path, value in iter_quest_text(data)
                    if value
                )
                changed = parse_quest(raw)
                set_value(changed, first_path, first_value + " ")
                reparsed = parse_quest(encode_quest(changed))
                assert value_at(reparsed, first_path) == first_value + " "
                writer_checked = True
            rows = []
            for field_path, source in iter_quest_text(data):
                if not source:
                    continue
                identifier = pointer(("quests", name, *field_path))
                rows.append({
                    "identifier": identifier,
                    "source_phrase": source,
                    "be": translations.get(identifier, ""),
                })
            by_quest[name] = rows
    return by_quest


def robot_properties(records):
    for record in records:
        items = {item.name: item for item in record.items}
        keys = items.get("0")
        values = items.get("1")
        if not keys or not values or keys.arrays is None or values.arrays is None:
            continue
        if len(keys.arrays) != len(values.arrays):
            raise ValueError(f"robots.dat record {record.name}: property key/value count differs")
        for index, (key, value) in enumerate(zip(keys.arrays, values.arrays)):
            yield record.name, index, key, value


def robots_dat(lang: str) -> Path:
    """Vanilla robots.dat for lang (Eng/Rus). Prefer *.vanilla after the build patches CFG."""
    vanilla = GAME / f"CFG/{lang}/robots.dat.vanilla"
    if vanilla.exists():
        return vanilla
    return GAME / f"CFG/{lang}/robots.dat"


def robot_rows(translations: dict[str, str]) -> list[dict[str, str]]:
    source_data = robots_dat("Rus").read_bytes()
    russian_raw, russian = parse_robots(source_data)
    assert encode_robots_raw(russian) == russian_raw, "robots.dat raw no-op round-trip differs"
    _, changed = parse_robots(source_data)
    first_record, first_index, _, first_value = next(robot_properties(changed))
    first_item = next(item for item in next(
        record for record in changed if record.name == first_record
    ).items if item.name == "1")
    replace_array(first_item, first_index, first_value + " ")
    _, reparsed = parse_robots(encode_robots(changed))
    assert next(
        value for record, index, _, value in robot_properties(reparsed)
        if (record, index) == (first_record, first_index)
    ) == first_value + " "
    _, english = parse_robots(robots_dat("Eng").read_bytes())
    english_values = {
        (record, index): value for record, index, _, value in robot_properties(english)
    }
    rows = []
    for record, index, key, source in robot_properties(russian):
        identifier = pointer(("robots", record, str(index)))
        reference = english_values.get((record, index))
        if exclusion_reason(("robots", record, key), source, reference, translations.keys()):
            continue
        rows.append({
            "identifier": identifier,
            "source_phrase": source,
            "be": translations.get(identifier, ""),
        })
    return rows


def game_rows(translations: dict[str, str]) -> dict[Path, list[dict[str, str]]]:
    """Rows of every corpus file that has game Russian, keyed by the file's path."""
    russian = DAT.from_dat(SOURCE_DAT).to_dict()
    english = DAT.from_dat(ENGLISH_DAT).to_dict()
    rows = {LANG_DIR / f"{section}.json": r for section, r in dat_rows(russian, english, translations).items()}
    rows |= {QUEST_DIR / f"{name}.json": r for name, r in quest_rows(translations).items()}
    rows[ROBOTS_DIR / "robots.json"] = robot_rows(translations)
    return rows


def tag_sources() -> dict[str, str]:
    """The Russian each line was translated from, kept in the TSV corpus at TAG."""
    git = ["git", "-C", str(PROJECT)]
    if subprocess.run([*git, "rev-parse", "-q", "--verify", f"{TAG}^{{commit}}"], capture_output=True).returncode:
        raise SystemExit(f"Tag {TAG} is missing; run git fetch --tags")
    names = subprocess.run(
        [*git, "ls-tree", "-r", "--name-only", TAG, "corpus"], capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    sources = {}
    for name in names:
        if name.endswith(".tsv"):
            raw = subprocess.run([*git, "show", f"{TAG}:{name}"], capture_output=True, check=True).stdout
            for row in csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""), dialect="excel-tab"):
                sources[row["identifier"]] = row["source_phrase"]
    return sources


def translations() -> dict[tuple[str, ...], str]:
    return {
        unpointer(identifier): target
        for path in sorted(LANG_DIR.glob("*.json"))
        for identifier, target in load(path).items()
    }


def asset_translations() -> dict[tuple[str, str], str]:
    return {
        unpointer(identifier)[1:3]: target
        for path in sorted(ASSET_DIR.glob("*.json"))
        for identifier, target in load(path).items()
    }


def write_translated_quests(destination: Path) -> int:
    targets = {}
    for path in sorted(QUEST_DIR.glob("*.json")):
        for identifier, target in load(path).items():
            parts = unpointer(identifier)
            targets.setdefault(parts[1], {})[parts[2:]] = target
    if not targets:
        return 0

    with TemporaryDirectory() as temporary:
        sources = unpack_quests(GAME / "DATA/questsRus.pkg", Path(temporary))
        for name, rows in targets.items():
            source = sources[name]
            data = parse_quest(source.read_bytes())
            for path, target in rows.items():
                set_value(data, path, target)
            encoded = encode_quest(data)
            parse_quest(encoded)
            for language in ("Rus", "Eng"):
                output_name = name if language == "Rus" else f"{Path(name).stem}_eng.qmm"
                output = destination / f"Data/Quest/{language}/{output_name}"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(encoded)
    return len(targets)


def write_translated_robots(cfg_dir: Path) -> int:
    """Write translated robots.dat into the mod and the game CFG folders.

    MatrixGame opens the game install's CFG/{Eng,Rus}/robots.dat directly; a mod
    overlay is ignored (unlike Lang.dat). Keep .vanilla backups beside them.
    Mod copies match German/Spanish (CFG/robots.dat) plus CFG/{Eng,Rus}/.
    """
    targets = {
        (parts[1], int(parts[2])): target
        for identifier, target in load(ROBOTS_DIR / "robots.json").items()
        if (parts := unpointer(identifier))
    }
    eng_vanilla = GAME / "CFG/Eng/robots.dat.vanilla"
    rus_vanilla = GAME / "CFG/Rus/robots.dat.vanilla"
    eng_path = GAME / "CFG/Eng/robots.dat"
    rus_path = GAME / "CFG/Rus/robots.dat"
    if not eng_vanilla.exists():
        shutil.copy2(eng_path, eng_vanilla)
    if not rus_vanilla.exists():
        shutil.copy2(rus_path, rus_vanilla)

    _, russian = parse_robots(rus_vanilla.read_bytes())
    _, english = parse_robots(eng_vanilla.read_bytes())
    key_of = {(record, index): key for record, index, key, _ in robot_properties(russian)}
    ru_order, en_order = defaultdict(list), defaultdict(list)
    for record, index, key, _ in robot_properties(russian):
        ru_order[(record, key)].append(index)
    for record, index, key, _ in robot_properties(english):
        en_order[(record, key)].append(index)
    eng_targets = {}
    for (record, index), target in targets.items():
        key = key_of[(record, index)]
        order = ru_order[(record, key)].index(index)
        if order < len(en_order[(record, key)]):
            eng_targets[(record, en_order[(record, key)][order])] = target

    def encode(source: bytes, by_index: dict[tuple[str, int], str]) -> bytes:
        if not by_index:
            return source
        _, records = parse_robots(source)
        by_name = {record.name: record for record in records}
        for (record_name, index), target in by_index.items():
            item = next(item for item in by_name[record_name].items if item.name == "1")
            replace_array(item, index, target)
        encoded = encode_robots(records)
        _, reparsed = parse_robots(encoded)
        values = {
            (record, index): value for record, index, _, value in robot_properties(reparsed)
        }
        assert all(values[pair] == target for pair, target in by_index.items())
        return encoded

    eng_bytes = encode(eng_vanilla.read_bytes(), eng_targets)
    rus_bytes = encode(rus_vanilla.read_bytes(), targets)
    # Game files MatrixGame actually opens:
    eng_path.write_bytes(eng_bytes)
    rus_path.write_bytes(rus_bytes)
    # Mod tree (same bytes; CFG/robots.dat = Eng layout, like German/Spanish)
    for destination in (cfg_dir / "robots.dat", cfg_dir / "Eng/robots.dat"):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(eng_bytes)
    rus_mod = cfg_dir / "Rus/robots.dat"
    rus_mod.parent.mkdir(parents=True, exist_ok=True)
    rus_mod.write_bytes(rus_bytes)
    return len(targets)


def validate_tags(source: str, target: str, location: str) -> None:
    if Counter(CONTROL.findall(source)) != Counter(CONTROL.findall(target)):
        raise ValueError(f"{location}: placeholders or control syntax differ")


def check() -> None:
    files = corpus()
    if not files:
        raise FileNotFoundError("No corpus files")
    translations = translations_by_id(files)
    rows = game_rows(translations)

    expected = {path: {row["identifier"] for row in r} for path, r in rows.items()}
    for form, stem in ASSETS:
        expected.setdefault(ASSET_DIR / f"{form}.json", set()).add(pointer(("assets", form, stem)))
    for path in sorted(expected.keys() | files.keys()):
        want, have = expected.get(path, set()), set(files.get(path, ()))
        if want != have:
            raise ValueError(
                f"{path.relative_to(PROJECT)} does not match the game's text: "
                f"missing {sorted(want - have)[:5]}, extra {sorted(have - want)[:5]}"
            )

    for path, r in rows.items():
        for row in r:
            validate_tags(row["source_phrase"], row["be"], f"{path.name}:{row['identifier']}")

    tagged = tag_sources()
    stale = [row["identifier"] for r in rows.values() for row in r if tagged.get(row["identifier"]) != row["source_phrase"]]
    if stale:
        raise ValueError(f"{len(stale)} game Russian lines differ from the Russian at {TAG}, e.g. {stale[:5]}")
    print(f"Valid: {len(translations)} translated strings in {len(files)} corpus files; game Russian matches {TAG}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check",))
    parser.add_argument(
        "--game",
        type=Path,
        help=f"game install folder (default: {DEFAULT_GAME})",
    )
    args = parser.parse_args()
    configure_game(args.game)
    check()


if __name__ == "__main__":
    main()
