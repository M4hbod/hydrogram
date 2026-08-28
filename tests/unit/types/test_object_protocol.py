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

"""The `Object` serialisation protocol.

`str(obj)` is what ends up in logs and bug reports, so what it does *not* contain matters as much
as what it does.
"""

from __future__ import annotations

import json

from pyrogram import raw, types
from pyrogram.types.object import ATTRIBUTES_TO_HIDE, ATTRIBUTES_TO_MASK


def test_phone_numbers_are_masked_not_omitted():
    """Masking keeps the shape visible; omitting would hide that a number was present at all."""
    user = types.User(id=1, phone_number="+15551234567")
    dumped = json.loads(str(user))
    assert dumped["phone_number"] == "*********"


def test_raw_attribute_is_hidden_from_str():
    """Types that keep their source MTProto object must not dump it.

    Several ported types (Gift, Invoice, Folder, GiftAuctionState) hold the raw constructor they
    were parsed from as an escape hatch. It is enormous, it is an implementation detail, and it can
    carry fields the wrapper deliberately masks -- so it is hidden rather than serialised.
    """
    invoice = types.Invoice(
        currency="XTR",
        is_test=False,
        title="t",
        description="d",
        total_amount=1,
        raw=raw.types.Invoice(
            currency="XTR",
            prices=[raw.types.LabeledPrice(label="l", amount=1)],
            max_tip_amount=0,
            suggested_tip_amounts=[],
        ),
    )
    assert invoice.raw is not None, "the attribute still exists for callers who want it"
    assert "raw" not in json.loads(str(invoice)), "but it must not appear in str()"


def test_hidden_and_masked_sets_are_disjoint():
    assert not (ATTRIBUTES_TO_HIDE & ATTRIBUTES_TO_MASK)


def test_none_values_are_omitted():
    assert "description" not in json.loads(str(types.Invoice(currency="XTR", is_test=False)))


def test_underscore_attributes_are_omitted():
    obj = types.Invoice(currency="XTR", is_test=False)
    obj._client = "sentinel"
    assert "_client" not in json.loads(str(obj))


def test_parse_chat_returns_none_for_a_missing_peer():
    """Callers pass `users.get(id) or chats.get(id)` straight in; a miss must not crash.

    `User._parse` already returned None for a missing peer, `Chat._parse_chat` fell through to
    `_parse_channel_chat(None)` and raised AttributeError.
    """
    assert types.Chat._parse_chat(None, None) is None
