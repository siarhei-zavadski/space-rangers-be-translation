#!/usr/bin/env python3
"""Generate, validate, and consume the game-structured Crowdin corpus."""

from collections import Counter
import argparse
import csv
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from rangers.dat import DAT
from rangers.pkg import PKG
from rangers.qm import QuestObj
from rangers.std.buffer import IBuffer, OBuffer

from robots_storage import encode as encode_robots
from robots_storage import encode_raw as encode_robots_raw
from robots_storage import parse as parse_robots
from robots_storage import replace_array


PROJECT = Path(__file__).parent
GAME = Path.home() / ".local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
SOURCE_DAT = GAME / "CFG/Rus/Lang.dat"
ENGLISH_DAT = GAME / "CFG/Eng/Lang.dat"
MOD_DAT = GAME / "Mods/Tweaks/BelTranslate/CFG/Rus/Lang.dat"
CROWDIN = PROJECT / "crowdin"
LANG_DIR = CROWDIN / "lang_dat"
QUEST_DIR = CROWDIN / "quests"
ASSET_DIR = CROWDIN / "assets"
ROBOTS_DIR = CROWDIN / "robots"
COVERAGE = CROWDIN / "coverage.json"
FIELDS = ("identifier", "source_phrase", "context", "labels", "be")
CONTROL = re.compile(r"<[^<>]+>|\{[^{}]*\}|\[p\d+\]|\r\n|\r|\n")
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

# Crowdin stores the words; build metadata maps those words back to GI assets.
ASSETS = {
    ("FormMain2", "New"): ("НОВАЯ ИГРА", "НОВАЯ ГУЛЬНЯ", "button"),
    ("FormMain2", "Load"): ("ЗАГРУЗИТЬ", "ЗАГРУЗІЦЬ", "button"),
    ("FormMain2", "Exit"): ("ВЫХОД", "ВЫЙСЬЦІ", "button"),
    ("FormMain2", "Settings"): ("НАСТРОЙКИ", "НАЛАДЫ", "button"),
    ("FormMain2", "Records"): ("РЕКОРДЫ", "РЭКОРДЫ", "button"),
    ("FormMain2", "About"): ("ОБ АВТОРАХ", "ПРА АЎТАРАЎ", "button"),
    ("FormMain3", "Ach"): ("ДОСТИЖЕНИЯ", "ДАСЯГНЕНЬНІ", "button"),
    ("FormMain3", "2Caption"): ("КОСМИЧЕСКИЕ РЕЙНДЖЕРЫ HD", "", "deferred"),
    ("FormMain3", "CaptionLarge"): ("КОСМИЧЕСКИЕ РЕЙНДЖЕРЫ HD", "", "deferred"),
    ("FormMain3", "CaptionBlur"): ("КОСМИЧЕСКИЕ РЕЙНДЖЕРЫ HD", "", "deferred"),
    ("FormMain3", "2CaptionLine"): ("КОСМИЧЕСКИЕ РЕЙНДЖЕРЫ HD", "", "deferred"),
    ("FormMain3", "Sub"): (
        "ДОМИНАТОРЫ: ПЕРЕЗАГРУЗКА",
        "ДАМІНАТАРЫ: ПЕРАЗАГРУЗКА",
        "deferred",
    ),
    ("FormMain3", "SubLarge"): (
        "ДОМИНАТОРЫ: ПЕРЕЗАГРУЗКА",
        "ДАМІНАТАРЫ: ПЕРАЗАГРУЗКА",
        "deferred",
    ),
    ("FormMain3", "2SubLarge"): (
        "ДОМИНАТОРЫ: ПЕРЕЗАГРУЗКА",
        "ДАМІНАТАРЫ: ПЕРАЗАГРУЗКА",
        "deferred",
    ),
    ("FormMenu2", "Achievements"): ("ДОСТИЖЕНИЯ", "ДАСЯГНЕНЬНІ", "deferred"),
    ("FormLoad3", "LoadAnim"): ("ЗАГРУЗКА", "ЗАГРУЗКА", "deferred"),
    ("FormAbout2", "SubName"): (
        "ДОМИНАТОРЫ: ПЕРЕЗАГРУЗКА",
        "ДАМІНАТАРЫ: ПЕРАЗАГРУЗКА",
        "deferred",
    ),
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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, dialect="excel-tab")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: expected TSV columns {FIELDS}")
        return list(reader)


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, dialect="excel-tab", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def corpus_files() -> list[Path]:
    return sorted((
        *LANG_DIR.glob("*.tsv"),
        *QUEST_DIR.glob("*.tsv"),
        *ASSET_DIR.glob("*.tsv"),
        *ROBOTS_DIR.glob("*.tsv"),
    ))


