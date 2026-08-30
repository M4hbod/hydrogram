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

"""The dispatcher's routing table, driven with real raw updates.

A parser that raises is caught and logged by the handler worker, so a broken one
does not stop the client -- it just means that update type never reaches a
handler. That is why these are asserted here rather than noticed in production.
"""

from __future__ import annotations

import inspect
import pathlib

import pytest

import pyrogram
from pyrogram import enums, raw
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import (
    BusinessConnectionHandler,
    CallbackQueryHandler,
    ChatBoostHandler,
    ChatMemberUpdatedHandler,
    DeletedMessagesHandler,
    InlineQueryHandler,
    MessageReactionCountHandler,
    MessageReactionHandler,
    PreCheckoutQueryHandler,
    PurchasedPaidMediaHandler,
    ShippingQueryHandler,
    UserStatusHandler,
)


@pytest.fixture
def dispatcher():
    client = pyrogram.Client("test", api_id=1, api_hash="x", in_memory=True)

    # A callback query resolves the message its button sits under. That is a
    # round trip, and these tests are offline, so it is stubbed out -- the
    # subject here is the parse, not the fetch.
    async def get_messages(*args, **kwargs):
        return None

    async def resolve_peer(*args, **kwargs):
        return raw.types.InputPeerUser(user_id=7, access_hash=0)

    client.get_messages = get_messages
    client.resolve_peer = resolve_peer

    return Dispatcher(client)


async def dispatch(dispatcher: Dispatcher, update, users=None, chats=None):
    """Exactly what handler_worker does with one update."""
    parser = dispatcher.update_parsers[type(update)]
    parsed = parser(update, users or {}, chats or {})

    return await parsed if inspect.isawaitable(parsed) else parsed


async def test_deleted_messages_are_parsed(dispatcher):
    update = raw.types.UpdateDeleteMessages(messages=[11, 12], pts=1, pts_count=2)

    parsed, handler = await dispatch(dispatcher, update)

    assert handler is DeletedMessagesHandler
    assert [message.id for message in parsed] == [11, 12]
    assert parsed[0].chat is None


async def test_deleted_channel_messages_carry_their_chat(dispatcher):
    update = raw.types.UpdateDeleteChannelMessages(
        channel_id=1234567890, messages=[7], pts=1, pts_count=1
    )

    parsed, _handler = await dispatch(dispatcher, update)

    assert parsed[0].chat.id == -1001234567890
    assert parsed[0].chat.type is enums.ChatType.CHANNEL


async def test_user_status_is_parsed(dispatcher):
    update = raw.types.UpdateUserStatus(user_id=7, status=raw.types.UserStatusOnline(expires=0))

    parsed, handler = await dispatch(dispatcher, update)

    assert handler is UserStatusHandler
    assert parsed.id == 7
    assert parsed.status is enums.UserStatus.ONLINE


async def test_inline_query_is_parsed(dispatcher):
    user = raw.types.User(id=7, first_name="Test", access_hash=0)
    update = raw.types.UpdateBotInlineQuery(
        query_id=1,
        user_id=7,
        query="search",
        offset="",
        peer_type=raw.types.InlineQueryPeerTypePM(),
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: user})

    assert handler is InlineQueryHandler
    assert parsed.query == "search"
    assert parsed.from_user.id == 7


async def test_chat_member_update_is_parsed(dispatcher):
    user = raw.types.User(id=7, first_name="Test", access_hash=0)
    update = raw.types.UpdateChatParticipant(
        chat_id=99,
        date=1700000000,
        actor_id=7,
        user_id=7,
        qts=1,
        new_participant=raw.types.ChatParticipant(user_id=7, inviter_id=7, date=1700000000),
    )

    chat = raw.types.Chat(
        id=99, title="Group", photo=None, participants_count=1, date=1700000000, version=1
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: user}, chats={99: chat})

    assert handler is ChatMemberUpdatedHandler
    assert parsed.chat.id == -99


