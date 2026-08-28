#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

"""TL serialization round-trips over the generated layer.

``pyrogram/raw/`` is excluded from coverage because it is generated, which leaves it with no
guard at all unless something exercises it structurally. These tests do that: they walk the
compiled layer itself rather than a hand-written list, so new constructors are covered the moment
`make api` produces them.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from io import BytesIO
from pathlib import Path

import pytest

from pyrogram import raw
from pyrogram.raw.core import Bool, Int, Long, String, TLObject, Vector


def all_raw_types() -> list[type[TLObject]]:
    found: list[type[TLObject]] = []
    for module_info in pkgutil.walk_packages(raw.types.__path__, f"{raw.types.__name__}."):
        module = importlib.import_module(module_info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, TLObject) and obj.__module__ == module_info.name:
                found.append(obj)
    return found


RAW_TYPES = all_raw_types()


def test_layer_is_the_one_the_schema_declares():
    schema = Path(raw.__file__).parent.parent.parent / "compiler/api/source/main_api.tl"
    declared = [
        line
        for line in schema.read_text(encoding="utf-8").splitlines()
        if line.startswith("// LAYER")
    ][-1]
    assert declared.split()[-1] == str(raw.all.layer), (
        "pyrogram/raw is stale: regenerate it with `make api`"
    )


def test_walk_found_the_layer():
    assert len(RAW_TYPES) > 1400, f"only {len(RAW_TYPES)} raw types found; the walk is broken"


def test_every_constructor_id_is_registered():
    """``raw.all.objects`` is what the deserializer dispatches on; a gap there is silent data loss."""
    registered = set(raw.all.objects)
    missing = sorted(
        f"{cls.__module__}.{cls.__qualname__}" for cls in RAW_TYPES if cls.ID not in registered
    )
    assert not missing, (
        f"{len(missing)} constructors are absent from raw.all.objects: {missing[:5]}"
    )


def test_constructor_ids_are_unique():
    seen: dict[int, str] = {}
    clashes = []
    for cls in RAW_TYPES:
        name = f"{cls.__module__}.{cls.__qualname__}"
        if cls.ID in seen:
            clashes.append(f"{hex(cls.ID)}: {seen[cls.ID]} and {name}")
        else:
            seen[cls.ID] = name
    assert not clashes, clashes


@pytest.mark.parametrize(
    ("primitive", "value"),
    [
        (Int, 0),
        (Int, -1),
        (Int, 2**31 - 1),
        (Int, -(2**31)),
        (Long, 0),
        (Long, 2**63 - 1),
        (Long, -(2**63)),
        (Bool, True),
        (Bool, False),
        (String, ""),
        (String, "hello"),
        (String, "متن فارسی"),
        (String, "x" * 1000),  # crosses the long-string length prefix
    ],
)
def test_primitive_round_trip(primitive, value):
    assert primitive.read(BytesIO(primitive(value))) == value


# Vector is asymmetric and the asymmetry bites: __new__ emits the 0x1CB5C415 constructor ID
# followed by the count, but read() starts at the count. Callers are expected to have consumed the
# ID already (TLObject.read dispatches on it before delegating). Feeding a full Vector payload
# straight back into Vector.read makes it interpret 0x1CB5C415 as the element count and allocate a
# 481-million element list -- an OOM kill, not an exception. The [4:] below is not incidental.
VECTOR_HEADER = 4


def test_vector_write_starts_with_the_vector_constructor_id():
    assert Vector([1, 2, 3], Int)[:VECTOR_HEADER] == Int(Vector.ID, False)


@pytest.mark.parametrize("values", [[], [1], [1, 2, 3], list(range(100))])
def test_vector_round_trip(values):
    payload = Vector(values, Int)
    assert Vector.read(BytesIO(payload[VECTOR_HEADER:]), Int) == values


def test_vector_of_objects_round_trip():
    """Object vectors are read with t=None, dispatching on each element's own constructor ID."""
    buttons = [
        raw.types.KeyboardInlineButton(
            text="a", type=raw.types.InlineButtonTypeUrl(url="https://example.com")
        ),
        raw.types.KeyboardInlineButton(
            text="b", type=raw.types.InlineButtonTypeUrl(url="https://example.org")
        ),
    ]
    payload = Vector(buttons)
    restored = Vector.read(BytesIO(payload[VECTOR_HEADER:]))
    assert [b.write() for b in restored] == [b.write() for b in buttons]