def existing_translations() -> dict[str, str]:
    paths = corpus_files()
    result = {}
    for path in paths:
        for row in read_rows(path):
            target = row["be"]
            if not target:
                continue
            old = result.setdefault(row["identifier"], target)
            if old != target:
                raise ValueError(f"Conflicting translations for {row['identifier']}")
    return result


def termbase_translations() -> dict[str, str]:
    path = PROJECT / "TERMBASE.tsv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as stream:
        return {
            pointer(tuple(row["id"].split("."))): row["be_tarask"]
            for row in csv.DictReader(stream, dialect="excel-tab")
            if row["id"] and row["be_tarask"]
        }


def clean_generated(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.tsv"):
        path.unlink()


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
    translations_by_id: dict[str, str],
) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
    english_values = dict(iter_strings(english))
    by_section: dict[str, list[dict[str, str]]] = {}
    coverage = []
    for path, source in iter_strings(russian):
        identifier = pointer(path)
        reference = english_values.get(path)
        reason = exclusion_reason(path, source, reference, translations_by_id.keys())
        coverage.append({
            "kind": "lang_dat",
            "identifier": identifier,
            "status": "excluded" if reason else "translatable",
            "reason": reason,
        })
        if reason:
            continue
        context = f"Lang.dat: {'.'.join(path)}. Preserve every <tag> exactly."
        if reference is not None and reference != source:
            context += f" English reference: {reference}"
        by_section.setdefault(path[0], []).append({
            "identifier": identifier,
            "source_phrase": source,
            "context": context,
            "labels": path[0],
            "be": translations_by_id.get(identifier, ""),
        })
    return by_section, coverage


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


def quest_rows(
    translations_by_id: dict[str, str],
) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
    by_quest = {}
    coverage = []
    writer_checked = False
    with TemporaryDirectory() as rus_tmp, TemporaryDirectory() as eng_tmp:
        russian = unpack_quests(GAME / "DATA/questsRus.pkg", Path(rus_tmp))
        english = {
            name.removesuffix("_eng.qmm") + ".qmm": path
            for name, path in unpack_quests(GAME / "DATA/questsEng.pkg", Path(eng_tmp)).items()
        }
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
            english_data = parse_quest(english[name].read_bytes()) if name in english else None
            english_values = dict(iter_quest_text(english_data)) if english_data else {}
            rows = []
            for field_path, source in iter_quest_text(data):
                identifier = pointer(("quests", name, *field_path))
                reason = None if source else "empty text field"
                coverage.append({
                    "kind": "quest",
                    "identifier": identifier,
                    "status": "excluded" if reason else "translatable",
                    "reason": reason,
                })
                if reason:
                    continue
                reference = english_values.get(field_path)
                context = f"Quest {name}: {'.'.join(field_path)}. Preserve every <tag> exactly."
                if reference is not None and reference != source:
                    context += f" English reference: {reference}"
                rows.append({
                    "identifier": identifier,
                    "source_phrase": source,
                    "context": context,
                    "labels": f"quest,{Path(name).stem}",
                    "be": translations_by_id.get(identifier, ""),
                })
            by_quest[name] = rows
    return by_quest, coverage


def asset_rows(translations_by_id: dict[str, str]) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
    by_form = {}
    coverage = []
    for (form, stem), (source, seed, renderer) in ASSETS.items():
        identifier = pointer(("assets", form, stem))
        by_form.setdefault(form, []).append({
            "identifier": identifier,
            "source_phrase": source,
            "context": f"Baked GI label: Data/{form}/{stem}. Renderer: {renderer}.",
            "labels": f"asset,{form}",
            "be": translations_by_id.get(identifier, seed),
        })
        coverage.append({
            "kind": "asset",
            "identifier": identifier,
            "status": "translatable",
            "reason": None,
            "renderer": renderer,
        })
    return by_form, coverage


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


