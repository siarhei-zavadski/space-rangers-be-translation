# UI font

Selected: **Russo One Regular**

- Source: https://fonts.google.com/specimen/Russo+One
- Local file: `tools/fonts/RussoOne-Regular.ttf`
- License: SIL Open Font License 1.1 (`tools/fonts/OFL-RussoOne.txt`)
- Use: baked `.gi` menu labels
- Coverage checked: Belarusian `І/і`, `Ў/ў`, and optional classical `Ґ/ґ`

Why: readable geometric display face close to Space Rangers' square menu lettering. The font is not embedded in `belarusian.pkg`; generated `.gi` files contain rasterized pixels only.

Runtime `Lang.dat` is UTF-16. The renderer looks up Unicode codepoints in `.aft` fonts from `forms.pkg` (`DATA/FONT/*.aft`). Vanilla coverage: Russian + Latin + Central European. Present: Latin `i`/`I`, Cyrillic `у`/`У`, ASCII `'`. Missing: `і`/`І` (U+0456/0406), `ў`/`Ў` (U+045E/040E), typographic `’`.

How letters get in (Playground/AFont/ResEditor: edit `forms.pkg`, not a mod overlay):

1. Apostrophe: DAT writer folds `’`/`‘`/`ʼ` to ASCII `'`.
2. `і`: unused Latin slots are retargeted to reuse `i`. `ў` is the game's `у` with a breve painted into a larger unused slot (same file size). A full Linux face would grow the AFT and crash `FillAlphaClip`.
3. Same-size AFTs are written into `DATA/forms.pkg` from `forms.pkg.vanilla`. A mod PKG of `DATA/FONT` is ignored on Proton.
4. Do not append glyph records or bump AFT sizes — that crashed `FillAlphaClip`. Steam verify or the `.vanilla` backup restores stock fonts.
