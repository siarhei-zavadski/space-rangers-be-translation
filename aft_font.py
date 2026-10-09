"""Patch Space Rangers AFT bitmap fonts with missing Belarusian letters.

Lang.dat is UTF-16. The renderer looks up Unicode codepoints, not CP1251.
Vanilla AFT has Latin i/I, Cyrillic у/У, and ASCII apostrophe. It omits
і/І (U+0456/0406), ў/Ў (U+045E/040E), and typographic ’.

Appending glyph records or bumping AFT sizes crashed Galaxy blit
(OKGR_TransBuf_FillAlphaClip_16). This patch only retargets unused Central
European slots (ĄąĆć…) and unused ů/Ů — same glyph count, same file size.

і clones i. Apostrophe clones ASCII '. ў is the game's у with a breve
painted into a larger unused Latin slot. A full Linux face in place of
the AFT would grow the file (FillAlphaClip) and mix typefaces.

Same-size AFTs go in the mod's belarusian_fonts.pkg (DATA/FONT/...).
Do not append glyphs or bump AFT sizes.
"""

from __future__ import annotations

import struct
from pathlib import Path

from rangers.pkg import PKG, PKG_COMP

RECORD = 64
HEADER = 32

# Latin-1 / Latin-extended letters unused by be-tarask, Russian, or ASCII UI.
UNUSED = frozenset(range(0x00C0, 0x0100)) | frozenset(range(0x0100, 0x0180))

# Clone-only: new code → existing glyph. Unique ў/Ў are composed separately.
CLONES = (
    (0x0456, 0x0069),  # і ← i
    (0x0406, 0x0049),  # І ← I
    (0x00B3, 0x0069),  # CP1251 і
    (0x00B2, 0x0049),  # CP1251 І
    (0x2019, 0x0027),  # ’
    (0x2018, 0x0027),  # ‘
    (0x02BC, 0x0027),  # ʼ
)

# Composed letter → body source. CP1251 clones the composed Unicode glyph.
COMPOSE = (
    (0x045E, 0x0443),  # ў ← у + breve
    (0x040E, 0x0423),  # Ў ← У + breve
)
COMPOSE_ALIASES = (
    (0x00A2, 0x045E),  # CP1251 ў
    (0x00A1, 0x040E),  # CP1251 Ў
)

def glyph_codes(data: bytes) -> list[int]:
    if data[:4] != b"aft\x00":
        raise ValueError("not an AFT font")
    count = struct.unpack_from("<I", data, 8)[0]
    return [struct.unpack_from("<i", data, HEADER + RECORD * i)[0] for i in range(count)]


def _recs(data: bytes) -> list[tuple[int, ...]]:
    count = struct.unpack_from("<I", data, 8)[0]
    return [struct.unpack_from("<16i", data, HEADER + RECORD * i) for i in range(count)]


def _decode(payload: bytes, w: int, h: int) -> list[list[bool]]:
    i = 0
    rows: list[list[bool]] = []
    for _ in range(h):
        if i < len(payload) and payload[i] == 0x80:
            rows.append([False] * w)
            i += 1
            continue
        row = [False] * w
        x = 0
        while i < len(payload):
            b = payload[i]
            i += 1
            if b == 0:
                break
            if b >= 0x80:
                for _ in range(b - 0x80):
                    if x < w:
                        row[x] = True
                    x += 1
            else:
                x += b
        rows.append(row)
    return rows


def _encode(rows: list[list[bool]]) -> bytes:
    w = len(rows[0]) if rows else 0
    out = bytearray()
    for row in rows:
        if not any(row):
            out.append(0x80)
            continue
        x = 0
        while x < w:
            ink = row[x]
            n = 0
            while x < w and row[x] == ink:
                n += 1
                x += 1
            while n:
                chunk = min(n, 127)
                out.append((0x80 + chunk) if ink else chunk)
                n -= chunk
        out.append(0)
    return struct.pack("<4i", len(out), w, len(rows), 0) + bytes(out)


def _read_bitmap(data: bytes, rec: tuple[int, ...]) -> list[list[bool]] | None:
    off, size = rec[8], rec[9]
    if size < 16:
        return None
    blob = data[off : off + size]
    n, w, h, _z = struct.unpack_from("<4i", blob)
    if n <= 0 or w <= 0 or h <= 0:
        return None
    return _decode(blob[16 : 16 + n], w, h)