# Round-tripping *every* generated type by filling its fields from primitives looks thorough and
# is not: the only runtime type information is the annotation string, and substring matching on it
# is unsound. "list[int]" contains "int", and -- less obviously -- "GeoPoint" contains "int" too,
# so a nested TL object gets filled with the integer 1 and serialization either raises or, worse,
# emits a garbage length prefix that read() turns into a multi-gigabyte allocation. That is an OOM
# kill, not a test failure.
#
# So the generated layer is checked structurally above (registration, uniqueness, layer freshness)
# and the wire format is checked here against hand-built objects that are actually valid. Each
# entry exists for a serialization shape, not for coverage of a particular method.
def curated_objects() -> list[tuple[str, TLObject]]:
    return [
        # bare longs
        ("InputPeerUser", raw.types.InputPeerUser(user_id=123456789, access_hash=-987654321)),
        # single small int
        ("PeerChannel", raw.types.PeerChannel(channel_id=1234567890)),
        # two plain ints
        ("MessageEntityBold", raw.types.MessageEntityBold(offset=0, length=5)),
        # flags with only "true" bits set, no payload
        (
            "KeyboardButtonStyle-flags-only",
            raw.types.KeyboardButtonStyle(bg_danger=True),
        ),
        # flags carrying an optional long
        (
            "KeyboardButtonStyle-with-icon",
            raw.types.KeyboardButtonStyle(bg_success=True, icon=5361979468344771956),
        ),
        # bytes payload plus a nested optional object
        (
            "KeyboardInlineButton-callback",
            raw.types.KeyboardInlineButton(
                text="press",
                type=raw.types.InlineButtonTypeCallback(data=b"cb:1"),
                style=raw.types.KeyboardButtonStyle(bg_primary=True),
            ),
        ),
        # bytes that are not valid utf-8
        (
            "KeyboardInlineButton-binary-payload",
            raw.types.KeyboardInlineButton(
                text="x", type=raw.types.InlineButtonTypeCallback(data=bytes(range(256)))
            ),
        ),
        # vector of nested objects
        (
            "ReplyInlineMarkup",
            raw.types.ReplyInlineMarkup(
                rows=[
                    raw.types.KeyboardInlineButtonRow(
                        buttons=[
                            raw.types.KeyboardInlineButton(
                                text="a",
                                type=raw.types.InlineButtonTypeUrl(url="https://example.com"),
                            ),
                            raw.types.KeyboardInlineButton(
                                text="b",
                                type=raw.types.InlineButtonTypeUrl(url="https://example.org"),
                            ),
                        ]
                    )
                ]
            ),
        ),
        # empty vector
        ("ReplyInlineMarkup-empty", raw.types.ReplyInlineMarkup(rows=[])),
        # unicode strings, including a long one crossing the length-prefix boundary
        (
            "MessageEntityUrl-unicode",
            raw.types.KeyboardInlineButton(
                text="سلام دنیا 🌍",
                type=raw.types.InlineButtonTypeUrl(url="https://" + "a" * 300),
            ),
        ),
        # deeply nested optional chain
        (
            "InputMediaUploadedDocument",
            raw.types.InputMediaUploadedDocument(
                file=raw.types.InputFile(id=1, parts=1, name="f.bin", md5_checksum=""),
                mime_type="application/octet-stream",
                attributes=[raw.types.DocumentAttributeFilename(file_name="f.bin")],
            ),
        ),
        # negative and boundary integers
        ("Message-boundaries", raw.types.MessageEntityBold(offset=0, length=2**31 - 1)),
    ]


CURATED = curated_objects()


