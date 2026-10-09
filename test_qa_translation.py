"""Smallest check that qa_translation.check() and the corpus loader still fail on what they must fail on."""

from pathlib import Path
from tempfile import TemporaryDirectory

from qa_translation import SLIPS, check, resolve_corpus_file
from validate_corpus import load

row = lambda src, be: {"source_phrase": src, "be": be}  # noqa: E731

assert check(row('1 колба "Т"', '2 колбы "Т"'))  # digit swapped
assert not check(row("1-й судья", "Першы судзьдзя"))  # ordinal spelled out
assert not check(row("В 8 утра", "Раніцай"))  # digits dropped is allowed
assert check(row("<format=left,5>Круг</format>", "<format=left,5>Кругавы</format>"))  # overflow
assert not check(row("<format=left,5>Круг</format>", "<format=left,5>Круг</format>"))
text = "Вашая з'ява, вашую"
for pattern, repl in SLIPS:
    text = pattern.sub(repl, text)
assert text == "Ваша зьява, вашу", text
with TemporaryDirectory() as temporary:
    duplicated = Path(temporary) / "Talk.json"
    duplicated.write_text('{\n"/Talk/a": "1",\n"/Talk/a": "2"\n}\n', encoding="utf-8")
    try:
        load(duplicated)
    except ValueError:
        pass
    else:
        raise AssertionError("a duplicated key was silently dropped")

assert resolve_corpus_file("FormMain.json").name == "FormMain.json"
print("ok")
