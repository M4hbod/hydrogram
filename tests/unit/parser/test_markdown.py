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

"""Markdown parsing and unparsing.

Two things this file pins down:

* **Entity offsets are UTF-16 code units, not Python characters.** Any text containing an emoji or
  another astral-plane character makes the two disagree, and the result is bold text that starts in
  the wrong place. The astral cases below are the point.
* **``parse`` and ``unparse`` are asymmetric.** ``Markdown.parse`` returns *raw* entities
  (``raw.types.MessageEntityBold``), while ``Markdown.unparse`` expects *high-level* ones
  (``types.MessageEntity``). They do not compose directly; converting between them needs a client
  to resolve mentioned users. Anything that assumes a straight round trip is wrong.
"""

from __future__ import annotations

import pytest

import pyrogram
from pyrogram import raw
from pyrogram.enums import MessageEntityType
from pyrogram.parser.markdown import Markdown

parser = Markdown(client=None)


@pytest.mark.parametrize(
    ("markup", "plain", "entity_type"),
    [
        ("**bold**", "bold", raw.types.MessageEntityBold),
        ("__italic__", "italic", raw.types.MessageEntityItalic),
        ("--underline--", "underline", raw.types.MessageEntityUnderline),
        ("~~strike~~", "strike", raw.types.MessageEntityStrike),
        ("||spoiler||", "spoiler", raw.types.MessageEntitySpoiler),
        ("`code`", "code", raw.types.MessageEntityCode),
    ],
)
async def test_basic_styles(markup, plain, entity_type):
    result = await parser.parse(markup)
    assert result["message"] == plain
    assert [type(e) for e in result["entities"]] == [entity_type]
    assert result["entities"][0].offset == 0
    assert result["entities"][0].length == len(plain)


async def test_text_without_markup_produces_no_entities():
    result = await parser.parse("just text")
    assert result["message"] == "just text"
    assert not result["entities"]


async def test_nested_styles_are_both_captured():
    result = await parser.parse("**bold and __italic__**")
    assert sorted(type(e).__name__ for e in result["entities"]) == [
        "MessageEntityBold",
        "MessageEntityItalic",
    ]


async def test_offsets_are_utf16_code_units_not_characters():
    """An astral-plane emoji is one Python character but two UTF-16 code units."""
    result = await parser.parse("👍**bold**")
    assert result["message"] == "👍bold"
    entity = result["entities"][0]
    assert entity.offset == 2, "the emoji occupies two UTF-16 code units, not one"
    assert entity.length == 4


async def test_lengths_are_utf16_code_units_too():
    result = await parser.parse("**👍👍**")
    entity = result["entities"][0]
    assert entity.offset == 0
    assert entity.length == 4, "two astral emoji are four UTF-16 code units"


async def test_url_becomes_a_text_url_entity():
    result = await parser.parse("[label](https://example.com/)")
    assert result["message"] == "label"
    entity = result["entities"][0]
    assert isinstance(entity, raw.types.MessageEntityTextUrl)
    assert entity.url == "https://example.com/"


async def test_markdown_has_no_custom_emoji_syntax():
    """Documented gap, not a bug report.

    The HTML parser understands ``<emoji id="...">`` and emits
    ``raw.types.MessageEntityCustomEmoji``. Markdown has no equivalent: a ``tg://emoji`` link is
    left as an ordinary text URL. Anything that needs custom emoji in message text has to use the
    HTML parse mode (keyboard button icons are a separate mechanism and are unaffected).
    """
    result = await parser.parse("[👍](tg://emoji?id=5361979468344771956)")
    entity = result["entities"][0]
    assert isinstance(entity, raw.types.MessageEntityTextUrl)
    assert entity.url == "tg://emoji?id=5361979468344771956"


async def test_user_mention_link_without_a_client_keeps_a_bare_id():
    """``user_id`` is only resolved to an ``InputUser`` when a client is attached.

    The TL field is ``user_id:InputUser``, and ``HTML.parse`` upgrades the int via
    ``client.resolve_peer``. With ``client=None`` -- the shape used for offline parsing -- it stays
    an int, so such an entity is not yet safe to serialize.
    """
    result = await parser.parse("[name](tg://user?id=777000)")
    entity = result["entities"][0]
    assert isinstance(entity, raw.types.InputMessageEntityMentionName)
    assert entity.user_id == 777000


async def test_code_block_keeps_its_language():
    result = await parser.parse("```python\nprint(1)\n```")
    entity = result["entities"][0]
    assert isinstance(entity, raw.types.MessageEntityPre)
    assert entity.language == "python"


# --- unparse takes high-level entities --------------------------------------


def high_level(entity_type: MessageEntityType, offset: int, length: int, **kwargs):
    return pyrogram.types.MessageEntity(type=entity_type, offset=offset, length=length, **kwargs)


@pytest.mark.parametrize(
    ("entity_type", "text", "expected"),
    [
        (MessageEntityType.BOLD, "bold", "**bold**"),
        (MessageEntityType.ITALIC, "italic", "__italic__"),
        (MessageEntityType.STRIKETHROUGH, "strike", "~~strike~~"),
        (MessageEntityType.SPOILER, "spoiler", "||spoiler||"),
        (MessageEntityType.CODE, "code", "`code`"),
    ],
)
def test_unparse_basic_styles(entity_type, text, expected):
    entities = pyrogram.types.List([high_level(entity_type, 0, len(text))])
    assert Markdown.unparse(text=text, entities=entities) == expected


def test_unparse_leaves_unstyled_text_alone():
    assert Markdown.unparse(text="plain", entities=pyrogram.types.List([])) == "plain"


def test_unparse_uses_utf16_offsets():
    """The offset is in UTF-16 units, so the emoji must not shift the styled span."""
    entities = pyrogram.types.List([high_level(MessageEntityType.BOLD, 2, 4)])
    assert Markdown.unparse(text="👍bold", entities=entities) == "👍**bold**"
