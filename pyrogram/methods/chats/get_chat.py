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
from pyrogram import raw, types, utils


class GetChat:
    async def get_chat(
        self: pyrogram.Client,
        chat_id: int | str,
        force_full: bool = True,
    ) -> types.Chat | types.ChatPreview:
        """Get up to date information about a chat.

        Information include current name of the user for one-on-one conversations, current username of a user, group or
        channel, etc.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                Unique identifier for the target chat in form of a *t.me/joinchat/* link, identifier (int) or username
                of the target channel/supergroup (in the format @username).

            force_full (``bool``, *optional*):
                Pass False to return the cached chat rather than asking the server for the full one.

        Returns:
            :obj:`~pyrogram.types.Chat` | :obj:`~pyrogram.types.ChatPreview`: On success, if you've already joined the chat, a chat object is returned,
            otherwise, a chat preview object is returned.

        Raises:
            ValueError: In case the chat invite link points to a chat you haven't joined yet.

        Example:
            .. code-block:: python

                chat = await app.get_chat("pyrogram")
                print(chat)
        """
        if match := self.INVITE_LINK_RE.match(str(chat_id)):
            r = await self.invoke(raw.functions.messages.CheckChatInvite(hash=match.group(1)))

            if isinstance(r, raw.types.ChatInvite):
                return types.ChatPreview._parse(self, r)

            await self.fetch_peers([r.chat])

            if isinstance(r.chat, raw.types.Chat):
                chat_id = -r.chat.id

            if isinstance(r.chat, raw.types.Channel):
                chat_id = utils.get_channel_id(r.chat.id)

        peer = await self.resolve_peer(chat_id)

        if not force_full:
            # The short form is one request and carries no description, pinned
            # message, or member count -- but it is what a caller who only needs
            # a title and an id should be paying for.
            if isinstance(peer, raw.types.InputPeerChannel):
                r = await self.invoke(raw.functions.channels.GetChannels(id=[peer]))
            elif isinstance(peer, (raw.types.InputPeerUser, raw.types.InputPeerSelf)):
                r = await self.invoke(raw.functions.users.GetUsers(id=[peer]))
            else:
                r = await self.invoke(raw.functions.messages.GetChats(id=[peer.chat_id]))

            return types.Chat._parse_chat(
                self, r.chats[0] if isinstance(r, raw.types.messages.Chats) else r[0]
            )

        if isinstance(peer, raw.types.InputPeerChannel):
            r = await self.invoke(raw.functions.channels.GetFullChannel(channel=peer))
        elif isinstance(peer, (raw.types.InputPeerUser, raw.types.InputPeerSelf)):
            r = await self.invoke(raw.functions.users.GetFullUser(id=peer))
        else:
            r = await self.invoke(raw.functions.messages.GetFullChat(chat_id=peer.chat_id))

        return await types.Chat._parse_full(self, r)