# --- the eight that parsed into types which did not exist -------------------
#
# Each of these routed an update to `pyrogram.types.X._parse`, where X was never
# ported. AttributeError inside the handler worker is logged and swallowed, so
# the only symptom was that the update type never arrived.

USER = raw.types.User(id=7, first_name="Test", access_hash=0)
CHANNEL = raw.types.Channel(
    id=1234567890, title="Channel", photo=None, date=1700000000, access_hash=0, broadcast=True
)


async def test_pre_checkout_query_is_parsed(dispatcher):
    update = raw.types.UpdateBotPrecheckoutQuery(
        query_id=1,
        user_id=7,
        payload=b"order-1",
        currency="XTR",
        total_amount=100,
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is PreCheckoutQueryHandler
    assert parsed.id == "1"
    assert parsed.invoice_payload == "order-1"
    assert parsed.total_amount == 100


async def test_a_pre_checkout_payload_that_is_not_text_stays_bytes(dispatcher):
    # Decoding with errors="ignore" would corrupt a binary payload, and the
    # answer has to echo it back exactly.
    update = raw.types.UpdateBotPrecheckoutQuery(
        query_id=1, user_id=7, payload=b"\xff\xfe", currency="XTR", total_amount=1
    )

    parsed, _handler = await dispatch(dispatcher, update, users={7: USER})

    assert parsed.invoice_payload == b"\xff\xfe"


async def test_shipping_query_is_parsed(dispatcher):
    update = raw.types.UpdateBotShippingQuery(
        query_id=2,
        user_id=7,
        payload=b"ship-1",
        shipping_address=raw.types.PostAddress(
            street_line1="1 Road",
            street_line2="",
            city="Town",
            state="",
            country_iso2="GB",
            post_code="AA1 1AA",
        ),
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is ShippingQueryHandler
    assert parsed.invoice_payload == "ship-1"
    assert parsed.shipping_address.city == "Town"


async def test_message_reaction_update_is_parsed(dispatcher):
    update = raw.types.UpdateBotMessageReaction(
        peer=raw.types.PeerUser(user_id=7),
        msg_id=5,
        date=1700000000,
        actor=raw.types.PeerUser(user_id=7),
        old_reactions=[],
        new_reactions=[raw.types.ReactionEmoji(emoticon="👍")],
        qts=1,
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is MessageReactionHandler
    assert parsed.message_id == 5
    assert [reaction.emoji for reaction in parsed.new_reaction] == ["👍"]


async def test_message_reaction_count_update_is_parsed(dispatcher):
    update = raw.types.UpdateBotMessageReactions(
        peer=raw.types.PeerChannel(channel_id=1234567890),
        msg_id=5,
        date=1700000000,
        reactions=[
            raw.types.ReactionCount(reaction=raw.types.ReactionEmoji(emoticon="🔥"), count=3)
        ],
        qts=1,
    )

    parsed, handler = await dispatch(dispatcher, update, chats={1234567890: CHANNEL})

    assert handler is MessageReactionCountHandler
    assert parsed.reactions[0].count == 3


async def test_chat_boost_update_is_parsed(dispatcher):
    update = raw.types.UpdateBotChatBoost(
        peer=raw.types.PeerChannel(channel_id=1234567890),
        boost=raw.types.Boost(id="b1", date=1700000000, expires=1800000000, user_id=7),
        qts=1,
    )

    parsed, handler = await dispatch(
        dispatcher, update, users={7: USER}, chats={1234567890: CHANNEL}
    )

    assert handler is ChatBoostHandler
    assert parsed.chat.id == -1001234567890
    assert parsed.boost.id == "b1"


async def test_purchased_paid_media_update_is_parsed(dispatcher):
    update = raw.types.UpdateBotPurchasedPaidMedia(payload="paid-1", user_id=7, qts=1)

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is PurchasedPaidMediaHandler
    assert parsed.payload == "paid-1"
    assert parsed.from_user.id == 7


async def test_business_connection_update_is_parsed(dispatcher):
    update = raw.types.UpdateBotBusinessConnect(
        connection=raw.types.BotBusinessConnection(
            connection_id="c1", user_id=7, dc_id=2, date=1700000000
        ),
        qts=1,
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is BusinessConnectionHandler
    assert parsed.id == "c1"
    assert parsed.is_enabled is True


# --- callback queries -------------------------------------------------------
#
# The one update kind this file did not cover, because callback queries predate
# the layer-229 port every other test here was written for. The dispatcher was
# calling CallbackQuery._parse with a fourth `chats` argument it does not take,
# so every button press raised TypeError inside the handler worker -- logged,
# swallowed, and invisible except that the buttons did nothing.


async def test_a_callback_query_is_parsed(dispatcher):
    update = raw.types.UpdateBotCallbackQuery(
        query_id=1,
        user_id=7,
        peer=raw.types.PeerUser(user_id=7),
        msg_id=5,
        chat_instance=99,
        data=b"pressed",
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is CallbackQueryHandler
    assert parsed.id == "1"
    assert parsed.data == "pressed"
    assert parsed.from_user.id == 7


async def test_an_inline_callback_query_is_parsed(dispatcher):
    update = raw.types.UpdateInlineBotCallbackQuery(
        query_id=2,
        user_id=7,
        msg_id=raw.types.InputBotInlineMessageID(dc_id=2, id=1, access_hash=0),
        chat_instance=99,
        data=b"inline",
    )

    parsed, handler = await dispatch(dispatcher, update, users={7: USER})

    assert handler is CallbackQueryHandler
    assert parsed.data == "inline"
    assert parsed.inline_message_id is not None


async def test_callback_data_that_is_not_text_stays_bytes(dispatcher):
    # Decoding with errors="ignore" would corrupt binary payloads, and the
    # answer has to match what the button carried.
    update = raw.types.UpdateBotCallbackQuery(
        query_id=3,
        user_id=7,
        peer=raw.types.PeerUser(user_id=7),
        msg_id=5,
        chat_instance=99,
        data=b"\xff\xfe",
    )

    parsed, _handler = await dispatch(dispatcher, update, users={7: USER})

    assert parsed.data == b"\xff\xfe"


def test_every_routed_update_kind_has_a_test_here():
    """The gap this file had: callback queries were routed but never driven.

    Every other update kind gained in the layer-229 port got a test here;
    callback queries predate it, so nobody thought to add one, and the broken
    parser sat behind a `TypeError` the handler worker swallows.
    """
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    client = pyrogram.Client("test", api_id=1, api_hash="x", in_memory=True)
    routed = {update.__name__ for update in Dispatcher(client).update_parsers}

    # Named individually so adding a routed update type without a test fails.
    untested = sorted(name for name in routed if name not in source)

    assert not untested, f"these update types are routed but never driven in this file: {untested}"


# --- everything else the dispatcher routes ---------------------------------
#
# One fixture per routed update type. The assertion is deliberately weak -- the
# parser runs and hands back the handler it is registered for -- because the
# failure this catches is not a wrong value, it is an exception the handler
# worker logs and swallows, which looks exactly like "that update never
# arrives". The named-field tests above cover the values.

MESSAGE = raw.types.Message(
    id=1, peer_id=raw.types.PeerUser(user_id=7), date=1700000000, message="hi"
)
BUSINESS_MESSAGE = raw.types.Message(
    id=1, peer_id=raw.types.PeerUser(user_id=7), date=1700000000, message="biz"
)
INLINE_ID = raw.types.InputBotInlineMessageID(dc_id=2, id=1, access_hash=0)


def routed_updates():
    return {
        "UpdateNewMessage": raw.types.UpdateNewMessage(message=MESSAGE, pts=1, pts_count=1),
        "UpdateNewChannelMessage": raw.types.UpdateNewChannelMessage(
            message=MESSAGE, pts=1, pts_count=1
        ),
        "UpdateNewScheduledMessage": raw.types.UpdateNewScheduledMessage(message=MESSAGE),
        "UpdateNewEphemeralMessage": raw.types.UpdateNewEphemeralMessage(message=MESSAGE),
        "UpdateEditMessage": raw.types.UpdateEditMessage(message=MESSAGE, pts=1, pts_count=1),
        "UpdateEditChannelMessage": raw.types.UpdateEditChannelMessage(
            message=MESSAGE, pts=1, pts_count=1
        ),
        "UpdateEditEphemeralMessage": raw.types.UpdateEditEphemeralMessage(message=MESSAGE),
        "UpdateDeleteEphemeralMessages": raw.types.UpdateDeleteEphemeralMessages(
            peer=raw.types.PeerUser(user_id=7), ids=[1]
        ),
        "UpdateBotNewBusinessMessage": raw.types.UpdateBotNewBusinessMessage(
            connection_id="c1", message=BUSINESS_MESSAGE, qts=1
        ),
        "UpdateBotEditBusinessMessage": raw.types.UpdateBotEditBusinessMessage(
            connection_id="c1", message=BUSINESS_MESSAGE, qts=1
        ),
        "UpdateBotDeleteBusinessMessage": raw.types.UpdateBotDeleteBusinessMessage(
            connection_id="c1", peer=raw.types.PeerUser(user_id=7), messages=[1], qts=1
        ),
        "UpdateBusinessBotCallbackQuery": raw.types.UpdateBusinessBotCallbackQuery(
            query_id=1, user_id=7, connection_id="c1", message=MESSAGE, chat_instance=9
        ),
        "UpdateEphemeralBotCallbackQuery": raw.types.UpdateEphemeralBotCallbackQuery(
            query_id=1, user_id=7, msg_id=1, data=b"d", message=MESSAGE
        ),
        "UpdateBotInlineSend": raw.types.UpdateBotInlineSend(user_id=7, query="q", id="r"),
        "UpdateBotChatInviteRequester": raw.types.UpdateBotChatInviteRequester(
            peer=raw.types.PeerChannel(channel_id=1234567890),
            date=1700000000,
            user_id=7,
            about="hi",
            invite=raw.types.ChatInviteExported(
                link="https://t.me/+x", admin_id=7, date=1700000000
            ),
            qts=1,
        ),
        "UpdateChannelParticipant": raw.types.UpdateChannelParticipant(
            channel_id=1234567890, date=1700000000, actor_id=7, user_id=7, qts=1
        ),
        "UpdateManagedBot": raw.types.UpdateManagedBot(user_id=7, bot_id=8, qts=1),
        "UpdateMessagePoll": raw.types.UpdateMessagePoll(
            poll_id=1,
            results=raw.types.PollResults(),
        ),
        "UpdateMessagePollVote": raw.types.UpdateMessagePollVote(
            poll_id=1,
            peer=raw.types.PeerUser(user_id=7),
            options=[b"0"],
            positions=[0],
            qts=1,
        ),
        "UpdateStory": raw.types.UpdateStory(
            peer=raw.types.PeerUser(user_id=7),
            story=raw.types.StoryItem(
                id=1,
                date=1700000000,
                expire_date=1800000000,
                media=raw.types.MessageMediaEmpty(),
            ),
        ),
        "UpdateBotGuestChatQuery": raw.types.UpdateBotGuestChatQuery(
            query_id=1, message=MESSAGE, qts=1
        ),
    }


ROUTED = sorted(routed_updates().items())


@pytest.mark.parametrize(("name", "update"), ROUTED, ids=[name for name, _ in ROUTED])
async def test_the_routed_update_parses_without_raising(dispatcher, name, update):
    chats = {
        1234567890: raw.types.Channel(
            id=1234567890,
            title="Channel",
            photo=None,
            date=1700000000,
            access_hash=0,
            broadcast=True,
        )
    }

    _parsed, handler = await dispatch(dispatcher, update, users={7: USER, 8: USER}, chats=chats)

    assert handler is not type(None), f"{name} produced no handler"
