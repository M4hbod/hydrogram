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

"""The filters added for parity, driven with hand-built objects.

Each is a one-liner, and each one-liner reads a differently named attribute --
which is exactly the kind of thing that is wrong without ever raising.
"""

from __future__ import annotations

import inspect

import pytest

from pyrogram import enums, filters, types

CLIENT = None


def message(**kwargs) -> types.Message:
    return types.Message(id=1, **kwargs)


async def matches(flt, update) -> bool:
    # Filters here are plain functions; the parameterised ones are coroutines.
    result = flt(CLIENT, update)

    return bool(await result if inspect.isawaitable(result) else result)


@pytest.mark.parametrize(
    ("flt", "field", "value"),
    [
        (filters.chat_shared, "chat_shared", types.ChatShared(button_id=1, chat=None)),
        (filters.users_shared, "users_shared", types.UsersShared(button_id=1, users=[])),
        (filters.giveaway, "giveaway", object()),
        (filters.giveaway_winners, "giveaway_winners", object()),
        (filters.story, "story", object()),
        (filters.gift, "gift", object()),
        (filters.gift_code, "premium_gift_code", object()),
        (filters.successful_payment, "successful_payment", object()),
        (filters.paid_message, "send_paid_messages_stars", 5),
        (filters.ephemeral, "ephemeral_message_id", 7),
    ],
)
async def test_an_attribute_filter_matches_only_when_its_field_is_set(flt, field, value):
    assert await matches(flt, message(**{field: value}))
    assert not await matches(flt, message())


async def test_live_location_needs_a_live_period_not_just_a_location():
    still = types.Location(longitude=0.0, latitude=0.0)
    live = types.Location(longitude=0.0, latitude=0.0, live_period=60)

    assert not await matches(filters.live_location, message(location=still))
    assert await matches(filters.live_location, message(location=live))


@pytest.mark.parametrize("field", ["photo", "voice", "video", "video_note"])
async def test_self_destruction_reads_the_ttl_off_any_of_the_four_media(field):
    media = types.Photo(
        file_id="x", file_unique_id="x", width=1, height=1, file_size=1, date=None, ttl_seconds=5
    )

    assert await matches(filters.self_destruction, message(**{field: media}))


async def test_media_without_a_ttl_is_not_self_destructing():
    photo = types.Photo(file_id="x", file_unique_id="x", width=1, height=1, file_size=1, date=None)

    assert not await matches(filters.self_destruction, message(photo=photo))
    assert not await matches(filters.self_destruction, message())


async def test_quote_reads_through_to_the_message():
    assert await matches(filters.quote, message(quote=object()))
    assert not await matches(filters.quote, message())


async def test_business_matches_on_the_connection_id():
    assert await matches(filters.business, message(business_connection_id="c1"))
    assert not await matches(filters.business, message())


async def test_forum_and_admin_read_the_chat():
    forum = types.Chat(id=-100, type=enums.ChatType.SUPERGROUP, is_forum=True)
    admin = types.Chat(id=-100, type=enums.ChatType.SUPERGROUP, is_admin=True)
    plain = types.Chat(id=-100, type=enums.ChatType.SUPERGROUP)

    assert await matches(filters.forum, message(chat=forum))
    assert not await matches(filters.forum, message(chat=plain))
    assert await matches(filters.admin, message(chat=admin))
    assert not await matches(filters.admin, message(chat=plain))


async def test_direct_matches_the_direct_chat_type():
    direct = types.Chat(id=-100, type=enums.ChatType.DIRECT)
    private = types.Chat(id=7, type=enums.ChatType.PRIVATE)

    assert await matches(filters.direct, message(chat=direct))
    assert not await matches(filters.direct, message(chat=private))


async def test_sender_chat_matches_a_message_sent_on_behalf_of_a_chat():
    chat = types.Chat(id=-100, type=enums.ChatType.CHANNEL)

    assert await matches(filters.sender_chat, message(sender_chat=chat))
    assert not await matches(filters.sender_chat, message())


class Offer:
    def __init__(self, state):
        self.state = state


@pytest.mark.parametrize(
    ("flt", "state"),
    [
        (filters.gift_offer, enums.GiftPurchaseOfferState.PENDING),
        (filters.gift_offer_accepted, enums.GiftPurchaseOfferState.ACCEPTED),
        (filters.gift_offer_rejected, enums.GiftPurchaseOfferState.REJECTED),
    ],
)
async def test_a_gift_offer_filter_matches_only_its_own_state(flt, state):
    assert await matches(flt, message(upgraded_gift_purchase_offer=Offer(state)))

    for other in enums.GiftPurchaseOfferState:
        if other is not state:
            assert not await matches(flt, message(upgraded_gift_purchase_offer=Offer(other)))


async def test_a_rejection_service_message_counts_as_a_rejected_offer():
    # Two shapes mean the same thing, and only one of them carries an offer.
    assert await matches(
        filters.gift_offer_rejected, message(upgraded_gift_purchase_offer_rejected=object())
    )


class Topic:
    def __init__(self, topic_id):
        self.id = topic_id


async def test_topic_matches_only_the_ids_it_was_given():
    assert await matches(filters.topic(5), message(topic=Topic(5)))
    assert await matches(filters.topic([5, 6]), message(topic=Topic(6)))
    assert not await matches(filters.topic(5), message(topic=Topic(7)))
    assert not await matches(filters.topic(5), message())


# --- the filters that now work on more than a Message ----------------------


def inline_query(**kwargs) -> types.InlineQuery:
    kwargs.setdefault("from_user", None)

    return types.InlineQuery(
        id="1", query="q", offset="", chat_type=enums.ChatType.PRIVATE, **kwargs
    )


def callback_query(**kwargs) -> types.CallbackQuery:
    return types.CallbackQuery(id="1", from_user=None, chat_instance="x", **kwargs)


async def test_a_chat_type_filter_works_on_a_callback_query():
    group = types.Chat(id=-100, type=enums.ChatType.SUPERGROUP)
    query = callback_query(message=message(chat=group))

    assert await matches(filters.group, query)
    assert not await matches(filters.private, query)


async def test_a_chat_type_filter_does_not_raise_on_an_update_with_no_chat():
    # It used to raise ValueError on anything that was not a Message or a
    # CallbackQuery. Raising inside a filter kills the handler silently.
    query = inline_query()

    assert not await matches(filters.group, query)
    assert not await matches(filters.private, query)


async def test_outgoing_is_false_for_an_update_that_cannot_be_outgoing():
    query = inline_query()

    assert not await matches(filters.outgoing, query)
    assert await matches(filters.incoming, query)


async def test_bot_reads_the_sender_of_any_update_that_has_one():
    bot_user = types.User(id=7, is_bot=True)
    human = types.User(id=8, is_bot=False)

    assert await matches(filters.bot, inline_query(from_user=bot_user))
    assert not await matches(filters.bot, inline_query(from_user=human))
