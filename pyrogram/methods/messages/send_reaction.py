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

import pyrogram
from pyrogram import raw


class SendReaction:
    async def send_reaction(
        self: pyrogram.Client,
        chat_id: int | str,
        message_id: int | None = None,
        emoji: int | str | list[int | str] | None = None,
        story_id: int | None = None,
        big: bool = False,
    ) -> bool:
        """Send a reaction to a message or a story.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            message_id (``int``, *optional*):
                Identifier of the message. Required unless ``story_id`` is given.

            emoji (``int`` | ``str`` | List of ``int`` | ``str``, *optional*):
                Reaction emoji. An ``int`` is a custom emoji document id, a ``str``
                is a plain one, and a list sends several at once (Premium accounts).
                Pass nothing to retract the reaction.

            story_id (``int``, *optional*):
                Identifier of the story to react to, instead of a message.

            big (``bool``, *optional*):
                Pass True to show a bigger and longer reaction.
                Defaults to False. Ignored for a story.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                # Send a reaction
                await app.send_reaction(chat_id, message_id, "🔥")

                # Send a custom emoji reaction
                await app.send_reaction(chat_id, message_id, 5319161050128459957)

                # React to a story
                await app.send_reaction(chat_id, story_id=story_id, emoji="❤️")

                # Retract a reaction
                await app.send_reaction(chat_id, message_id)
        """
        reactions = _parse_reactions(emoji)

        if story_id is not None:
            rpc = raw.functions.stories.SendReaction(
                peer=await self.resolve_peer(chat_id),
                story_id=story_id,
                # A story takes exactly one reaction, and retracting it is an
                # explicit "empty" rather than the absence messages use.
                reaction=reactions[0] if reactions else raw.types.ReactionEmpty(),
            )
        else:
            rpc = raw.functions.messages.SendReaction(
                peer=await self.resolve_peer(chat_id),
                msg_id=message_id,
                reaction=reactions,
                big=big,
            )

        await self.invoke(rpc)

        return True


def _parse_reactions(emoji: int | str | list[int | str] | None) -> list | None:
    """An int is a custom emoji document id; a str is a plain one."""
    if not emoji:
        return None

    if not isinstance(emoji, list):
        emoji = [emoji]

    return [
        raw.types.ReactionCustomEmoji(document_id=one)
        if isinstance(one, int)
        else raw.types.ReactionEmoji(emoticon=one)
        for one in emoji
    ]
