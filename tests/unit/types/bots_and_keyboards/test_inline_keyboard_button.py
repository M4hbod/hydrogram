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

"""Inline keyboard buttons across the layer-229 ``InlineButtonType`` split.

Layer 229 replaced eighteen flat ``= KeyboardButton;`` constructors with two base types --
``KeyboardButton`` for reply keyboards and a new ``KeyboardInlineButton`` for inline ones -- each
carrying a discriminator union. The public Python API did not change, so these tests are what say
so: every button kind must survive write() and come back from read() unchanged.

A button kind with no ``read()`` branch does not raise; it returns ``None`` and vanishes from the
parsed markup. The parametrised round trip below is there to make that impossible to reintroduce.
"""

from __future__ import annotations

import asyncio

import pytest

from pyrogram import enums, raw, types

CUSTOM_EMOJI_ID = "5361979468344771956"


class FakeClient:
    """Stands in for Client.resolve_peer; InlineKeyboardButton.write needs nothing else."""

    @staticmethod
    async def resolve_peer(_peer):
        return raw.types.InputUser(user_id=1, access_hash=2)


def write(button: types.InlineKeyboardButton):
    return asyncio.run(button.write(FakeClient()))


# --- every kind survives a write --------------------------------------------

BUTTON_KINDS = [
    ("callback", {"callback_data": "cb"}, raw.types.InlineButtonTypeCallback),
    ("callback-bytes", {"callback_data": b"\xff\xfe"}, raw.types.InlineButtonTypeCallback),
    ("url", {"url": "https://example.com"}, raw.types.InlineButtonTypeUrl),
    (
        "login_url",
        {"login_url": types.LoginUrl(url="https://example.com")},
        raw.types.InputInlineButtonTypeUrlAuth,
    ),
    ("user_id", {"user_id": 777000}, raw.types.InputInlineButtonTypeUserProfile),
    ("switch_inline", {"switch_inline_query": "q"}, raw.types.InlineButtonTypeSwitchInline),
    (
        "switch_inline_current",
        {"switch_inline_query_current_chat": "q"},
        raw.types.InlineButtonTypeSwitchInline,
    ),
    ("game", {"callback_game": types.CallbackGame()}, raw.types.InlineButtonTypeGame),
    (
        "web_app",
        {"web_app": types.WebAppInfo(url="https://example.com")},
        raw.types.InlineButtonTypeWebView,
    ),
    ("copy_text", {"copy_text": "copy me"}, raw.types.InlineButtonTypeCopy),
    ("pay", {"pay": True}, raw.types.InlineButtonTypeBuy),
    ("disabled", {"disabled": True}, raw.types.InlineButtonTypeDisabled),
]


@pytest.mark.parametrize(
    ("kwargs", "expected_type"),
    [(kwargs, expected) for _, kwargs, expected in BUTTON_KINDS],
    ids=[label for label, _, _ in BUTTON_KINDS],
)
def test_every_kind_writes_the_right_button_type(kwargs, expected_type):
    raw_button = write(types.InlineKeyboardButton(text="x", **kwargs))
    assert isinstance(raw_button, raw.types.KeyboardInlineButton)
    assert isinstance(raw_button.type, expected_type)
    assert raw_button.text == "x"


@pytest.mark.parametrize(
    "kwargs",
    [kwargs for _, kwargs, _ in BUTTON_KINDS],
    ids=[label for label, _, _ in BUTTON_KINDS],
)
def test_no_kind_is_dropped_by_read(kwargs):
    """read() returning None means the button disappears from the markup."""
    assert (
        types.InlineKeyboardButton.read(write(types.InlineKeyboardButton(text="x", **kwargs)))
        is not None
    )


def test_a_button_with_no_action_is_rejected():
    with pytest.raises(ValueError, match="exactly one of"):
        write(types.InlineKeyboardButton(text="x"))


# --- values survive the round trip ------------------------------------------


