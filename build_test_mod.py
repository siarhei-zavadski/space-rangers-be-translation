#!/usr/bin/env python3
"""Build the Belarusian UI translation mod (Lang.dat + menu button GI)."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from PIL import Image, ImageDraw, ImageFont
from rangers.dat import DAT
from rangers.graphics.gi import GI
from rangers.pkg import PKG

from aft_font import glyph_codes, write_patched_fonts
from corpus_data import (
    ASSETS,
    DEFAULT_GAME,
    asset_translations,
    check as check_corpus,
    configure_game,
    set_value,
    translations,
    write_translated_quests,
    write_translated_robots,
)


PROJECT = Path(__file__).parent
FONT = PROJECT / "tools/fonts/RussoOne-Regular.ttf"


def clean_label(image: Image.Image) -> Image.Image:
    """Remove baked Russian label while retaining the button background."""
    image = image.convert("RGBA")
    pixels = image.load()
    # Text occupies this central strip. Interpolation preserves the original
    # red horizontal texture and transparent edge decoration.
    top_y, bottom_y = 5, 39
    for x in range(26, 290):
        top = pixels[x, top_y]
        bottom = pixels[x, bottom_y]
        for y in range(top_y + 1, bottom_y):
            t = (y - top_y) / (bottom_y - top_y)
            pixels[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
    return image


def render_label(image: Image.Image, state: str, text: str) -> Image.Image:
    image = clean_label(image)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 26)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    x = (image.width - (box[2] - box[0])) // 2 - box[0]
    y = (image.height - (box[3] - box[1])) // 2 - box[1] - 1
    fill = (220, 211, 177, 255) if state == "N" else (244, 174, 8, 255)
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 210), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    draw.text((x, y), text, font=font, fill=fill, stroke_width=3, stroke_fill=(12, 12, 8, 255))
    return image


# Vanilla AFT already has ASCII apostrophe. Typographic ’/‘/ʼ would miss.
APOSTROPHE_FOLD = str.maketrans({"\u2019": "'", "\u2018": "'", "\u02bc": "'"})


def patch_dat(source: Path, destination: Path) -> None:
    dat = DAT.from_dat(source)
    values = dat.to_dict()
    for path, translation in translations().items():
        try:
            set_value(values, path, translation.translate(APOSTROPHE_FOLD))
        except (TypeError, IndexError):
            # Eng Lang.dat flattens or shortens a few Rus arrays (BK/Policy/BK, FormAbout.N).
            continue
    DAT.from_dict(values).to_dat(destination, fmt="HDMain", sign=True)


def write_utf16(path: Path, text: str) -> None:
    """UTF-16 LE with BOM and CRLF. newline='' so Windows does not turn \\r\\n into \\r\\r\\n."""
    with path.open("w", encoding="utf-16", newline="") as stream:
        stream.write(text.replace("\n", "\r\n"))


def uninstall(game: Path) -> None:
    """Restore patched game files and remove Mods/Tweaks/BelTranslate."""
    for rel in ("CFG/Eng/robots.dat", "CFG/Rus/robots.dat"):
        path = game / rel
        backup = path.with_name(path.name + ".vanilla")
        if backup.exists():
            shutil.copy2(backup, path)
            print(f"restored {path}")
    forms = game / "DATA/forms.pkg"
    forms_backup = game / "DATA/forms.pkg.vanilla"
    if forms_backup.exists() and forms.exists() and forms.read_bytes() != forms_backup.read_bytes():
        shutil.copy2(forms_backup, forms)
        print(f"restored {forms}")
    mod = game / "Mods/Tweaks/BelTranslate"
    if mod.exists():
        shutil.rmtree(mod)
        print(f"removed {mod}")
    else:
        print(f"no mod at {mod}")


def build(game: Path) -> None:
    mod = game / "Mods/Tweaks/BelTranslate"
    assert FONT.exists(), FONT
    check_corpus()
    source_pkg = game / "DATA/russian.pkg"
    assert source_pkg.exists(), source_pkg

    work = PROJECT / "build"
    if work.exists():
        shutil.rmtree(work)
    preview = work / "preview"
    preview.mkdir(parents=True)
    buttons = {
        key: value
        for key, value in asset_translations().items()
        if ASSETS[key] == "button"
    }

    with TemporaryDirectory() as temporary:
        unpacked = Path(temporary)
        PKG.from_file(source_pkg).to_folder(unpacked)
        for (folder, button), text in buttons.items():
            out_dir = work / "pkg" / "Data" / folder
            out_dir.mkdir(parents=True, exist_ok=True)
            for state in "NAD":
                source = unpacked / f"Data/{folder}/2But{button}{state}.gi"
                original = GI.from_gi(source)
                image = render_label(original.to_image(), state, text)
                image.save(preview / f"{folder}_2But{button}{state}.png")
                # Original assets use format 2 (three layers), 16-bit.
                output = GI.from_image(image, fmt=2, opt=16)
                output.to_gi(out_dir / f"2But{button}{state}.gi")

    # Fonts stay in their own package. Vanilla forms.pkg uses DATA/FONT;
    # buttons use Data/ from russian.pkg. One archive cannot hold both
    # DATA and Data — the engine keys folders by the uppercase name.
    # A mod PKG of DATA/FONT is read (game build 2.1.2500 / Proton 11.0-100).
    forms_pkg = game / "DATA/forms.pkg"
    vanilla_forms = forms_pkg.with_name(forms_pkg.name + ".vanilla")
    if vanilla_forms.exists():
        shutil.copy2(vanilla_forms, forms_pkg)
    font_count = write_patched_fonts(forms_pkg, work / "fonts")

    (mod / "DATA").mkdir(parents=True, exist_ok=True)
    package = PKG.from_folder(work / "pkg")
    package.compress(9)
    package.to_file(mod / "DATA/belarusian.pkg")
    font_package = PKG.from_folder(work / "fonts")
    font_package.compress(9)
    font_package.to_file(mod / "DATA/belarusian_fonts.pkg")

    quest_count = write_translated_quests(work / "quests")
    quest_package = mod / "DATA/belarusian_quests.pkg"
    if quest_count:
        package = PKG.from_folder(work / "quests")
        package.compress(9)
        package.to_file(quest_package)
    elif quest_package.exists():
        quest_package.unlink()

    for language in ("Eng", "Rus"):
        destination = mod / f"CFG/{language}/Lang.dat"
        destination.parent.mkdir(parents=True, exist_ok=True)
        patch_dat(game / f"CFG/{language}/Lang.dat", destination)
        parsed = DAT.from_dat(destination).to_dict()
        assert parsed["FormGameMenu"]["Resume"] == "Працягнуць (Esc)"
        assert parsed["FormMain"]["Options"] == "Налады"
    robot_count = write_translated_robots(mod / "CFG")

    packages = [
        "    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian.pkg",
        "    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian_fonts.pkg",
    ]
    if quest_count:
        packages.append("    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian_quests.pkg")
    manifest = "Packages {\n" + "\n".join(packages) + "\n}"
    (mod / "INSTALL_ENGLISH.TXT").write_text(manifest, encoding="ascii", newline="\r\n")
    (mod / "INSTALL_RUSSIAN.TXT").write_text(manifest, encoding="ascii", newline="\r\n")

    info = """Name=Belarusian
