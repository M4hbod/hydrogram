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

import logging
from typing import TYPE_CHECKING

from pyrogram import raw, utils
from pyrogram.errors import (
    ChannelInvalid,
    ChannelPrivate,
    PersistentTimestampInvalid,
    PersistentTimestampOutdated,
)
from pyrogram.storage import UpdateState

if TYPE_CHECKING:
    from collections.abc import Iterable

    import pyrogram

log = logging.getLogger(__name__)


class RecoverGaps:
    async def recover_gaps(
        self: pyrogram.Client, ids: int | Iterable[int] | None = None
    ) -> tuple[int, int]:
        """Fetch the updates that arrived while the client was offline.

        Telegram numbers updates per chat, and the client stores how far it got
        in each. This asks the server for everything past those counters and
        feeds it through the normal handler pipeline, so a handler cannot tell a
        recovered update from a live one.

        Nothing is recovered for a chat with no stored state -- there is no
        counter to ask from -- so a brand new session recovers nothing, and
        ``skip_updates=True`` is the setting that deliberately keeps it that way.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            ids (``int`` | Iterable of ``int``, *optional*):
                Identifiers of the chats to recover, ``0`` for the account-wide
                sequence. Every chat with a stored state when omitted.

        Returns:
            ``tuple``: The number of recovered messages, and of other updates.

        Example:
            .. code-block:: python

                messages, updates = await app.recover_gaps()
        """
        recovered_messages = 0
        recovered_updates = 0

        states = await self.storage.get_update_states(ids)

        if not states:
            log.info("No stored update state, nothing to recover")
            return recovered_messages, recovered_updates

        log.info("Recovering gaps in %s chats", len(states))

        for state in states:
            chat_id = state.id
            pts, qts, date, seq = state.pts, state.qts, state.date, state.seq
            forgotten = False

            while True:
                requested_pts = pts

                try:
                    diff = await self.invoke(
                        raw.functions.updates.GetChannelDifference(
                            channel=await self.resolve_peer(chat_id),
                            filter=raw.types.ChannelMessagesFilterEmpty(),
                            pts=requested_pts,
                            limit=10000,
                            force=False,
                        )
                        if chat_id < utils.MAX_CHANNEL_ID
                        else raw.functions.updates.GetDifference(
                            pts=requested_pts, date=date, qts=0
                        )
                    )
                except (ChannelPrivate, ChannelInvalid):
                    # The account cannot see this chat any more, so its stored
                    # counter is dead weight that would be retried every start.
                    await self.storage.delete_update_state(chat_id)
                    forgotten = True
                    break
                except (PersistentTimestampOutdated, PersistentTimestampInvalid):
                    continue

                no_progress = False

                # Every branch that ends the loop only moves the local
                # counters; the single write after the loop is what persists
                # them. Writing here as well would be overwritten by that one.
                if isinstance(diff, raw.types.updates.DifferenceEmpty):
                    date, seq = diff.date, diff.seq
                    break

                if isinstance(diff, raw.types.updates.ChannelDifferenceEmpty):
                    pts = diff.pts
                    break

                if isinstance(diff, raw.types.updates.DifferenceTooLong):
                    # Too much happened to enumerate. Jump the counter forward
                    # and ask again from there.
                    pts = diff.pts
                    await self.storage.set_update_state(UpdateState(chat_id, pts, qts, date, seq))
                    continue

                if isinstance(diff, raw.types.updates.ChannelDifferenceTooLong):
                    pts = diff.dialog.pts
                    await self.storage.set_update_state(UpdateState(chat_id, pts, qts, date, seq))
                    continue

                if isinstance(diff, raw.types.updates.Difference):
                    pts, date, seq = diff.state.pts, diff.state.date, diff.state.seq
                elif isinstance(diff, raw.types.updates.DifferenceSlice):
                    pts = diff.intermediate_state.pts
                    date = diff.intermediate_state.date
                    seq = diff.intermediate_state.seq
                    # A slice that did not move the counter would be asked for
                    # again forever.
                    no_progress = pts == requested_pts
                elif isinstance(diff, raw.types.updates.ChannelDifference):
                    pts = diff.pts

                users = {user.id: user for user in diff.users}
                chats = {chat.id: chat for chat in diff.chats}

                for message in diff.new_messages:
                    self.dispatcher.updates_queue.put_nowait((
                        # pts_count is -1 because these messages arrive as a
                        # batch: there is no per-message count to report.
                        raw.types.UpdateNewMessage(message=message, pts=pts, pts_count=-1),
                        users,
                        chats,
                    ))
                    recovered_messages += 1

                for update in diff.other_updates:
                    self.dispatcher.updates_queue.put_nowait((update, users, chats))
                    recovered_updates += 1

                if isinstance(diff, raw.types.updates.Difference):
                    break

                if isinstance(diff, raw.types.updates.ChannelDifference) and diff.final:
                    break

                if no_progress:
                    break

            if not forgotten:
                await self.storage.set_update_state(UpdateState(chat_id, pts, qts, date, seq))

        await self.storage.save()

        log.info("Recovered %s messages and %s updates", recovered_messages, recovered_updates)

        return recovered_messages, recovered_updates
