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

"""Parameters removed by the Bot API 7 migration must stay removed.

The migration was adopted outright, with no deprecation shims (see docs/dev/UPGRADE-PLAN.md, Q1),
so nothing warns a caller who still passes the old spelling -- they get an unexpected-keyword
TypeError. That makes it worth asserting the old names cannot creep back in through a later port,
which is exactly how they would: Kurigram still carries both, and every send method is a candidate
for future porting.
"""

from __future__ import annotations

import inspect

import pytest

import pyrogram
from pyrogram import types
from pyrogram.methods import Methods

# `reply_to_message_id` survives as a *Message attribute* describing an incoming message, and
# `reply_to_message_ids` is a get_messages fetch filter. Neither is a send parameter.
REMOVED = ("reply_to_message_id", "disable_web_page_preview")

REPLACEMENTS = {
    "reply_to_message_id": "reply_parameters",
    "disable_web_page_preview": "link_preview_options",
}


def public_methods():
    for name in dir(Methods):
        if name.startswith("_"):
            continue
        attr = getattr(Methods, name, None)
        if callable(attr):
            yield name, attr


def bound_methods():
    for type_name in ("Message", "CallbackQuery"):
        cls = getattr(types, type_name)
        for name in dir(cls):
            if name.startswith("_"):
                continue
            attr = getattr(cls, name, None)
            if callable(attr):
                yield f"{type_name}.{name}", attr


ALL_CALLABLES = list(public_methods()) + list(bound_methods())


def test_the_scan_found_the_surface():
    assert len(ALL_CALLABLES) > 200, f"only {len(ALL_CALLABLES)} callables found; scan is broken"


@pytest.mark.parametrize("removed", REMOVED)
def test_no_public_callable_still_accepts_the_removed_parameter(removed):
    offenders = []
    for name, attr in ALL_CALLABLES:
        try:
            params = inspect.signature(attr).parameters
        except (ValueError, TypeError):  # pragma: no cover - builtins have no signature
            continue
        if removed in params:
            offenders.append(name)
    assert not offenders, (
        f"{removed!r} is back in {offenders}; use {REPLACEMENTS[removed]!r} instead"
    )


@pytest.mark.parametrize(
    ("method", "parameter"),
    [
        ("send_message", "reply_parameters"),
        ("send_message", "link_preview_options"),
        ("send_photo", "reply_parameters"),
        ("edit_message_text", "link_preview_options"),
        ("copy_message", "reply_parameters"),
    ],
)
def test_the_replacement_is_present(method, parameter):
    assert parameter in inspect.signature(getattr(pyrogram.Client, method)).parameters


def test_message_keeps_reply_to_message_id_as_an_attribute():
    """The read side is unchanged: it describes an incoming message, it is not a send target."""
    assert "reply_to_message_id" in inspect.signature(types.Message.__init__).parameters


def test_get_messages_keeps_its_plural_fetch_filter():
    """`reply_to_message_ids` fetches replies; it was never the send parameter."""
    params = inspect.signature(pyrogram.Client.get_messages).parameters
    assert "reply_to_message_ids" in params