def test_callback_data_round_trips_as_a_string():
    parsed = types.InlineKeyboardButton.read(
        write(types.InlineKeyboardButton(text="x", callback_data="payload"))
    )
    assert parsed.callback_data == "payload"


def test_undecodable_callback_data_stays_bytes():
    """Falling back to bytes beats decoding with errors="ignore" and losing information."""
    payload = bytes(range(256))
    parsed = types.InlineKeyboardButton.read(
        write(types.InlineKeyboardButton(text="x", callback_data=payload))
    )
    assert parsed.callback_data == payload


def test_url_round_trips():
    parsed = types.InlineKeyboardButton.read(
        write(types.InlineKeyboardButton(text="x", url="https://example.com/a?b=c"))
    )
    assert parsed.url == "https://example.com/a?b=c"


def test_copy_text_round_trips():
    parsed = types.InlineKeyboardButton.read(
        write(types.InlineKeyboardButton(text="x", copy_text="copy me"))
    )
    assert parsed.copy_text == "copy me"


def test_switch_inline_current_chat_keeps_the_same_peer_flag():
    raw_button = write(types.InlineKeyboardButton(text="x", switch_inline_query_current_chat="q"))
    assert raw_button.type.same_peer is True
    parsed = types.InlineKeyboardButton.read(raw_button)
    assert parsed.switch_inline_query_current_chat == "q"
    assert parsed.switch_inline_query is None


def test_switch_inline_other_chat_does_not_set_same_peer():
    raw_button = write(types.InlineKeyboardButton(text="x", switch_inline_query="q"))
    assert not raw_button.type.same_peer
    assert types.InlineKeyboardButton.read(raw_button).switch_inline_query == "q"


# --- style and custom emoji survive the redesign ----------------------------
#
# keyboardButtonStyle#4fdd3430 is byte-identical at layer 223 and 229, so the feature carries over
# untouched. What moved is where the style sits: on the enclosing keyboardInlineButton rather than
# on each per-kind constructor.


@pytest.mark.parametrize(
    ("style", "flag"),
    [
        (enums.ButtonStyle.PRIMARY, "bg_primary"),
        (enums.ButtonStyle.DANGER, "bg_danger"),
        (enums.ButtonStyle.SUCCESS, "bg_success"),
    ],
)
@pytest.mark.parametrize(
    "kwargs",
    [kwargs for _, kwargs, _ in BUTTON_KINDS],
    ids=[label for label, _, _ in BUTTON_KINDS],
)
def test_style_survives_on_every_button_kind(style, flag, kwargs):
    """Regression: login_url used to drop the style, because LoginUrl.write() took no style."""
    raw_button = write(types.InlineKeyboardButton(text="x", style=style, **kwargs))
    assert raw_button.style is not None
    assert getattr(raw_button.style, flag) is True
    assert types.InlineKeyboardButton.read(raw_button).style == style


@pytest.mark.parametrize(
    "kwargs",
    [kwargs for _, kwargs, _ in BUTTON_KINDS],
    ids=[label for label, _, _ in BUTTON_KINDS],
)
def test_custom_emoji_icon_survives_on_every_button_kind(kwargs):
    raw_button = write(
        types.InlineKeyboardButton(text="x", icon_custom_emoji_id=CUSTOM_EMOJI_ID, **kwargs)
    )
    assert raw_button.style.icon == int(CUSTOM_EMOJI_ID)
    assert types.InlineKeyboardButton.read(raw_button).icon_custom_emoji_id == CUSTOM_EMOJI_ID


@pytest.mark.parametrize(
    "kwargs",
    [kwargs for _, kwargs, _ in BUTTON_KINDS],
    ids=[label for label, _, _ in BUTTON_KINDS],
)
def test_unstyled_buttons_send_no_style_object(kwargs):
    """An unstyled button must not carry an empty KeyboardButtonStyle."""
    assert write(types.InlineKeyboardButton(text="x", **kwargs)).style is None
