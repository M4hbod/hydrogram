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

Set ``PYROGRAM_TEST_SESSION_STRING`` and ``PYROGRAM_TEST_CHAT_ID`` to run it.
The session string is read from the environment and never written to disk; the
client is in-memory and the message it sends is deleted again.
"""

from __future__ import annotations

import os

import pytest

from pyrogram import Client, types

SESSION_STRING = os.environ.get("PYROGRAM_TEST_SESSION_STRING")
CHAT_ID = os.environ.get("PYROGRAM_TEST_CHAT_ID")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (SESSION_STRING and CHAT_ID),
        reason="PYROGRAM_TEST_SESSION_STRING and PYROGRAM_TEST_CHAT_ID are not set",
    ),
]


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


@pytest.mark.asyncio
async def test_a_block_rich_message_is_accepted_by_the_server():
    client = Client("rich-blocks", session_string=SESSION_STRING, in_memory=True)

    await client.start()
    message = None
    try:
        message = await client.send_rich_message(
            chat_id=int(CHAT_ID),
            rich_message=types.InputRichMessage(blocks=panel()),
        )

        assert message is not None, "the server accepted the send but returned no message"
        assert message.rich_message is not None, (
            "the message came back without a rich_message, so the blocks were dropped"
        )

        blocks = message.rich_message.blocks
        assert blocks, "the rich message came back with no blocks"
        assert not any(isinstance(b, types.RichBlockUnsupported) for b in blocks), (
            "the server echoed a block this library cannot parse"
        )
    finally:
        if message is not None:
            await client.delete_messages(int(CHAT_ID), message.id)
        await client.stop()
