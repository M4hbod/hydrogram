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

import asyncio
import base64
import functools
import hashlib
import os
import re
import struct
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timezone
from getpass import getpass
from types import SimpleNamespace

import pyrogram
from pyrogram import enums, raw, types
from pyrogram.file_id import DOCUMENT_TYPES, PHOTO_TYPES, FileId, FileType

PyromodConfig = SimpleNamespace(
    timeout_handler=None,
    stopped_handler=None,
    throw_exceptions=True,
    unallowed_click_alert=True,
    unallowed_click_alert_text=("[pyromod] You're not expected to click this button."),
)


async def ainput(prompt: str = "", *, hide: bool = False):
    """Just like the built-in input, but async"""
    with ThreadPoolExecutor(1) as executor:
        func = functools.partial(getpass if hide else input, prompt)
        return await asyncio.get_running_loop().run_in_executor(executor, func)


def get_input_media_from_file_id(
    file_id: str, expected_file_type: FileType = None, ttl_seconds: int | None = None
) -> raw.types.InputMediaPhoto | raw.types.InputMediaDocument:
    try:
        decoded = FileId.decode(file_id)
    except Exception as e:
        raise ValueError(
            f'Failed to decode "{file_id}". The value does not represent an existing local file, '
            f"HTTP URL, or valid file id."
        ) from e

    file_type = decoded.file_type

    if expected_file_type is not None and file_type != expected_file_type:
        raise ValueError(
            f"Expected {expected_file_type.name}, got {file_type.name} file id instead"
        )

    if file_type in {FileType.THUMBNAIL, FileType.CHAT_PHOTO}:
        raise ValueError(f"This file id can only be used for download: {file_id}")

    if file_type in PHOTO_TYPES:
        return raw.types.InputMediaPhoto(
            id=raw.types.InputPhoto(
                id=decoded.media_id,
                access_hash=decoded.access_hash,
                file_reference=decoded.file_reference,
            ),
            ttl_seconds=ttl_seconds,
        )

    if file_type in DOCUMENT_TYPES:
        return raw.types.InputMediaDocument(
            id=raw.types.InputDocument(
                id=decoded.media_id,
                access_hash=decoded.access_hash,
                file_reference=decoded.file_reference,
            ),
            ttl_seconds=ttl_seconds,
        )

    raise ValueError(f"Unknown file id: {file_id}")


async def parse_messages(
    client, messages: raw.types.messages.Messages, replies: int = 1
) -> list[types.Message]:
    users = {i.id: i for i in messages.users}
    chats = {i.id: i for i in messages.chats}
    topics = {i.id: i for i in messages.topics} if hasattr(messages, "topics") else None
    if not messages.messages:
        return types.List()

    parsed_messages = []

    parsed_messages = [
        await types.Message._parse(
            client=client, message=message, users=users, chats=chats, topics=topics, replies=0
        )
        for message in messages.messages
    ]

    if (
        messages_with_replies := {
            i.id: i.reply_to.reply_to_msg_id
            for i in messages.messages
            if not isinstance(i, raw.types.MessageEmpty) and i.reply_to
        }
    ) and replies:
        # We need a chat id, but some messages might be empty (no chat attribute available)
        # Scan until we find a message with a chat available (there must be one, because we are fetching replies)
        chat_id = next((m.chat.id for m in parsed_messages if m.chat), 0)
        reply_messages = await client.get_messages(
            chat_id,
            reply_to_message_ids=messages_with_replies.keys(),
            replies=replies - 1,
        )

        for message in parsed_messages:
            reply_id = messages_with_replies.get(message.id)

            for reply in reply_messages:
                if reply.id == reply_id and not reply.forum_topic_created:
                    message.reply_to_message = reply

    return types.List(parsed_messages)


def parse_deleted_messages(client, update) -> list[types.Message]:
    messages = update.messages
    channel_id = getattr(update, "channel_id", None)

    parsed_messages = [
        types.Message(
            id=message,
            chat=types.Chat(
                id=get_channel_id(channel_id),
                type=enums.ChatType.CHANNEL,
                client=client,
            )
            if channel_id is not None
            else None,
            client=client,
        )
        for message in messages
    ]
    return types.List(parsed_messages)


