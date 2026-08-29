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

import base64
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from pyrogram import raw

if TYPE_CHECKING:
    from collections.abc import Iterable

InputPeer = Union[raw.types.InputPeerUser, raw.types.InputPeerChat, raw.types.InputPeerChannel]


@dataclass(frozen=True)
class UpdateState:
    """How far through the update sequence a chat was when we last saw it.

    Telegram numbers updates per chat rather than globally, so catching up after
    being offline means asking for the difference from a remembered counter.
    ``id`` is the chat, or ``0`` for the account-wide sequence. Every other
    field may be ``None``, meaning "unknown, leave whatever is stored alone".
    """

    id: int
    pts: int | None = None
    qts: int | None = None
    date: int | None = None
    seq: int | None = None


class BaseStorage(ABC):
    """The BaseStorage class is an abstract base class defining the interface
    for different storage engines used by Hyrogram.

    Parameters:
        name (``str``):
            The name of the session.
    """

    SESSION_STRING_FORMAT: str = ">BI?256sQ?"

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def open(self) -> None:
        """Opens the storage engine."""
        ...

    @abstractmethod
    async def save(self) -> None:
        """Saves the current state of the storage engine."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Closes the storage engine."""
        ...

    @abstractmethod
    async def delete(self) -> None:
        """Deletes the storage."""
        ...

    @abstractmethod
    async def update_peers(self, peers: list[tuple[int, int, str, str, str]]) -> None:
        """Update the peers table with the provided information.

        Parameters:
            peers (``List[Tuple[int, int, str, str, str]]``): A list of tuples containing the
                information of the peers to be updated. Each tuple must contain:
                - ``int``: The peer id.
                - ``int``: The peer access hash.
                - ``str``: The peer type (user, chat, or channel).
                - ``str``: The peer username (if any).
                - ``str``: The peer phone number (if any).
        """
        ...

    @abstractmethod
    async def get_peer_by_id(self, peer_id: int) -> InputPeer:
        """Retrieve a peer by its ID.

        Parameters:
            peer_id (``int``):
                The ID of the peer to retrieve.

        Returns:
            :obj:`~pyrogram.storage.base.InputPeer`: The retrieved peer.
        """
        ...

    @abstractmethod
    async def get_peer_by_username(self, username: str) -> InputPeer:
        """Retrieve a peer by its username.

        Parameters:
            username (``str``):
                The username of the peer to retrieve.

        Returns:
            :obj:`~pyrogram.storage.base.InputPeer`: The retrieved peer.
        """
        ...

    @abstractmethod
    async def get_peer_by_phone_number(self, phone_number: str) -> InputPeer:
        """Retrieve a peer by its phone number.

        Parameters:
            phone_number (``str``):
                The phone number of the peer to retrieve.

        Returns:
            :obj:`~pyrogram.storage.base.InputPeer`: The retrieved peer.
        """
        ...

    @abstractmethod
    async def get_update_states(self, ids: int | Iterable[int] | None = None) -> list[UpdateState]:
        """Return the stored update states, oldest first.

        Parameters:
            ids (``int`` | Iterable of ``int``, *optional*):
                Restrict the result to these chat ids. All of them when omitted.
        """
        ...

    @abstractmethod
    async def set_update_state(self, update_state: UpdateState | Iterable[UpdateState]) -> None:
        """Store one or more update states.

        A ``None`` field leaves the stored value alone rather than clearing it,
        because an update carries only the counters it advances.
        """
        ...

    @abstractmethod
    async def delete_update_state(self, state_id: int | Iterable[int]) -> None:
        """Forget the update state of one or more chats."""
        ...

    @abstractmethod
    async def dc_id(self, value: int | None = None) -> int:
        """Get or set the DC ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The DC ID to set.

        Returns:
            ``int``: The current DC ID if no value is provided.
        """
        ...

    @abstractmethod
    async def api_id(self, value: int | None = None) -> int:
        """Get or set the API ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The API ID to set.

        Returns:
            ``int``: The current API ID if no value is provided.
        """
        ...

    @abstractmethod
    async def test_mode(self, value: bool | None = None) -> bool:
        """Get or set the test mode of the current session.

        Parameters:
            value (``bool``, *optional*):
                The test mode to set.

        Returns:
            ``bool``: The current test mode if no value is provided.
        """
        ...

    @abstractmethod
    async def auth_key(self, value: bytes | None = None) -> bytes:
        """Get or set the authorization key of the current session.

        Parameters:
            value (``bytes``, *optional*):
                The authorization key to set.

        Returns:
            ``bytes``: The current authorization key if no value is provided.
        """
        ...

    @abstractmethod
    async def date(self, value: int | None = None) -> int:
        """Get or set the date of the current session.

        Parameters:
            value (``int``, *optional*):
                The date to set.

        Returns:
            ``int``: The current date if no value is provided.
        """
        ...

    @abstractmethod
    async def user_id(self, value: int | None = None) -> int:
        """Get or set the user ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The user ID to set.

        Returns:
            ``int``: The current user ID if no value is provided.
        """
        ...

    @abstractmethod
    async def is_bot(self, value: bool | None = None) -> bool:
        """Get or set the bot flag of the current session.

        Parameters:
            value (``bool``, *optional*):
                The bot flag to set.

        Returns:
            ``bool``: The current bot flag if no value is provided.
        """
        ...

    async def export_session_string(self) -> str:
        """Exports the session string for the current session.

        Returns:
            ``str``: The session string for the current session.
        """
        packed = struct.pack(
            self.SESSION_STRING_FORMAT,
            await self.dc_id(),
            await self.api_id(),
            await self.test_mode(),
            await self.auth_key(),
            await self.user_id(),
            await self.is_bot(),
        )
        return base64.urlsafe_b64encode(packed).decode().rstrip("=")
