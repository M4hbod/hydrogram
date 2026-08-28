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

from pyrogram import raw
from pyrogram.types.object import Object


class LinkPreviewOptions(Object):
    """Describes how a link preview should be generated for a message.

    Replaces the flat ``disable_web_page_preview`` parameter, which could only turn previews off.

    Parameters:
        is_disabled (``bool``, *optional*):
            True if the link preview is disabled.

        url (``str``, *optional*):
            URL to use for the link preview. If empty, the first URL found in the message text is
            used.

        prefer_small_media (``bool``, *optional*):
            True if the media in the preview should be shrunk. Ignored if the message contains no
            preview, or if the preview media cannot be resized.

        prefer_large_media (``bool``, *optional*):
            True if the media in the preview should be enlarged. Ignored under the same conditions
            as *prefer_small_media*.

        show_above_text (``bool``, *optional*):
            True if the preview should be shown above the message text rather than below it.
    """

    def __init__(
        self,
        *,
        is_disabled: bool | None = None,
        url: str | None = None,
        prefer_small_media: bool | None = None,
        prefer_large_media: bool | None = None,
        show_above_text: bool | None = None,
    ):
        super().__init__()

        self.is_disabled = is_disabled
        self.url = url
        self.prefer_small_media = prefer_small_media
        self.prefer_large_media = prefer_large_media
        self.show_above_text = show_above_text

    @staticmethod
    def _parse(
        media: raw.types.MessageMediaWebPage,
        url: str | None = None,
        invert_media: bool | None = None,
    ) -> LinkPreviewOptions | None:
        """Build the options from an incoming message's media.

        A ``WebPageNotModified`` carries no URL, so it is treated as "no preview information"
        rather than as a preview with an empty URL.
        """
        if isinstance(media, raw.types.MessageMediaWebPage) and not isinstance(
            media.webpage, raw.types.WebPageNotModified
        ):
            return LinkPreviewOptions(
                is_disabled=False,
                url=media.webpage.url,
                prefer_small_media=media.force_small_media,
                prefer_large_media=media.force_large_media,
                show_above_text=invert_media,
            )

        if url:
            return LinkPreviewOptions(is_disabled=True, url=url, show_above_text=invert_media)

        return None