def pack_inline_message_id(msg_id: raw.base.InputBotInlineMessageID):
    if isinstance(msg_id, raw.types.InputBotInlineMessageID):
        inline_message_id_packed = struct.pack("<iqq", msg_id.dc_id, msg_id.id, msg_id.access_hash)
    else:
        inline_message_id_packed = struct.pack(
            "<iqiq", msg_id.dc_id, msg_id.owner_id, msg_id.id, msg_id.access_hash
        )

    return base64.urlsafe_b64encode(inline_message_id_packed).decode().rstrip("=")


def unpack_inline_message_id(inline_message_id: str) -> raw.base.InputBotInlineMessageID:
    padded = inline_message_id + "=" * (-len(inline_message_id) % 4)
    decoded = base64.urlsafe_b64decode(padded)

    if len(decoded) == 20:
        unpacked = struct.unpack("<iqq", decoded)

        return raw.types.InputBotInlineMessageID(
            dc_id=unpacked[0], id=unpacked[1], access_hash=unpacked[2]
        )

    unpacked = struct.unpack("<iqiq", decoded)

    return raw.types.InputBotInlineMessageID64(
        dc_id=unpacked[0],
        owner_id=unpacked[1],
        id=unpacked[2],
        access_hash=unpacked[3],
    )


MIN_CHANNEL_ID_OLD = -1002147483647
MIN_CHANNEL_ID = -1007852516352
MAX_CHANNEL_ID = -1000000000000
MIN_CHAT_ID_OLD = -2147483647
MIN_CHAT_ID = -999999999999
MAX_USER_ID_OLD = 2147483647
MAX_USER_ID = 999999999999


def get_raw_peer_id(peer: raw.base.Peer) -> int | None:
    """Get the raw peer id from a Peer object"""
    if isinstance(peer, raw.types.PeerUser):
        return peer.user_id

    if isinstance(peer, raw.types.PeerChat):
        return peer.chat_id

    return peer.channel_id if isinstance(peer, raw.types.PeerChannel) else None


def get_peer_id(peer: raw.base.Peer) -> int:
    """Get the non-raw peer id from a Peer object"""
    if isinstance(peer, raw.types.PeerUser):
        return peer.user_id

    if isinstance(peer, raw.types.PeerChat):
        return -peer.chat_id

    if isinstance(peer, raw.types.PeerChannel):
        return MAX_CHANNEL_ID - peer.channel_id

    raise ValueError(f"Peer type invalid: {peer}")


def get_peer_type(peer_id: int) -> str:
    if peer_id < 0:
        if peer_id >= MIN_CHAT_ID:
            return "chat"

        if MIN_CHANNEL_ID <= peer_id < MAX_CHANNEL_ID:
            return "channel"
    elif 0 < peer_id <= MAX_USER_ID:
        return "user"

    raise ValueError(f"Peer id invalid: {peer_id}")


def get_channel_id(peer_id: int) -> int:
    return MAX_CHANNEL_ID - peer_id


def btoi(b: bytes) -> int:
    return int.from_bytes(b, "big")


def itob(i: int) -> bytes:
    return i.to_bytes(256, "big")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(i ^ j for i, j in zip(a, b))


def compute_password_hash(
    algo: raw.types.PasswordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow,
    password: str,
) -> bytes:
    hash1 = sha256(algo.salt1 + password.encode() + algo.salt1)
    hash2 = sha256(algo.salt2 + hash1 + algo.salt2)
    hash3 = hashlib.pbkdf2_hmac("sha512", hash2, algo.salt1, 100000)

    return sha256(algo.salt2 + hash3 + algo.salt2)


