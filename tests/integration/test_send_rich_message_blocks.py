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

"""Sending a block-based rich message against the live API.

The offline tests in ``tests/unit/types/messages_and_media/`` prove the blocks
serialise and round-trip through our own parser, which is as far as an offline
test can go: it cannot tell whether the *server* accepts the vector. Nothing in
the rich-message send path has ever been run against Telegram, so until this
passes once, treat block sending as unverified.

There are two tests because the reply shape differs by account type. A user
sending to their own private chat gets the ``UpdateShortSentMessage`` shortcut;
a bot gets a full ``Updates``. Only the bot exercises the branch that was
broken, so the user test alone would have passed while every bot send raised.

Set ``PYROGRAM_TEST_SESSION_STRING`` and ``PYROGRAM_TEST_CHAT_ID`` for the user
test, and ``PYROGRAM_TEST_BOT_TOKEN``, ``PYROGRAM_TEST_API_ID``,
``PYROGRAM_TEST_API_HASH`` and ``PYROGRAM_TEST_BOT_CHAT_ID`` for the bot one.
Credentials are read from the environment and never written to disk; both
clients are in-memory and every message they send is deleted again.
"""

from __future__ import annotations

import os

import pytest

from pyrogram import Client, types

SESSION_STRING = os.environ.get("PYROGRAM_TEST_SESSION_STRING")
CHAT_ID = os.environ.get("PYROGRAM_TEST_CHAT_ID")

# A bot is not an optional extra here. messages.SendMessage answers a user
# sending to their own private chat with the UpdateShortSentMessage shortcut,
# and a bot with a full Updates. Only the second shape reaches the parsing
# branch that was broken, so a user-session-only test can pass while every bot
# send raises.
BOT_TOKEN = os.environ.get("PYROGRAM_TEST_BOT_TOKEN")
API_ID = os.environ.get("PYROGRAM_TEST_API_ID")
API_HASH = os.environ.get("PYROGRAM_TEST_API_HASH")
BOT_CHAT_ID = os.environ.get("PYROGRAM_TEST_BOT_CHAT_ID")

pytestmark = pytest.mark.integration

needs_user = pytest.mark.skipif(
    not (SESSION_STRING and CHAT_ID),
    reason="PYROGRAM_TEST_SESSION_STRING and PYROGRAM_TEST_CHAT_ID are not set",
)
needs_bot = pytest.mark.skipif(
    not (BOT_TOKEN and API_ID and API_HASH and BOT_CHAT_ID),
    reason=(
        "PYROGRAM_TEST_BOT_TOKEN, PYROGRAM_TEST_API_ID, PYROGRAM_TEST_API_HASH and "
        "PYROGRAM_TEST_BOT_CHAT_ID are not set"
    ),
)


def panel() -> list[types.RichBlock]:
    """One of each construct the block form exists for."""
    return [
        types.RichBlockSectionHeading(text="Rich message smoke test", size=2),
        types.RichBlockParagraph(
            text=[
                "sent by ",
                types.RichTextBold(text="pyrogram"),
                " as ",
                types.RichTextCode(text="blocks"),
            ]
        ),
        types.RichBlockTable(
            cells=[
                [
                    types.RichBlockTableCell(text="Field", is_header=True),
                    types.RichBlockTableCell(text="Value", is_header=True, align="right"),
                ],
                [
                    types.RichBlockTableCell(text="Codec"),
                    types.RichBlockTableCell(text="FLAC", align="right"),
                ],
            ],
            is_bordered=True,
            is_striped=True,
        ),
        types.RichBlockList(
            items=[
                types.RichBlockListItem(
                    label="•",
                    blocks=[types.RichBlockParagraph(text="Checked")],
                    has_checkbox=True,
                    is_checked=True,
                ),
                types.RichBlockListItem(
                    label="•",
                    blocks=[types.RichBlockParagraph(text="Unchecked")],
                    has_checkbox=True,
                ),
            ]
        ),
        types.RichBlockDetails(
            summary="Collapsed section",
            blocks=[types.RichBlockParagraph(text="Only visible when opened")],
        ),
        types.RichBlockBlockQuotation(
            blocks=[types.RichBlockParagraph(text="quoted")], credit="source"
        ),
        types.RichBlockDivider(),
    ]


async def send_and_check(client, chat_id: int):
    """Send the panel, assert the reply parses, then clean up."""
    message = None
    try:
        message = await client.send_rich_message(
            chat_id=chat_id, rich_message=types.InputRichMessage(blocks=panel())
        )

        assert message is not None, "the server accepted the send but the reply parsed to None"
        assert message.rich_message is not None, (
            "the message came back without a rich_message, so the blocks were dropped"
        )

        blocks = message.rich_message.blocks
        assert blocks, "the rich message came back with no blocks"
        assert not any(isinstance(b, types.RichBlockUnsupported) for b in blocks), (
            "the server echoed a block this library cannot parse"
        )
        return message
    finally:
        if message is not None:
            await client.delete_messages(chat_id, message.id)


@needs_bot
@pytest.mark.asyncio
async def test_a_bot_can_send_a_block_rich_message():
    """The shape that caught the bug: a bot gets Updates, not the shortcut."""
    client = Client(
        "rich-blocks-bot",
        api_id=int(API_ID),
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
    )

    await client.start()
    try:
        await send_and_check(client, int(BOT_CHAT_ID))
    finally:
        await client.stop()


@needs_user
@pytest.mark.asyncio
async def test_a_block_rich_message_is_accepted_by_the_server():
    client = Client("rich-blocks", session_string=SESSION_STRING, in_memory=True)

    await client.start()
    try:
        await send_and_check(client, int(CHAT_ID))
    finally:
        await client.stop()
