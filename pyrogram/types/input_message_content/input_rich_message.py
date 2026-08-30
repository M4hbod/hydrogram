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

from __future__ import annotations

from pyrogram import raw, types
from pyrogram.types.messages_and_media.rich_block import RichMessageMedia
from pyrogram.types.object import Object


class InputRichMessage(Object):
    """Describes the content of a rich message to send.

    Exactly one of ``blocks``, ``html`` or ``markdown`` must be given. ``blocks``
    is the structured form: it carries tables, lists with checkboxes, collapsible
    sections, headings, anchors, quotations, collages and media, using the same
    :obj:`~pyrogram.types.RichBlock` classes that reading a rich message returns.

    Parameters:
        blocks (List of :obj:`~pyrogram.types.RichBlock`, *optional*):
            Content of the rich message as structured blocks.

        html (``str``, *optional*):
            Content of the rich message to send described using HTML formatting.
            See `rich message formatting options <https://core.telegram.org/bots/api#rich-message-formatting-options>`__ for more details.

        markdown (``str``, *optional*):
            Content of the rich message to send described using Markdown formatting.
            See `rich message formatting options <https://core.telegram.org/bots/api#rich-message-formatting-options>`__ for more details.

        is_rtl (``bool``, *optional*):
            Pass *True* if the rich message must be shown right-to-left.

        skip_entity_detection (``bool``, *optional*):
            Pass *True* to skip automatic detection of entities
            (e.g., URLs, email addresses, username mentions, hashtags, cashtags, bot commands, or phone numbers) in the text.
    """

    def __init__(
        self,
        blocks: list[types.RichBlock] | None = None,
        html: str | None = None,
        markdown: str | None = None,
        is_rtl: bool | None = None,
        skip_entity_detection: bool | None = None,
    ):
        super().__init__()

        self.blocks = blocks
        self.html = html
        self.markdown = markdown
        self.is_rtl = is_rtl
        self.skip_entity_detection = skip_entity_detection

    def write(self) -> raw.base.InputRichMessage:
        if self.blocks:
            # A block names its media by id, so the blocks and the message's
            # photo and document vectors have to be built in one pass.
            media = RichMessageMedia()
            blocks = [types.RichBlock._write(block, media) for block in self.blocks]

            return raw.types.InputRichMessage(
                blocks=blocks,
                rtl=self.is_rtl,
                noautolink=self.skip_entity_detection,
                photos=media.photos or None,
                documents=media.documents or None,
            )

        if self.html:
            return raw.types.InputRichMessageHTML(
                html=self.html, rtl=self.is_rtl, noautolink=self.skip_entity_detection
            )

        if self.markdown:
            return raw.types.InputRichMessageMarkdown(
                markdown=self.markdown, rtl=self.is_rtl, noautolink=self.skip_entity_detection
            )

        raise ValueError("You must provide blocks, html or markdown in the rich message")
