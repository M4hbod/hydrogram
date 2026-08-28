#  Pyrogram - Telegram MTProto API Client Library for Python
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

import logging
from typing import TYPE_CHECKING

import pyrogram
from pyrogram import raw, types

if TYPE_CHECKING:
    from collections.abc import Iterable

log = logging.getLogger(__name__)


class GetForumTopicsByID:
    async def get_forum_topics_by_id(
        self: pyrogram.Client, chat_id: int | str, topic_ids: int | Iterable[int]
    ) -> types.ForumTopic | list[types.ForumTopic]:
        """Get one or more topic from a chat by using topic identifiers.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            topic_ids (``int`` | Iterable of ``int``):
                Pass a single topic identifier or an iterable of topic ids (as integers) to get the information of the
                topic themselves.

        Returns:
            :obj:`~pyrogram.types.ForumTopic` | List of :obj:`~pyrogram.types.ForumTopic`: In case *topic_ids* was not
            a list, a single topic is returned, otherwise a list of topics is returned.

        Example:
            .. code-block:: python

                # Get one topic
                await app.get_forum_topics_by_id(chat_id, 12345)

                # Get more than one topic (list of topics)
                await app.get_forum_topics_by_id(chat_id, [12345, 12346])

        Raises:
            ValueError: In case of invalid arguments.
        """

        peer = await self.resolve_peer(chat_id)

        is_iterable = not isinstance(topic_ids, int)
        topic_ids = list(topic_ids) if is_iterable else [topic_ids]

        rpc = raw.functions.messages.GetForumTopicsByID(peer=peer, topics=topic_ids)

        r = await self.invoke(rpc, sleep_threshold=-1)

        if is_iterable:
            topic_list = [await types.ForumTopic._parse(topic) for topic in r.topics]
            topics = types.List(topic_list)
        else:
            topics = await types.ForumTopic._parse(r.topics[0])

        return topics