@pytest.mark.parametrize(("label", "obj"), CURATED, ids=[label for label, _ in CURATED])
def test_curated_round_trip(label, obj):
    """write() -> read() -> write() must reproduce the bytes exactly, and consume them exactly.

    Byte-stability rather than object equality is the property worth asserting. An unset
    ``flags.n?true`` field is ``None`` on the object we built but comes back as ``False`` after a
    round trip, so ``restored == obj`` fails on objects that serialize identically. The wire format
    is what has to be stable; the attribute spelling of an absent flag is not.
    """
    cls = type(obj)
    data = obj.write()
    assert data[:4] == cls.ID.to_bytes(4, "little"), "constructor ID prefix is wrong"

    buffer = BytesIO(data[4:])
    restored = cls.read(buffer)
    assert buffer.read() == b"", "read() left bytes on the wire"
    assert restored.write() == data, f"{label} is not stable across a re-serialise"


@pytest.mark.parametrize(("label", "obj"), CURATED, ids=[label for label, _ in CURATED])
def test_curated_values_survive(label, obj):
    """Every field we set explicitly must come back with the same value."""
    restored = type(obj).read(BytesIO(obj.write()[4:]))
    # Generated TL classes use __slots__, so there is no __dict__ to walk.
    for field in type(obj).__slots__:
        expected = getattr(obj, field, None)
        if expected is None:
            continue
        actual = getattr(restored, field)
        if isinstance(expected, list):
            assert len(actual) == len(expected), f"{label}.{field} changed length"
        elif isinstance(expected, TLObject):
            assert actual.write() == expected.write(), f"{label}.{field} changed"
        else:
            assert actual == expected, f"{label}.{field} changed"


# --- optional vectors -------------------------------------------------------
#
# read() gives an absent `flags.n?Vector<T>` field the value `[]`, not None, while the flag bit is
# computed by truthiness. The generated write() used to guard the body on `is not None`, so a
# round-tripped object wrote an empty Vector (8 bytes) with its flag bit clear -- every field after
# it was then read from the wrong offset. 97 generated types carried the pattern. The guard in
# compiler/api/compiler.py is now truthiness, matching the flag calculation.


def test_absent_optional_vector_reads_as_empty_list():
    obj = raw.types.InputMediaUploadedDocument(
        file=raw.types.InputFile(id=1, parts=1, name="f.bin", md5_checksum=""),
        mime_type="application/octet-stream",
        attributes=[raw.types.DocumentAttributeFilename(file_name="f.bin")],
    )
    restored = type(obj).read(BytesIO(obj.write()[4:]))
    assert restored.stickers == []


def test_empty_optional_vector_writes_no_body_bytes():
    """The regression itself: `[]` must set no flag *and* write nothing."""
    without = raw.types.InputMediaUploadedDocument(
        file=raw.types.InputFile(id=1, parts=1, name="f.bin", md5_checksum=""),
        mime_type="application/octet-stream",
        attributes=[raw.types.DocumentAttributeFilename(file_name="f.bin")],
        stickers=None,
    )
    with_empty = raw.types.InputMediaUploadedDocument(
        file=raw.types.InputFile(id=1, parts=1, name="f.bin", md5_checksum=""),
        mime_type="application/octet-stream",
        attributes=[raw.types.DocumentAttributeFilename(file_name="f.bin")],
        stickers=[],
    )
    assert with_empty.write() == without.write()


def test_every_optional_vector_field_is_stable_across_a_round_trip():
    """Sweep the generated layer for the pattern rather than trusting one example."""
    offenders = []
    for cls in RAW_TYPES:
        source_read = getattr(cls, "read", None)
        if source_read is None:
            continue
        try:
            code = inspect.getsource(cls.write)
        except (OSError, TypeError):  # pragma: no cover - generated code is always on disk
            continue
        if "if self." in code and " is not None:\n            b.write(Vector(" in code:
            offenders.append(f"{cls.__module__}.{cls.__qualname__}")
    assert not offenders, (
        f"{len(offenders)} generated types guard an optional Vector body on `is not None` while "
        f"the flag bit uses truthiness; regenerate with the fixed compiler. First few: "
        f"{offenders[:5]}"
    )