def _pixel_breve(w: int, extra: int) -> list[list[bool]]:
    rows = [[False] * w for _ in range(extra)]
    if w < 3 or extra < 1:
        if rows:
            rows[0][w // 2] = True
        return rows
    inset = 0 if w <= 5 else 1
    rows[0][inset] = True
    rows[0][w - 1 - inset] = True
    if extra >= 2:
        for x in range(inset + 1, w - 1 - inset):
            rows[1][x] = True
    return rows


def _with_breve(body: list[list[bool]], extra: int) -> list[list[bool]]:
    w = len(body[0])
    top = _pixel_breve(w, extra)
    if extra >= 3:
        top = top[: extra - 1] + [[False] * w]
    return top + body


def _retarget_clone(out: bytearray, by: dict[int, int], steal: list[int], new: int, src: int) -> None:
    dest = steal.pop(0)
    src_off = HEADER + RECORD * by[src]
    dest_off = HEADER + RECORD * by[dest]
    out[dest_off : dest_off + RECORD] = bytes(out[src_off : src_off + RECORD])
    struct.pack_into("<i", out, dest_off, new)
    by[new] = by.pop(dest)


def _steal_pool(data: bytes, by: dict[int, int]) -> list[int]:
    recs = _recs(data)
    pool = [code for code in by if code in UNUSED]
    pool.sort(key=lambda c: recs[by[c]][9], reverse=True)
    return pool


def _retarget_bitmap(
    out: bytearray,
    by: dict[int, int],
    steal: list[int],
    new: int,
    src: int,
) -> None:
    recs = _recs(out)
    src_rec = recs[by[src]]
    body = _read_bitmap(out, src_rec)
    if body is None:
        _retarget_clone(out, by, steal, new, src)
        return
    dest = None
    encoded = b""
    extra_used = 0
    for extra in (3, 2, 1):
        blob = _encode(_with_breve(body, extra))
        for code in steal:
            if recs[by[code]][9] >= len(blob):
                dest = code
                encoded = blob
                extra_used = extra
                break
        if dest is not None:
            break
    if dest is None:
        _retarget_clone(out, by, steal, new, src)
        return
    steal.remove(dest)
    dest_rec = recs[by[dest]]
    src_off = HEADER + RECORD * by[src]
    dest_off = HEADER + RECORD * by[dest]
    out[dest_off : dest_off + RECORD] = bytes(out[src_off : src_off + RECORD])
    struct.pack_into("<i", out, dest_off, new)
    struct.pack_into("<i", out, dest_off + 20, src_rec[5] - extra_used)
    struct.pack_into("<i", out, dest_off + 24, len(body[0]))
    struct.pack_into("<i", out, dest_off + 28, len(body) + extra_used)
    struct.pack_into("<i", out, dest_off + 32, dest_rec[8])
    struct.pack_into("<i", out, dest_off + 36, dest_rec[9])
    out[dest_rec[8] : dest_rec[8] + len(encoded)] = encoded
    by[new] = by.pop(dest)


def patch_aft(data: bytes, *, bold: bool = False) -> bytes:
    """Retarget unused slots. File length and glyph count stay the same."""
    del bold  # kept so call sites stay stable
    if data[:4] != b"aft\x00":
        raise ValueError("not an AFT font")
    count = struct.unpack_from("<I", data, 8)[0]
    by = {struct.unpack_from("<i", data, HEADER + RECORD * i)[0]: i for i in range(count)}
    out = bytearray(data)
    steal = _steal_pool(data, by)
    for new, src in COMPOSE:
        if new in by:
            continue
        if src not in by:
            raise ValueError(f"missing source glyph U+{src:04X}")
        if not steal:
            raise ValueError(f"no unused slot for U+{new:04X}")
        _retarget_bitmap(out, by, steal, new, src)
    for new, src in (*CLONES, *COMPOSE_ALIASES):
        if new in by:
            continue
        if src not in by:
            raise ValueError(f"missing source glyph U+{src:04X}")
        if not steal:
            raise ValueError(f"no unused slot for U+{new:04X}")
        _retarget_clone(out, by, steal, new, src)
    assert len(out) == len(data)
    assert struct.unpack_from("<I", out, 8)[0] == count
    return bytes(out)


def _is_bold_name(path: str) -> bool:
    lower = path.lower()
    return "_4." in lower or "bold" in lower


def write_patched_fonts(source_pkg: Path, destination: Path) -> int:
    """Write same-size patched AFTs at vanilla DATA/FONT/..."""
    pkg = PKG.from_file(source_pkg)
    written = 0

    def walk(node: PKG, prefix: str = "") -> None:
        nonlocal written
        if node.type == 3:
            name = "" if node.name == "<root>" else node.name + "/"
            for child in node.data:
                walk(child, prefix + name)
            return
        path = prefix + node.name
        if not path.lower().endswith(".aft"):
            return
        raw = bytes(node.data)
        if node.type == PKG_COMP:
            raw = PKG._decompress(raw)
        patched = patch_aft(raw, bold=_is_bold_name(path))
        codes = set(glyph_codes(patched))
        assert len(patched) == len(raw)
        assert 0x0456 in codes and 0x0406 in codes
        assert 0x045E in codes and 0x040E in codes
        assert 0x2019 in codes and 0x0027 in codes
        out = destination / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(patched)
        written += 1

    walk(pkg)
    return written


def _art(rows: list[list[bool]]) -> str:
    return "\n".join("".join("#" if p else "." for p in row) for row in rows)


def _selfcheck() -> None:
    game = Path.home() / ".local/share/Steam/steamapps/common/Space Rangers HD A War Apart"
    src = game / "DATA/forms.pkg.vanilla"
    if not src.exists():
        src = game / "DATA/forms.pkg"
    pkg = PKG.from_file(src)

    def walk(node: PKG, prefix: str = "") -> None:
        if node.type == 3:
            name = "" if node.name == "<root>" else node.name + "/"
            for child in node.data:
                walk(child, prefix + name)
            return
        path = prefix + node.name
        if not path.lower().endswith(".aft"):
            return
        raw = bytes(node.data)
        if node.type == PKG_COMP:
            raw = PKG._decompress(raw)
        patched = patch_aft(raw, bold=_is_bold_name(path))
        assert len(patched) == len(raw)
        recs = {r[0]: r for r in _recs(patched)}
        uy = _read_bitmap(patched, recs[0x0443])
        breve = _read_bitmap(patched, recs[0x045E])
        if uy is None or breve is None:
            print("empty", path)
            return
        assert len(breve) >= len(uy)
        marked = any(p for row in breve[: len(breve) - len(uy)] for p in row)
        if path.endswith("ranger_5.aft"):
            print("у\n" + _art(uy))
            print("ў\n" + _art(breve))
        print("ok" if marked else "CLONE", path, f"{len(uy[0])}x{len(uy)}→{len(breve[0])}x{len(breve)}")

    walk(pkg)


if __name__ == "__main__":
    _selfcheck()
