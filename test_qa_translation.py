"""Smallest check that qa_translation.check() still fails on what it must fail on."""

from qa_translation import SLIPS, check

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
print("ok")
