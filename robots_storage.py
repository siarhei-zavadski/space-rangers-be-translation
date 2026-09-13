"""Minimal MatrixGame CStorage reader/writer for CFG/*/robots.dat."""

from dataclasses import dataclass
import struct
import zlib


ST_WCHAR = 5


@dataclass
class Item:
    name: str
    type: int
    blob: bytes
    arrays: list[str] | None = None


@dataclass
class Record:
    name: str
    items: list[Item]


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def u32(self) -> int:
        value = struct.unpack_from("<I", self.data, self.pos)[0]
        self.pos += 4
        return value

    def wstr(self) -> str:
        start = self.pos
        while self.data[self.pos:self.pos + 2] != b"\0\0":
            self.pos += 2
        value = self.data[start:self.pos].decode("utf-16le")
        self.pos += 2
        return value

    def bytes(self, size: int) -> bytes:
        value = self.data[self.pos:self.pos + size]
        self.pos += size
        return value


def pack_wstr(value: str) -> bytes:
    return value.encode("utf-16le") + b"\0\0"


def decode_zl03(data: bytes) -> bytes:
    if data[:8] != b"STRG\x01\0\0\0" or data[8:12] != b"ZL03":
        raise ValueError("Unsupported robots.dat Storage header")
    reader = Reader(data[12:])
    result = bytearray()
    for _ in range(reader.u32()):
        size = reader.u32()
        result.extend(zlib.decompress(reader.bytes(size)))
    if reader.pos != len(reader.data):
        raise ValueError("Trailing ZL03 data")
    return bytes(result)


def encode_zl03(raw: bytes) -> bytes:
    chunks = [zlib.compress(raw[pos:pos + 65000], 9) for pos in range(0, len(raw), 65000)]
    body = bytearray(b"STRG\x01\0\0\0ZL03")
    body.extend(struct.pack("<I", len(chunks)))
    for chunk in chunks:
        body.extend(struct.pack("<I", len(chunk)))
        body.extend(chunk)
    return bytes(body)


def parse_wchar_arrays(blob: bytes) -> list[str]:
    table_offset, count, element_size = struct.unpack_from("<III", blob)
    if element_size != 2 or table_offset + count * 12 > len(blob):
        raise ValueError("Invalid CDataBuf")
    result = []
    for index in range(count):
        offset, length, allocated = struct.unpack_from("<III", blob, table_offset + index * 12)
        if length > allocated or offset + length * 2 > table_offset:
            raise ValueError("Invalid CDataBuf array")
        result.append(blob[offset:offset + length * 2].decode("utf-16le"))
    return result


def encode_wchar_arrays(arrays: list[str]) -> bytes:
    encoded = [value.encode("utf-16le") for value in arrays]
    table_offset = 12 + sum(map(len, encoded))
    result = bytearray(struct.pack("<III", table_offset, len(encoded), 2))
    offset = 12
    for value in encoded:
        result.extend(value)
    for value in encoded:
        length = len(value) // 2
        result.extend(struct.pack("<III", offset, length, length))
        offset += len(value)
    return bytes(result)


def parse_raw(raw: bytes) -> list[Record]:
    reader = Reader(raw)
    records = []
    for _ in range(reader.u32()):
        name = reader.wstr()
        items = []
        for _ in range(reader.u32()):
            item_name = reader.wstr()
            item_type = reader.u32()
            blob = reader.bytes(reader.u32())
            arrays = parse_wchar_arrays(blob) if item_type == ST_WCHAR else None
            items.append(Item(item_name, item_type, blob, arrays))
        records.append(Record(name, items))
    if reader.pos != len(raw):
        raise ValueError("Trailing CStorage data")
    return records


def encode_raw(records: list[Record]) -> bytes:
    result = bytearray(struct.pack("<I", len(records)))
    for record in records:
        result.extend(pack_wstr(record.name))
        result.extend(struct.pack("<I", len(record.items)))
        for item in record.items:
            blob = encode_wchar_arrays(item.arrays) if item.arrays is not None and item.blob == b"" else item.blob
            result.extend(pack_wstr(item.name))
            result.extend(struct.pack("<II", item.type, len(blob)))
            result.extend(blob)
    return bytes(result)


def parse(data: bytes) -> tuple[bytes, list[Record]]:
    raw = decode_zl03(data)
    return raw, parse_raw(raw)


def replace_array(item: Item, index: int, value: str) -> None:
    if item.arrays is None:
        raise TypeError("Not a wchar CDataBuf")
    item.arrays[index] = value
    item.blob = b""  # Rebuild this item compactly.


def encode(records: list[Record]) -> bytes:
    return encode_zl03(encode_raw(records))