Author=siarhei
Conflict=German,Spanish
Dependence=
Priority=6
Section=Твики
SectionEng=Tweaks
Languages=Rus,Eng
SmallDescription=Беларускі пераклад
SmallDescriptionEng=Belarusian translation
FullDescription=Беларускі пераклад Space Rangers HD.
FullDescriptionEng=Belarusian translation for Space Rangers HD.
"""
    write_utf16(mod / "ModuleInfo.txt", info)

    # Structural self-check: package can unpack and every generated GI decodes.
    with TemporaryDirectory() as temporary:
        extracted = Path(temporary)
        PKG.from_file(mod / "DATA/belarusian.pkg").to_folder(extracted)
        for (folder, button) in buttons:
            for state in "NAD":
                gi = GI.from_gi(extracted / f"Data/{folder}/2But{button}{state}.gi")
                assert gi.to_image().size == (316, 45)
        assert not (extracted / "DATA").exists()
        fonts_extracted = Path(temporary) / "fonts"
        fonts_extracted.mkdir()
        PKG.from_file(mod / "DATA/belarusian_fonts.pkg").to_folder(fonts_extracted)
        fonts = list((fonts_extracted / "DATA/FONT").glob("*.aft"))
        assert len(fonts) == font_count
        patched = fonts[0].read_bytes()
        codes = set(glyph_codes(patched))
        assert 0x0456 in codes and 0x045E in codes
        assert 0x2019 in codes and 0x0027 in codes

    # ModuleInfo must be UTF-16 LE + BOM with single CRLF (not \\r\\r\\n on Windows).
    raw = (mod / "ModuleInfo.txt").read_bytes()
    assert raw.startswith(b"\xff\xfe"), "ModuleInfo missing UTF-16 LE BOM"
    assert b"\r\r\n" not in raw, "ModuleInfo has doubled CR (write_utf16 newline bug)"
    assert b"N\x00a\x00m\x00e\x00=\x00B\x00e\x00l\x00a\x00r\x00u\x00s\x00i\x00a\x00n\x00" in raw

    n_dat = len(translations())
    print(f"Built {mod}")
    print(f"Preview: {preview}")
    print(f"Menu buttons: {len(buttons)}")
    print(f"Patched AFT fonts: {font_count}")
    print(f"Translated DAT rows: {n_dat}")
    print(f"Translated quest files: {quest_count}")
    print(f"Translated robots.dat rows: {robot_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game",
        type=Path,
        help=f"game install folder (default: {DEFAULT_GAME})",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="restore patched game CFG/DATA files and remove Mods/Tweaks/BelTranslate",
    )
    args = parser.parse_args()
    game = configure_game(args.game)
    if args.uninstall:
        uninstall(game)
        return
    build(game)


if __name__ == "__main__":
    main()
