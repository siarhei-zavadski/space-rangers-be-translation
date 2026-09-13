# UI font

Selected: **Russo One Regular**

- Source: https://fonts.google.com/specimen/Russo+One
- Local file: `tools/fonts/RussoOne-Regular.ttf`
- License: SIL Open Font License 1.1 (`tools/fonts/OFL-RussoOne.txt`)
- Use: baked `.gi` menu labels
- Coverage checked: Belarusian `І/і`, `Ў/ў`, and optional classical `Ґ/ґ`

Why: readable geometric display face close to Space Rangers' square menu lettering. The font is not embedded in `belarusian.pkg`; generated `.gi` files contain rasterized pixels only.

Runtime `Lang.dat` text still uses the game's `.aft` fonts. Full Belarusian runtime glyph coverage (`і`, `ў`) needs a later AFont test.
