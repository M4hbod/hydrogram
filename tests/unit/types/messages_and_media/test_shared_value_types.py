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

"""The stage-4.0 shared value types.

These are wanted by more than one feature group, so they are ported once and tested once. Each test
feeds a hand-built raw object into `_parse`, or checks what `write()` puts on the wire -- no
network, no recorded fixtures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pyrogram import raw, types

# --- auctions ---------------------------------------------------------------


# `_parse` lives on the concrete states, not on the AuctionState base -- the base is only the
# common type the two share.


def test_auction_state_base_has_no_parser():
    assert not hasattr(types.AuctionState, "_parse")


@pytest.mark.parametrize("state", [types.AuctionStateActive, types.AuctionStateFinished])
def test_each_concrete_auction_state_parses(state):
    assert callable(state._parse)


def test_gift_auction_parses_from_a_star_gift():
    # auction_slug, gifts_per_round and auction_start_date all sit behind flags.11, so a gift
    # that carries one carries all three.
    auction = types.GiftAuction._parse(
        raw.types.StarGift(
            id=1,
            sticker=raw.types.DocumentEmpty(id=0),
            stars=10,
            convert_stars=5,
            auction_slug="a1",
            gifts_per_round=3,
            auction_start_date=1_700_000_000,
        )
    )
    assert auction is not None
    assert auction.id == "a1"
    assert auction.gifts_per_round == 3
    assert auction.start_date.tzinfo is not None, "dates must be aware UTC"


def test_gift_auction_is_none_when_the_gift_is_not_auctioned():
    gift = raw.types.StarGift(
        id=1, sticker=raw.types.DocumentEmpty(id=0), stars=10, convert_stars=5
    )
    assert types.GiftAuction._parse(gift) is None


# --- purchase limits --------------------------------------------------------


def test_purchase_limit_parses_both_counts():
    limit = types.GiftPurchaseLimit._parse(100, 40)
    assert (limit.total_count, limit.remaining_count) == (100, 40)


def test_purchase_limit_is_none_when_unlimited():
    assert types.GiftPurchaseLimit._parse(None, None) is None


# --- prices -----------------------------------------------------------------


def test_labeled_price_round_trips():
    parsed = types.LabeledPrice._parse(raw.types.LabeledPrice(label="Item", amount=250))
    assert (parsed.label, parsed.amount) == ("Item", 250)

    written = parsed.write()
    assert isinstance(written, raw.types.LabeledPrice)
    assert (written.label, written.amount) == ("Item", 250)


def test_suggested_post_star_price_round_trips():
    parsed = types.SuggestedPostPrice._parse(raw.types.StarsAmount(amount=9, nanos=0))
    assert isinstance(parsed, types.SuggestedPostPriceStar)
    assert parsed.star_count == 9
    assert parsed.write().amount == 9


def test_suggested_post_parameters_writes_a_suggested_post():
    params = types.SuggestedPostParameters(
        price=types.SuggestedPostPriceStar(star_count=3),
        send_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    written = params.write()
    assert isinstance(written, raw.types.SuggestedPost)


# --- folders ----------------------------------------------------------------


def test_folder_invite_link_parses():
    link = types.FolderInviteLink._parse(
        raw.types.ExportedChatlistInvite(title="T", url="https://t.me/addlist/x", peers=[])
    )
    assert link.invite_link == "https://t.me/addlist/x"
    assert link.name == "T"


# --- invoices ---------------------------------------------------------------


@pytest.mark.parametrize("is_test", [True, False])
def test_invoice_keeps_its_flags(is_test):
    invoice = types.Invoice(currency="XTR", is_test=is_test, title="t", total_amount=5)
    assert invoice.is_test is is_test
    assert invoice.currency == "XTR"


def sticker_document(doc_id: int = 1):
    """A Document a Sticker can be parsed from.

    DocumentEmpty has no `attributes`, and the gift parsers index into it unconditionally.
    """
    return raw.types.Document(
        id=doc_id,
        access_hash=0,
        file_reference=b"",
        date=0,
        mime_type="image/webp",
        size=0,
        dc_id=1,
        # Thumbnail._parse iterates thumbs unconditionally; a real Document always has the field.
        thumbs=[],
        attributes=[
            raw.types.DocumentAttributeFilename(file_name="s.webp"),
            # Sticker._parse indexes DocumentAttributeCustomEmoji when there is no
            # DocumentAttributeSticker, so one of the two has to be present.
            raw.types.DocumentAttributeSticker(
                alt="🎁", stickerset=raw.types.InputStickerSetEmpty()
            ),
        ],
    )


# --- Gift -------------------------------------------------------------------
#
# Gift._parse dispatches on the raw constructor. The mutable-default landmine it shipped with
# (`users: dict = {}`) is gone; each parser normalises its own mapping.


async def test_gift_parse_dispatches_on_the_constructor():
    gift = await types.Gift._parse(
        None,
        raw.types.StarGift(
            id=42,
            sticker=sticker_document(),
            stars=10,
            convert_stars=5,
        ),
    )
    assert gift is not None
    assert gift.id == 42


async def test_gift_parse_returns_none_for_an_unknown_constructor():
    assert await types.Gift._parse(None, raw.types.DocumentEmpty(id=0)) is None


async def test_gift_parse_does_not_share_state_between_calls():
    """Regression: users/chats were mutable default arguments shared by every call."""
    star_gift = raw.types.StarGift(id=1, sticker=sticker_document(), stars=1, convert_stars=1)
    first = await types.Gift._parse(None, star_gift)
    second = await types.Gift._parse(None, star_gift)
    assert first is not second


async def test_gift_keeps_its_raw_object_but_hides_it_from_str():
    gift = await types.Gift._parse(
        None,
        raw.types.StarGift(id=7, sticker=sticker_document(), stars=1, convert_stars=1),
    )
    assert gift.raw is not None
    assert "raw" not in json.loads(str(gift))


# --- Folder -----------------------------------------------------------------


async def test_default_folder_is_not_parsed():
    """DialogFilterDefault is the "All chats" pseudo-folder and has no contents."""
    assert await types.Folder._parse(None, raw.types.DialogFilterDefault(), {}, {}) is None


async def test_missing_folder_is_none():
    assert await types.Folder._parse(None, None, {}, {}) is None


async def test_folder_parses_its_identity_and_empty_peer_lists():
    folder = await types.Folder._parse(
        None,
        raw.types.DialogFilter(
            id=3,
            title=raw.types.TextWithEntities(text="Work", entities=[]),
            pinned_peers=[],
            include_peers=[],
            exclude_peers=[],
        ),
        {},
        {},
    )
    assert folder.id == 3
    # Empty peer lists collapse to None rather than an empty List, so callers test truthiness.
    assert not folder.pinned_chats
    assert not folder.included_chats
