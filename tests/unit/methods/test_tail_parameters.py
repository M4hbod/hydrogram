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

"""The last thirteen parameters, each driven into the request it builds.

``test_parameters_are_used`` proves a parameter is named in the body;
``test_raw_keywords`` proves the field exists. Neither proves the value reaches
the right field, which is the thing that is actually wrong when a parameter is
wired to the wrong place -- and ``send_paid_media`` had done exactly that with
``direct_messages_topic_id``.
"""

from __future__ import annotations

import pytest

from pyrogram import Client, enums, raw, types
from pyrogram.parser import Parser

# A real sticker file id, so send_sticker takes its cached-media path rather
# than trying to upload.
STICKER = "CAACAgEAAx0CAAGgr9AAAgmWX7b6uFeLlhXEgYrM8pIbGaQKRQ0AAswBAALjeAQAAbeooNv_tb6-HgQ"


class RecordedError(Exception):
    """Raised once the request is captured, to stop before the reply is parsed."""


class Recorder:
    """Captures the request a method builds instead of sending it.

    It stops at the request rather than returning a plausible reply, because
    modelling replies well enough for `Message._parse` means building most of a
    Client -- and the request is the whole subject here.
    """

    def __init__(self):
        self.sent = []
        self.parse_mode = enums.ParseMode.DEFAULT
        self.parser = Parser(self)
        self.me = None

    async def invoke(self, query, *args, **kwargs):
        self.sent.append(query)

        raise RecordedError

    async def resolve_peer(self, peer_id=None):
        return raw.types.InputPeerUser(user_id=7, access_hash=0)

    @staticmethod
    def rnd_id():
        return 1


@pytest.fixture
def client():
    return Recorder()


def only(recorder):
    assert len(recorder.sent) == 1, f"expected one request, got {len(recorder.sent)}"

    return recorder.sent[0]


def unwrap(request):
    """The innermost query, past any InvokeWith* wrapper."""
    while hasattr(request, "query"):
        request = request.query

    return request


async def capture(recorder, coroutine):
    with pytest.raises(RecordedError):
        await coroutine

    return unwrap(only(recorder))


async def test_add_contact_sends_the_note(client):
    request = await capture(client, Client.add_contact(client, 7, "First", note="a private note"))

    assert request.note.text == "a private note"


async def test_add_contact_without_a_note_sends_none(client):
    request = await capture(client, Client.add_contact(client, 7, "First"))

    assert request.note is None


async def test_search_messages_offsets_from_the_given_id(client):
    async def drain():
        async for _ in Client.search_messages(client, -100123, offset_id=500, limit=1):
            break

    request = await capture(client, drain())

    assert request.offset_id == 500


async def test_get_messages_pinned_asks_for_the_pinned_message(client):
    request = await capture(client, Client.get_messages(client, -100123, pinned=True))

    assert isinstance(request.id[0], raw.types.InputMessagePinned)


async def test_get_messages_reply_asks_for_what_was_replied_to(client):
    request = await capture(
        client, Client.get_messages(client, -100123, message_ids=5, reply=True)
    )

    assert isinstance(request.id[0], raw.types.InputMessageReplyTo)
    assert request.id[0].id == 5


async def test_get_messages_without_reply_asks_for_the_message_itself(client):
    request = await capture(client, Client.get_messages(client, -100123, message_ids=5))

    assert isinstance(request.id[0], raw.types.InputMessageID)


async def test_forward_messages_can_forward_as_a_reply(client):
    request = await capture(
        client,
        Client.forward_messages(
            client,
            -100123,
            -100456,
            message_ids=[1],
            reply_parameters=types.ReplyParameters(message_id=99),
        ),
    )

    assert isinstance(request.reply_to, raw.types.InputReplyToMessage)
    assert request.reply_to.reply_to_msg_id == 99


async def test_send_poll_puts_the_description_in_the_message_body(client):
    request = await capture(
        client,
        Client.send_poll(client, -100123, "Question?", ["a", "b"], description="why I ask"),
    )

    assert request.message == "why I ask"


async def test_send_poll_without_a_description_sends_an_empty_body(client):
    request = await capture(client, Client.send_poll(client, -100123, "Question?", ["a", "b"]))

    assert not request.message


async def test_send_poll_flags_reach_the_poll(client):
    request = await capture(
        client,
        Client.send_poll(
            client,
            -100123,
            "Question?",
            ["a", "b"],
            shuffle_options=True,
            allows_revoting=False,
            hide_results_until_closes=True,
            members_only=True,
            allow_adding_options=True,
            country_codes=["GB"],
        ),
    )
    poll = request.media.poll

    assert poll.shuffle_answers is True
    assert poll.revoting_disabled is True
    assert poll.hide_results_until_close is True
    assert poll.subscribers_only is True
    assert poll.open_answers is True
    assert poll.countries_iso2 == ["GB"]


async def test_send_poll_correct_option_ids_beats_the_single_id(client):
    request = await capture(
        client,
        Client.send_poll(
            client, -100123, "Q?", ["a", "b", "c"], correct_option_ids=[0, 2], is_anonymous=False
        ),
    )

    assert request.media.correct_answers == [bytes([0]), bytes([2])]


async def test_edit_message_text_sends_rich_content(client):
    request = await capture(
        client,
        Client.edit_message_text(
            client, -100123, 1, "text", rich_message=types.InputRichMessage(html="<b>rich</b>")
        ),
    )

    assert request.rich_message is not None


async def test_edit_message_text_without_rich_content_sends_none(client):
    request = await capture(client, Client.edit_message_text(client, -100123, 1, "text"))

    assert request.rich_message is None


async def test_send_sticker_carries_a_caption(client):
    # The caption goes through the same parser as any other media caption,
    # which is why send_sticker needed a parse_mode of its own.
    request = await capture(
        client, Client.send_sticker(client, -100123, STICKER, caption="a caption")
    )

    assert request.message == "a caption"


async def test_send_sticker_without_a_caption_sends_an_empty_one(client):
    request = await capture(client, Client.send_sticker(client, -100123, STICKER))

    assert not request.message
