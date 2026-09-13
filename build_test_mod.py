#!/usr/bin/env python3
"""Build the Belarusian UI translation mod (Lang.dat + menu button GI)."""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from PIL import Image, ImageDraw, ImageFont
from rangers.dat import DAT
from rangers.graphics.gi import GI
from rangers.pkg import PKG

from aft_font import glyph_codes, patch_game_forms, write_patched_fonts
from crowdin_sync import (
    ASSETS,
    asset_translations,
    check as check_crowdin,
    set_value,
    translations as crowdin_translations,
    write_translated_quests,
    write_translated_robots,
)


PROJECT = Path(__file__).parent
GAME = Path.home() / ".local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
MOD = GAME / "Mods/Tweaks/BelTranslate"
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
    for path, translation in crowdin_translations().items():
        try:
            set_value(values, path, translation.translate(APOSTROPHE_FOLD))
        except TypeError:
            # Eng Lang.dat flattens a few Rus arrays into one string (e.g. BK/Policy/BK).
            continue
    DAT.from_dict(values).to_dat(destination, fmt="HDMain", sign=True)


def write_utf16(path: Path, text: str) -> None:
    path.write_text(text.replace("\n", "\r\n"), encoding="utf-16")


def main() -> None:
    assert FONT.exists(), FONT
    check_crowdin()
    source_pkg = GAME / "DATA/russian.pkg"
    assert source_pkg.exists(), source_pkg

    work = PROJECT / "build"
    if work.exists():
        shutil.rmtree(work)
    preview = work / "preview"
    preview.mkdir(parents=True)
    buttons = {
        key: value
        for key, value in asset_translations().items()
        if ASSETS[key][2] == "button"
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
    forms_pkg = GAME / "DATA/forms.pkg"
    vanilla_forms = forms_pkg.with_name(forms_pkg.name + ".vanilla")
    # Overlay of DATA/FONT is ignored. Community tools edit forms.pkg.
    # Same-size CE-slot remap only — do not append glyphs or bump sizes.
    font_src = vanilla_forms if vanilla_forms.exists() else forms_pkg
    font_count = write_patched_fonts(font_src, work / "fonts")
    game_font_count = patch_game_forms(forms_pkg)
    assert game_font_count == font_count

    (MOD / "DATA").mkdir(parents=True, exist_ok=True)
    package = PKG.from_folder(work / "pkg")
    package.compress(9)
    package.to_file(MOD / "DATA/belarusian.pkg")
    font_package = PKG.from_folder(work / "fonts")
    font_package.compress(9)
    font_package.to_file(MOD / "DATA/belarusian_fonts.pkg")

    quest_count = write_translated_quests(work / "quests")
    quest_package = MOD / "DATA/belarusian_quests.pkg"
    if quest_count:
        package = PKG.from_folder(work / "quests")
        package.compress(9)
        package.to_file(quest_package)
    elif quest_package.exists():
        quest_package.unlink()

    for language in ("Eng", "Rus"):
        destination = MOD / f"CFG/{language}/Lang.dat"
        destination.parent.mkdir(parents=True, exist_ok=True)
        patch_dat(GAME / f"CFG/{language}/Lang.dat", destination)
        parsed = DAT.from_dat(destination).to_dict()
        assert parsed["FormGameMenu"]["Resume"] == "Працягнуць (Esc)"
        assert parsed["FormMain"]["Options"] == "Налады"
    robot_count = write_translated_robots(MOD / "CFG/robots.dat")

    packages = [
        "    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian.pkg",
        "    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian_fonts.pkg",
    ]
    if quest_count:
        packages.append("    Package=Mods\\Tweaks\\BelTranslate\\data\\belarusian_quests.pkg")
    manifest = "Packages {\n" + "\n".join(packages) + "\n}"
    (MOD / "INSTALL_ENGLISH.TXT").write_text(manifest, encoding="ascii", newline="\r\n")
    (MOD / "INSTALL_RUSSIAN.TXT").write_text(manifest, encoding="ascii", newline="\r\n")

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
    write_utf16(MOD / "ModuleInfo.txt", info)

    # Structural self-check: package can unpack and every generated GI decodes.
    with TemporaryDirectory() as temporary:
        extracted = Path(temporary)
        PKG.from_file(MOD / "DATA/belarusian.pkg").to_folder(extracted)
        for (folder, button) in buttons:
            for state in "NAD":
                gi = GI.from_gi(extracted / f"Data/{folder}/2But{button}{state}.gi")
                assert gi.to_image().size == (316, 45)
        assert not (extracted / "DATA").exists()
        fonts_extracted = Path(temporary) / "fonts"
        fonts_extracted.mkdir()
        PKG.from_file(MOD / "DATA/belarusian_fonts.pkg").to_folder(fonts_extracted)
        fonts = list((fonts_extracted / "DATA/FONT").glob("*.aft"))
        assert len(fonts) == font_count
        patched = fonts[0].read_bytes()
        codes = set(glyph_codes(patched))
        assert 0x0456 in codes and 0x045E in codes
        assert 0x2019 in codes and 0x0027 in codes

    n_dat = len(crowdin_translations())
    print(f"Built {MOD}")
    print(f"Preview: {preview}")
    print(f"Menu buttons: {len(buttons)}")
    print(f"Patched AFT fonts: {font_count}")
    print(f"Translated DAT rows: {n_dat}")
    print(f"Translated quest files: {quest_count}")
    print(f"Translated robots.dat rows: {robot_count}")


if __name__ == "__main__":
    main()
