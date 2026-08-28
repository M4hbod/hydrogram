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


@pytest.mark.parametrize(
    ("style", "flag"),
    [
        (enums.ButtonStyle.PRIMARY, "bg_primary"),
        (enums.ButtonStyle.DANGER, "bg_danger"),
        (enums.ButtonStyle.SUCCESS, "bg_success"),
    ],
)
def test_login_url_button_keeps_style(style, flag):
    """Regression: LoginUrl.write() used to drop the style entirely."""
    raw_button = write(
        types.InlineKeyboardButton(
            text="login",
            login_url=types.LoginUrl(url="https://example.com"),
            style=style,
        )
    )

    assert raw_button.style is not None
    assert getattr(raw_button.style, flag) is True


def test_login_url_button_keeps_custom_emoji_icon():
    raw_button = write(
        types.InlineKeyboardButton(
            text="login",
            login_url=types.LoginUrl(url="https://example.com"),
            icon_custom_emoji_id=CUSTOM_EMOJI_ID,
        )
    )

    assert raw_button.style.icon == int(CUSTOM_EMOJI_ID)


def test_login_url_button_without_style_sends_none():
    """An unstyled button must not send an empty KeyboardButtonStyle."""
    raw_button = write(
        types.InlineKeyboardButton(
            text="login", login_url=types.LoginUrl(url="https://example.com")
        )
    )

    assert raw_button.style is None


def test_login_url_button_style_round_trips():
    button = types.InlineKeyboardButton(
        text="login",
        login_url=types.LoginUrl(url="https://example.com", forward_text="fwd"),
        style=enums.ButtonStyle.DANGER,
        icon_custom_emoji_id=CUSTOM_EMOJI_ID,
    )

    # Telegram echoes the non-input constructor back to us.
    echoed = raw.types.KeyboardButtonUrlAuth(
        text="login",
        url="https://example.com",
        button_id=0,
        fwd_text="fwd",
        style=write(button).style,
    )
    parsed = types.InlineKeyboardButton.read(echoed)

    assert parsed.style == enums.ButtonStyle.DANGER
    assert parsed.icon_custom_emoji_id == CUSTOM_EMOJI_ID
