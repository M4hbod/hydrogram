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

"""Send methods must parse the reply a bot actually gets.

``tests/contract/test_every_method_builds_a_request.py`` drives every method as
far as ``invoke`` and stops, which is why fifteen methods could reach a request
correctly and then raise ``AttributeError`` on the reply.

A *user* sending to their own private chat gets ``UpdateShortSentMessage``, a
shortcut the methods do handle. A **bot** gets a full ``Updates``. Nothing
offline had ever fed a method that second shape, so the branch bots always take
had never run. These tests feed it.
"""

from __future__ import annotations

import pytest

import pyrogram
from pyrogram import raw, types, utils

SENT_MESSAGE = raw.types.Message(
    id=4270,
    peer_id=raw.types.PeerUser(user_id=7),
    date=1700000000,
    message="",
)


def bot_shaped_updates(message: raw.types.Message = SENT_MESSAGE) -> raw.types.Updates:
    """What messages.SendMessage returns to a bot."""
    return raw.types.Updates(
        updates=[raw.types.UpdateNewMessage(message=message, pts=1, pts_count=1)],
        users=[
            raw.types.User(id=7, first_name="Owner", access_hash=0, is_self=False, contact=False)
        ],
        chats=[],
        date=1700000000,
        seq=0,
    )


@pytest.fixture
async def client():
    # Built inside the running loop: on Python 3.9 the client's own primitives
    # bind to a loop at construction.
    app = pyrogram.Client("test", api_id=1, api_hash="x", in_memory=True)

    async def resolve_peer(*args, **kwargs):
        return raw.types.InputPeerUser(user_id=7, access_hash=0)

    app.resolve_peer = resolve_peer
    return app


def answer_with(app, reply):
    async def invoke(*args, **kwargs):
        return reply

    app.invoke = invoke


@pytest.mark.asyncio
async def test_send_rich_message_parses_the_reply_a_bot_gets(client):
    """The live failure: AttributeError: 'Updates' object has no attribute 'messages'."""
    answer_with(client, bot_shaped_updates())

    message = await client.send_rich_message(
        chat_id=7,
        rich_message=types.InputRichMessage(
            blocks=[
                types.RichBlockSectionHeading(text="Now Playing", size=2),
                types.RichBlockParagraph(text="by Artemis"),
            ]
        ),
    )

    assert message is not None, "the reply was parsed away to None"
    assert message.id == 4270


@pytest.mark.asyncio
async def test_send_rich_message_still_takes_the_user_shortcut(client):
    """A user sending to their own private chat gets UpdateShortSentMessage."""
    answer_with(
        client,
        raw.types.UpdateShortSentMessage(id=99, pts=1, pts_count=1, date=1700000000, out=True),
    )

    message = await client.send_rich_message(
        chat_id=7, rich_message=types.InputRichMessage(html="<b>hi</b>")
    )

    assert message is not None
    assert message.id == 99


@pytest.mark.asyncio
async def test_a_reply_carrying_no_new_message_is_not_an_error(client):
    answer_with(client, raw.types.Updates(updates=[], users=[], chats=[], date=0, seq=0))

    message = await client.send_rich_message(
        chat_id=7, rich_message=types.InputRichMessage(html="<b>hi</b>")
    )

    assert message is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda app: app.send_checklist(
                chat_id=7,
                checklist=types.InputChecklist(
                    title="t", tasks=[types.InputChecklistTask(id=1, text="a")]
                ),
            ),
            id="send_checklist",
        ),
        pytest.param(
            lambda app: app.send_screenshot_notification(chat_id=7),
            id="send_screenshot_notification",
        ),
        pytest.param(lambda app: app.set_chat_ttl(chat_id=7, ttl_seconds=60), id="set_chat_ttl"),
        pytest.param(
            lambda app: app.delete_poll_option(chat_id=7, message_id=1, option="1"),
            id="delete_poll_option",
        ),
    ],
)
async def test_the_method_parses_a_bot_shaped_reply(client, call):
    """Each of these passed the Updates straight to parse_messages and raised."""
    answer_with(client, bot_shaped_updates())

    result = await call(client)

    assert result is not None
    assert getattr(result, "id", None) == 4270


@pytest.mark.asyncio
async def test_an_updates_reply_yields_every_new_message(client):
    """The media-group methods return the whole list, not just the first."""
    second = raw.types.Message(
        id=4271, peer_id=raw.types.PeerUser(user_id=7), date=1700000000, message=""
    )
    reply = bot_shaped_updates()
    reply.updates.append(raw.types.UpdateNewMessage(message=second, pts=2, pts_count=1))

    messages = await utils.parse_messages_from_updates(client=client, updates=reply)

    assert [m.id for m in messages] == [4270, 4271]