# ruff: noqa: N806
def compute_password_check(
    r: raw.types.account.Password, password: str
) -> raw.types.InputCheckPasswordSRP:
    algo = r.current_algo

    p_bytes = algo.p
    p = btoi(algo.p)

    g_bytes = itob(algo.g)
    g = algo.g

    B_bytes = r.srp_B
    B = btoi(B_bytes)

    srp_id = r.srp_id

    x_bytes = compute_password_hash(algo, password)
    x = btoi(x_bytes)

    g_x = pow(g, x, p)

    k_bytes = sha256(p_bytes + g_bytes)
    k = btoi(k_bytes)

    kg_x = (k * g_x) % p

    while True:
        a_bytes = os.urandom(256)
        a = btoi(a_bytes)

        A = pow(g, a, p)
        A_bytes = itob(A)

        u = btoi(sha256(A_bytes + B_bytes))

        if u > 0:
            break

    g_b = (B - kg_x) % p

    ux = u * x
    a_ux = a + ux
    S = pow(g_b, a_ux, p)
    S_bytes = itob(S)

    K_bytes = sha256(S_bytes)

    M1_bytes = sha256(
        xor(sha256(p_bytes), sha256(g_bytes))
        + sha256(algo.salt1)
        + sha256(algo.salt2)
        + A_bytes
        + B_bytes
        + K_bytes
    )

    return raw.types.InputCheckPasswordSRP(srp_id=srp_id, A=A_bytes, M1=M1_bytes)


async def parse_text_entities(
    client: pyrogram.Client,
    text: str,
    parse_mode: enums.ParseMode,
    entities: list[types.MessageEntity],
) -> dict[str, str | list[raw.base.MessageEntity]]:
    if entities:
        # Inject the client instance because parsing user mentions requires it
        for entity in entities:
            entity._client = client

        text, entities = text, [await entity.write() for entity in entities] or None  # noqa: PLW0127
    else:
        text, entities = (await client.parser.parse(text, parse_mode)).values()

    return {"message": text, "entities": entities}


def parse_text_with_entities(
    client: pyrogram.Client,
    message: raw.types.TextWithEntities | None,
    users: dict[int, raw.base.User],
) -> dict[str, str | list[types.MessageEntity] | None]:
    """Parse an incoming ``TextWithEntities`` into text plus high-level entities.

    The inverse of :func:`parse_text_entities`, despite the similar name: that one turns outgoing
    text into raw entities to send, this one turns a received raw object into something a caller
    can read. ``users`` is needed because a mention entity resolves to a :obj:`~pyrogram.types.User`.

    Entities that fail to parse are dropped rather than propagated as ``None``, so callers never
    have to filter the list themselves.
    """
    entities = types.List(
        filter(
            None,
            [
                types.MessageEntity._parse(client, entity, users)
                for entity in getattr(message, "entities", [])
            ],
        )
    )

    # Deferred deliberately: Str lives in message.py, which imports utils at module scope, so
    # a top-level import here closes the cycle and breaks `import pyrogram`.
    from pyrogram.types.messages_and_media.message import Str  # noqa: PLC0415

    return {
        "text": Str(getattr(message, "text", "")).init(entities) or None,
        "entities": entities or None,
    }


URL_RE = re.compile(
    r"(https?):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
)
_LEADING_TAG_RE = re.compile(r"^\s*(<[\w<>=\s\"]*>)\s*")
_TRAILING_TAG_RE = re.compile(r"\s*(</[\w</>]*>)\s*$")


def get_first_url(text: str) -> str | None:
    """First http(s) URL in ``text``, or None.

    Used to name the previewed link when Telegram sends a web page without echoing back which URL
    it came from. Surrounding HTML tags are trimmed first so a link wrapped in markup still
    matches.
    """
    text = _LEADING_TAG_RE.sub(r"\1", text)
    text = _TRAILING_TAG_RE.sub(r"\1", text)

    match = URL_RE.search(text)
    return f"{match.group(1)}://{match.group(2)}{match.group(3)}" if match else None


