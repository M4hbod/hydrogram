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

"""The shared gift cluster.

These types are wanted by three groups (business, payments, stories), which is why they are ported
once in stage 4.0 rather than three times later.
"""

from __future__ import annotations

import pytest

from pyrogram import enums, raw, types


def rarity(cls, **kwargs):
    return cls(**kwargs)


@pytest.mark.parametrize(
    ("raw_rarity", "expected"),
    [
        (raw.types.StarGiftAttributeRarityUncommon(), types.UpgradedGiftAttributeRarityUncommon),
        (raw.types.StarGiftAttributeRarityRare(), types.UpgradedGiftAttributeRarityRare),
        (raw.types.StarGiftAttributeRarityEpic(), types.UpgradedGiftAttributeRarityEpic),
        (raw.types.StarGiftAttributeRarityLegendary(), types.UpgradedGiftAttributeRarityLegendary),
    ],
)
def test_each_rarity_constructor_maps_to_its_type(raw_rarity, expected):
    assert isinstance(types.UpgradedGiftAttributeRarity._parse(raw_rarity), expected)


def test_per_mille_rarity_keeps_its_value():
    parsed = types.UpgradedGiftAttributeRarity._parse(
        raw.types.StarGiftAttributeRarity(permille=250)
    )
    assert isinstance(parsed, types.UpgradedGiftAttributeRarityPerMille)
    assert parsed.per_mille == 250


def test_unknown_rarity_is_none_rather_than_an_error():
    assert types.UpgradedGiftAttributeRarity._parse(None) is None


async def test_original_details_attribute_parses_without_a_rarity_field():
    """Regression: starGiftAttributeOriginalDetails has no `rarity`.

    Every other StarGiftAttribute constructor carries one, so reading `attr.rarity` directly looks
    safe and is not -- the original-details variant raises AttributeError, and it is the one
    constructor the parser explicitly branches on.
    """
    attr = raw.types.StarGiftAttributeOriginalDetails(
        recipient_id=raw.types.PeerUser(user_id=1),
        date=1_700_000_000,
    )
    parsed = await types.GiftAttribute._parse(None, attr, {}, {})

    assert parsed.rarity is None
    assert parsed.type == enums.GiftAttributeType.ORIGINAL_DETAILS


# GiftResalePrice is write-only: it is how a caller *sets* a resale price, so it has write() and
# no _parse().


def test_star_resale_price_writes_a_stars_amount():
    written = types.GiftResalePriceStar(star_count=5).write()
    assert isinstance(written, raw.types.StarsAmount)
    assert written.amount == 5


def test_ton_resale_price_writes_a_ton_amount():
    written = types.GiftResalePriceTon(toncoin_cent_count=7).write()
    assert isinstance(written, raw.types.StarsTonAmount)
    assert written.amount == 7