def robot_rows(translations_by_id: dict[str, str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    source_data = (GAME / "CFG/Rus/robots.dat").read_bytes()
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
    _, english = parse_robots((GAME / "CFG/Eng/robots.dat").read_bytes())
    english_values = {
        (record, index): value for record, index, _, value in robot_properties(english)
    }
    rows = []
    coverage = []
    for record, index, key, source in robot_properties(russian):
        identifier = pointer(("robots", record, str(index)))
        reference = english_values.get((record, index))
        reason = exclusion_reason(("robots", record, key), source, reference, translations_by_id.keys())
        coverage.append({
            "kind": "robots_dat",
            "identifier": identifier,
            "status": "excluded" if reason else "translatable",
            "reason": reason,
        })
        if reason:
            continue
        context = f"robots.dat record {record}, property {key}. Preserve every <tag> exactly."
        if reference is not None and reference != source:
            context += f" English reference: {reference}"
        rows.append({
            "identifier": identifier,
            "source_phrase": source,
            "context": context,
            "labels": "robots.dat",
            "be": translations_by_id.get(identifier, ""),
        })
    return rows, coverage


def refresh() -> None:
    existing = existing_translations()
    existing.update({key: value for key, value in termbase_translations().items() if key not in existing})
    if MOD_DAT.exists():
        source = DAT.from_dat(SOURCE_DAT).to_dict()
        patched = DAT.from_dat(MOD_DAT).to_dict()
        for path, value in iter_strings(patched):
            original = value_at(source, path)
            if value != original:
                existing.setdefault(pointer(path), value)

    russian = DAT.from_dat(SOURCE_DAT).to_dict()
    english = DAT.from_dat(ENGLISH_DAT).to_dict()
    dat, dat_coverage = dat_rows(russian, english, existing)
    quests, quest_coverage = quest_rows(existing)
    assets, asset_coverage = asset_rows(existing)
    robots, robots_coverage = robot_rows(existing)

    for directory in (LANG_DIR, QUEST_DIR, ASSET_DIR, ROBOTS_DIR):
        clean_generated(directory)
    for section, rows in dat.items():
        write_rows(LANG_DIR / f"{section}.tsv", rows)
    for name, rows in quests.items():
        write_rows(QUEST_DIR / f"{name}.tsv", rows)
    for form, rows in assets.items():
        write_rows(ASSET_DIR / f"{form}.tsv", rows)
    write_rows(ROBOTS_DIR / "robots.tsv", robots)

    coverage = {
        "version": 1,
        "sources": {
            "lang_dat": "CFG/Rus/Lang.dat",
            "quests": "DATA/questsRus.pkg",
            "robots_dat": "CFG/Rus/robots.dat",
        },
        "summary": {
            "lang_dat_values": len(dat_coverage),
            "lang_dat_translatable": sum(row["status"] == "translatable" for row in dat_coverage),
            "quest_text_fields": len(quest_coverage),
            "quest_translatable": sum(row["status"] == "translatable" for row in quest_coverage),
            "asset_labels": len(asset_coverage),
            "robots_values": len(robots_coverage),
            "robots_translatable": sum(row["status"] == "translatable" for row in robots_coverage),
        },
        "entries": [*dat_coverage, *quest_coverage, *asset_coverage, *robots_coverage],
    }
    COVERAGE.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {sum(map(len, dat.values()))} DAT strings in {len(dat)} files, "
        f"{sum(map(len, quests.values()))} quest strings in {len(quests)} files, "
        f"{sum(map(len, assets.values()))} asset labels in {len(assets)} files, "
        f"and {len(robots)} robots.dat strings"
    )
    check()


def all_rows() -> list[tuple[Path, dict[str, str]]]:
    return [(path, row) for path in corpus_files() for row in read_rows(path)]


def translations() -> dict[tuple[str, ...], str]:
    result = {}
    for path in LANG_DIR.glob("*.tsv"):
        for row in read_rows(path):
            if row["be"]:
                key = unpointer(row["identifier"])
                if key in result:
                    raise ValueError(f"Duplicate identifier {row['identifier']}")
                result[key] = row["be"]
    return result


def asset_translations() -> dict[tuple[str, str], str]:
    result = {}
    for path in ASSET_DIR.glob("*.tsv"):
        for row in read_rows(path):
            if row["be"]:
                parts = unpointer(row["identifier"])
                result[(parts[1], parts[2])] = row["be"]
    return result


def write_translated_quests(destination: Path) -> int:
    targets = {}
    for path in QUEST_DIR.glob("*.tsv"):
        for row in read_rows(path):
            if row["be"]:
                parts = unpointer(row["identifier"])
                targets.setdefault(parts[1], {})[parts[2:]] = row["be"]
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


def write_translated_robots(destination: Path) -> int:
    rows = read_rows(ROBOTS_DIR / "robots.tsv")
    targets = {
        (parts[1], int(parts[2])): row["be"]
        for row in rows
        if row["be"] and (parts := unpointer(row["identifier"]))
    }
    source = (GAME / "CFG/Rus/robots.dat").read_bytes()
    if not targets:
        destination.write_bytes(source)
        return 0
    _, records = parse_robots(source)
    by_name = {record.name: record for record in records}
    for (record_name, index), target in targets.items():
        item = next(item for item in by_name[record_name].items if item.name == "1")
        replace_array(item, index, target)
    encoded = encode_robots(records)
    _, reparsed = parse_robots(encoded)
    values = {
        (record, index): value for record, index, _, value in robot_properties(reparsed)
    }
    assert all(values[key] == target for key, target in targets.items())
    destination.write_bytes(encoded)
    return len(targets)


def validate_tags(source: str, target: str, location: str) -> None:
    if Counter(CONTROL.findall(source)) != Counter(CONTROL.findall(target)):
        raise ValueError(f"{location}: placeholders or control syntax differ")


def check() -> None:
    files = corpus_files()
    if not files:
        raise FileNotFoundError("No split Crowdin files; run refresh")
    russian = DAT.from_dat(SOURCE_DAT).to_dict()
    english = DAT.from_dat(ENGLISH_DAT).to_dict()
    expected_dat, _ = dat_rows(russian, english, existing_translations())
    expected_dat_ids = {row["identifier"] for rows in expected_dat.values() for row in rows}
    expected_assets = {pointer(("assets", form, stem)) for form, stem in ASSETS}

    seen = set()
    actual_dat_ids = set()
    actual_quest_ids = set()
    actual_asset_ids = set()
    actual_robot_ids = set()
    translated = 0
    for file, row in all_rows():
        identifier = row["identifier"]
        if identifier in seen:
            raise ValueError(f"{file}: duplicate identifier {identifier}")
        seen.add(identifier)
        parts = unpointer(identifier)
        target = row["be"]
        if parts[0] == "quests":
            actual_quest_ids.add(identifier)
        elif parts[0] == "assets":
            actual_asset_ids.add(identifier)
            source = ASSETS[(parts[1], parts[2])][0]
            if source != row["source_phrase"]:
                raise ValueError(f"{file}: stale asset source {identifier}")
        elif parts[0] == "robots":
            actual_robot_ids.add(identifier)
        else:
            actual_dat_ids.add(identifier)
            try:
                source = value_at(russian, parts)
            except (IndexError, KeyError, TypeError) as error:
                raise ValueError(f"{file}: unknown DAT identifier {identifier}") from error
            if source != row["source_phrase"]:
                raise ValueError(f"{file}: stale Russian source {identifier}")
        if target:
            translated += 1
            validate_tags(row["source_phrase"], target, f"{file}:{identifier}")

    if actual_dat_ids != expected_dat_ids:
        raise ValueError("Split DAT corpus does not match classified source paths; run refresh")
    if actual_asset_ids != expected_assets:
        raise ValueError("Asset corpus does not match known labels; run refresh")

    _, quest_coverage = quest_rows(existing_translations())
    expected_quest_ids = {
        row["identifier"] for row in quest_coverage if row["status"] == "translatable"
    }
    if actual_quest_ids != expected_quest_ids:
        raise ValueError("Quest corpus does not match QMM text fields; run refresh")

    expected_robots, _ = robot_rows(existing_translations())
    expected_robot_ids = {row["identifier"] for row in expected_robots}
    if actual_robot_ids != expected_robot_ids:
        raise ValueError("robots.dat corpus does not match Storage values; run refresh")
    robot_source = {
        pointer(("robots", record, str(index))): value
        for record, index, _, value in robot_properties(
            parse_robots((GAME / "CFG/Rus/robots.dat").read_bytes())[1]
        )
    }
    for file in ROBOTS_DIR.glob("*.tsv"):
        for row in read_rows(file):
            if robot_source[row["identifier"]] != row["source_phrase"]:
                raise ValueError(f"{file}: stale robots.dat source {row['identifier']}")

    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    coverage_ids = {
        kind: {
            row["identifier"] for row in coverage["entries"] if row["kind"] == kind
        }
        for kind in ("lang_dat", "quest", "asset", "robots_dat")
    }
    all_dat_ids = {pointer(path) for path, _ in iter_strings(russian)}
    if coverage_ids["lang_dat"] != all_dat_ids:
        raise ValueError("coverage.json does not account for every Lang.dat value")
    if coverage_ids["quest"] != {
        row["identifier"] for row in quest_coverage
    }:
        raise ValueError("coverage.json does not account for every QMM text field")
    if coverage_ids["asset"] != expected_assets:
        raise ValueError("coverage.json does not account for every known asset label")
    if coverage_ids["robots_dat"] != {
        row["identifier"] for row in robot_rows(existing_translations())[1]
    }:
        raise ValueError("coverage.json does not account for every robots.dat property")
    print(f"Valid: {translated}/{len(seen)} translated strings in {len(files)} Crowdin files")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("refresh", "check"))
    args = parser.parse_args()
    refresh() if args.command == "refresh" else check()


if __name__ == "__main__":
    main()