def zero_datetime() -> datetime:
    """The Unix epoch, timezone-aware in UTC.

    Used as the "unset" default for date parameters such as ``until_date``.
    """
    return datetime.fromtimestamp(0, timezone.utc)


def timestamp_to_datetime(ts: int | None) -> datetime | None:
    """Convert a Telegram timestamp to a timezone-aware UTC datetime.

    Telegram sends every date as a Unix timestamp, which is an instant, not a wall-clock reading.
    Returning an aware datetime keeps it that way: the result can be compared with
    :func:`zero_datetime`, subtracted from another aware datetime, and rendered in any timezone the
    caller likes via :meth:`~datetime.datetime.astimezone`.

    Passing ``tz`` also avoids the platform's ``localtime()``, which is not merely a tidiness point:
    ``datetime.fromtimestamp(1)`` returns ``1969-12-31T19:00:01`` west of UTC and raises
    ``OSError: [Errno 22]`` on Windows, because the local reading falls before the epoch.

    ``0`` means "never" in the Telegram API and is returned as ``None`` rather than the epoch.
    """
    return datetime.fromtimestamp(ts, timezone.utc) if ts else None


def datetime_to_timestamp(dt: datetime | None) -> int | None:
    """Convert a datetime to a Telegram timestamp.

    An aware datetime converts exactly. A **naive** one is interpreted as local time, which is what
    :meth:`datetime.datetime.timestamp` does and what ``datetime.now()`` -- the naive datetime
    users actually construct -- means. Interpreting naive input as UTC instead would silently shift
    every such call by the caller's UTC offset, which is a worse failure than being explicit.
    """
    return int(dt.timestamp()) if dt else None


async def get_reply_to(
    client: pyrogram.Client,
    reply_parameters: types.ReplyParameters | None = None,
    message_thread_id: int | None = None,
) -> raw.base.InputReplyTo | None:
    """Build the ``InputReplyTo`` for a send call.

    Layer 229 has four reply targets and :obj:`~pyrogram.types.ReplyParameters` maps onto them
    field for field, so this is a dispatcher rather than a translation. ``None`` means "not a
    reply", which is what every send method passes when the user did not ask for one.

    ``message_thread_id`` alone still produces a reply header: replying to the topic's root
    message is how Telegram scopes a message to a forum topic.
    """
    if reply_parameters is not None:
        if reply_parameters.story_id is not None:
            if reply_parameters.chat_id is None:
                raise ValueError("ReplyParameters.chat_id is required when replying to a story")
            return raw.types.InputReplyToStory(
                peer=await client.resolve_peer(reply_parameters.chat_id),
                story_id=reply_parameters.story_id,
            )

        if reply_parameters.message_id is not None:
            quote_text = None
            quote_entities = None
            if reply_parameters.quote is not None:
                quote_text, quote_entities = (
                    await parse_text_entities(
                        client,
                        reply_parameters.quote,
                        reply_parameters.quote_parse_mode,
                        reply_parameters.quote_entities,
                    )
                ).values()

            return raw.types.InputReplyToMessage(
                reply_to_msg_id=reply_parameters.message_id,
                top_msg_id=message_thread_id,
                # Resolved only when set: resolve_peer(None) goes straight to
                # storage.get_peer_by_id(None) and raises.
                reply_to_peer_id=(
                    await client.resolve_peer(reply_parameters.chat_id)
                    if reply_parameters.chat_id is not None
                    else None
                ),
                quote_text=quote_text,
                quote_entities=quote_entities,
                quote_offset=reply_parameters.quote_position,
                todo_item_id=reply_parameters.checklist_task_id,
                poll_option=(
                    reply_parameters.poll_option_id.encode()
                    if reply_parameters.poll_option_id is not None
                    else None
                ),
            )

        if reply_parameters.ephemeral_message_id is not None:
            return raw.types.InputReplyToEphemeralMessage(id=reply_parameters.ephemeral_message_id)

    if message_thread_id:
        return raw.types.InputReplyToMessage(
            reply_to_msg_id=message_thread_id, top_msg_id=message_thread_id
        )

    return None
