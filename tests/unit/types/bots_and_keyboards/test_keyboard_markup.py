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

"""Whole-keyboard round trips.

Layer 229 gave inline keyboards their own row type. Getting the row type wrong is the kind of
mistake that serializes fine and is rejected by the server, so it is worth an explicit assertion
rather than trusting the button-level tests.
"""

from __future__ import annotations

import asyncio

import pytest

from pyrogram import enums, raw, types


class FakeClient:
    @staticmethod
    async def resolve_peer(_peer):
        return raw.types.InputUser(user_id=1, access_hash=2)


def test_inline_markup_uses_the_inline_row_type():
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton(text="a", callback_data="a")]
    ])
    written = asyncio.run(markup.write(FakeClient()))
    assert isinstance(written, raw.types.ReplyInlineMarkup)
    assert isinstance(written.rows[0], raw.types.KeyboardInlineButtonRow)


def test_reply_markup_uses_the_plain_row_type():
    markup = types.ReplyKeyboardMarkup([["a"]])
    written = asyncio.run(markup.write(None))
    assert isinstance(written, raw.types.ReplyKeyboardMarkup)
    assert isinstance(written.rows[0], raw.types.KeyboardButtonRow)


def test_inline_markup_round_trips_its_shape():
    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton(text="a", callback_data="a"),
            types.InlineKeyboardButton(text="b", url="https://example.com"),
        ],
        [types.InlineKeyboardButton(text="c", copy_text="c")],
    ])
    parsed = types.InlineKeyboardMarkup.read(asyncio.run(markup.write(FakeClient())))

    assert [len(row) for row in parsed.inline_keyboard] == [2, 1]
    assert parsed.inline_keyboard[0][0].callback_data == "a"
    assert parsed.inline_keyboard[0][1].url == "https://example.com"
    assert parsed.inline_keyboard[1][0].copy_text == "c"


def test_inline_markup_preserves_per_button_styles():
    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton(
                text="a", callback_data="a", style=enums.ButtonStyle.DANGER
            ),
            types.InlineKeyboardButton(text="b", callback_data="b"),
        ]
    ])
    parsed = types.InlineKeyboardMarkup.read(asyncio.run(markup.write(FakeClient())))
    assert parsed.inline_keyboard[0][0].style == enums.ButtonStyle.DANGER
    assert parsed.inline_keyboard[0][1].style == enums.ButtonStyle.DEFAULT


def test_reply_markup_round_trips_plain_string_buttons():
    markup = types.ReplyKeyboardMarkup([["a", "b"], ["c"]])
    parsed = types.ReplyKeyboardMarkup.read(asyncio.run(markup.write(None)))
    assert parsed.keyboard == [["a", "b"], ["c"]]


@pytest.mark.parametrize(
    ("kwargs", "attribute"),
    [
        ({"request_contact": True}, "request_contact"),
        ({"request_location": True}, "request_location"),
    ],
)
def test_reply_markup_round_trips_special_buttons(kwargs, attribute):
    markup = types.ReplyKeyboardMarkup([[types.KeyboardButton(text="a", **kwargs)]])
    parsed = types.ReplyKeyboardMarkup.read(asyncio.run(markup.write(None)))
    assert getattr(parsed.keyboard[0][0], attribute) is True


def test_empty_keyboard_round_trips():
    written = asyncio.run(types.InlineKeyboardMarkup([]).write(FakeClient()))
    assert types.InlineKeyboardMarkup.read(written).inline_keyboard == []
