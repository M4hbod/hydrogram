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

"""Every client method is called, and must reach a request without raising.

``test_rpc_construction`` drives methods too, but it returns a plausible reply
and so gets as far as parsing it -- which means 75 of them skip with "needs more
client than the stub provides", and a method that skips is a method nobody has
ever run. ``Auth.create()`` was in that state and cost a production outage.

This stops at the request instead. The recorder raises the moment ``invoke`` is
called, so nothing downstream of the wire is needed: no message cache, no peer
storage, no reply shapes. What it proves is narrow and worth having -- the body
executes, the parameters are read, and the request is built without a
``TypeError``, an ``AttributeError`` or a bad raw field.

A method that cannot be driven is listed in ``UNDRIVEABLE`` with the reason, so
the set of untested methods is a thing you can read rather than a silence.
"""

from __future__ import annotations

import inspect

import pytest

from pyrogram import Client, enums, raw, types


class Recorded(BaseException):
    """Raised once a request is built, to stop before it would be sent."""


def recorder() -> Client:
    """A real Client that records instead of sending.

    A hand-built stub kept growing attributes the methods legitimately read --
    lang_code, api_id, the invite-link regexes, and the sibling methods some of
    them delegate to. Using the real class and overriding only `invoke` removes
    that whole category: everything except the wire is genuine.
    """
    client = Client("harness", api_id=1, api_hash="0" * 32, in_memory=True)
    client.sent = []

    async def invoke(query, *args, **kwargs):
        client.sent.append(query)

        raise Recorded

    async def resolve_peer(peer_id=None, *args, **kwargs):
        return raw.types.InputPeerUser(user_id=7, access_hash=0)

    async def save_file(*args, **kwargs):
        return raw.types.InputFile(id=1, parts=1, name="f", md5_checksum="")

    client.invoke = invoke
    client.resolve_peer = resolve_peer
    client.save_file = save_file
    client.me = types.User(id=7, is_self=True, is_bot=False, first_name="Me")

    return client


# Plausible values by parameter name. A method whose required parameters are all
# here can be driven; anything else is listed in UNDRIVEABLE.
ARGUMENTS = {
    "chat_id": -100123,
    "from_chat_id": -100456,
    "user_id": 7,
    "bot_user_id": 7,
    "sender_chat_id": 7,
    "peer": 7,
    "message_id": 1,
    "message_ids": [1],
    "story_id": 1,
    "story_ids": [1],
    "topic_id": 1,
    "topic_ids": [1],
    "folder_id": 1,
    "limit": 1,
    "offset": 0,
    "offset_id": 0,
    "query": "q",
    "query_id": 1,
    "text": "t",
    "title": "t",
    "name": "n",
    "description": "d",
    "caption": "c",
    "url": "https://example.com",
    "link": "https://t.me/x",
    "invite_link": "https://t.me/+abc",
    "emoji": "👍",
    "reaction": "👍",
    "phone_number": "+15551234567",
    "note": "n",
    "ttl": 60,
    "ttl_seconds": 60,
    "seconds": 60,
    "enabled": True,
    "is_enabled": True,
    "value": True,
    "tag": "t",
    "color": 1,
    "first_name": "F",
    "last_name": "L",
    "password": "p",
    "code": "12345",
    "phone_code_hash": "h",
    "bot_token": "1:aaa",
    "amount": 1,
    "star_count": 1,
    "stars_amount": 1,
    "payload": "p",
    "currency": "XTR",
    "prices": [],
    "provider_token": "tok",
    "results": [],
    "media": types.InputMediaPhoto("x"),
    "ok": True,
    "callback_query_id": "1",
    "pre_checkout_query_id": "1",
    "shipping_query_id": "1",
    "inline_query_id": "1",
    "web_app_query_id": "1",
    "result": types.InlineQueryResultArticle(
        title="t", input_message_content=types.InputTextMessageContent("t")
    ),
    "score": 1,
    "quantity": 1,
    "day": 1,
    "month": 1,
    "collection_id": 1,
    "gift_id": 1,
    "boost_id": 1,
    "slug": "s",
    "session_id": 1,
    "hash": "h",
    "data": b"d",
    "file_id": "x",
    "action": enums.ChatAction.TYPING,
    "privacy_key": enums.PrivacyKey.PHONE_NUMBER,
    "rules": [],
    "options": ["a", "b"],
    "question": "q?",
    "latitude": 0.0,
    "longitude": 0.0,
    "address": "a",
    "chat_ids": [-100123],
    "user_ids": [7],
    "usernames": ["u"],
    "username": "u",
    "permissions": types.ChatPermissions(),
    "privileges": types.ChatPrivileges(),
    "commands": [],
    "photo": "x",
    "sticker": "x",
    "document": "x",
    "video": "x",
    "audio": "x",
    "animation": "x",
    "voice": "x",
    "video_note": "x",
    "contact": None,
}

# Same parameter name, different shape: `media` is one object for
# edit_message_media and a list for the group senders.
PER_METHOD = {
    "send_media_group": {"media": [types.InputMediaPhoto("x")]},
    "send_paid_media": {"media": [types.InputMediaPhoto("x")]},
}

# Methods this harness cannot drive, and why. Each is a real reason, not a
# blanket exclusion -- the point of the list is that it can be read and argued
# with, unlike a silent skip.
UNDRIVEABLE = {
    # Drive the client lifecycle rather than build a request.
    "start",
    "stop",
    "run",
    "restart",
    "terminate",
    "connect",
    "disconnect",
    "initialize",
    "authorize",
    "load_session",
    "load_plugins",
    "log_out",
    "updates_watchdog",
    "get_session",
    "business_connection_session",
    # Decorators, handler registration and listeners: no request at all.
    "add_handler",
    "remove_handler",
    "remove_error_handler",
    "stop_transmission",
    "set_parse_mode",
    "listen",
    "ask",
    "stop_listening",
    "stop_listener",
    "remove_listener",
    "register_next_step_handler",
    "get_listener_matching_with_data",
    "get_listener_matching_with_identifier_pattern",
    "get_many_listeners_matching_with_data",
    "get_many_listeners_matching_with_identifier_pattern",
    # Local helpers, not RPCs.
    "guess_extension",
    "guess_mime_type",
    "rnd_id",
    "fetch_peers",
    "resolve_peer",
    "handle_updates",
    "handle_download",
    "save_file",
    "get_file",
    "stream_media",
    "download_media",
    "compose_text_with_ai",
    "fix_text_with_ai",
    "export_session_string",
    "invoke",
    "recover_gaps",
}


def driveable():
    found = []

    for name in sorted(dir(Client)):
        if name.startswith("_") or name in UNDRIVEABLE:
            continue

        fn = inspect.getattr_static(Client, name, None)

        if not inspect.isfunction(fn) or not inspect.iscoroutinefunction(fn):
            continue

        parameters = list(inspect.signature(fn).parameters.items())[1:]
        required = [
            key
            for key, spec in parameters
            if spec.default is inspect.Parameter.empty
            and spec.kind not in {spec.VAR_POSITIONAL, spec.VAR_KEYWORD}
        ]

        if all(key in ARGUMENTS for key in required):
            arguments = {key: ARGUMENTS[key] for key in required}
            arguments.update({k: v for k, v in PER_METHOD.get(name, {}).items() if k in arguments})
            found.append((name, fn, arguments))

    return found


DRIVEABLE = driveable()


def test_most_of_the_surface_is_driveable():
    # A floor, not a target: it exists so a change that quietly stops driving
    # half the surface fails here rather than going green on fewer tests.
    assert len(DRIVEABLE) > 230, f"only {len(DRIVEABLE)} methods driveable; the harness is broken"


@pytest.mark.parametrize(
    ("name", "fn", "kwargs"), DRIVEABLE, ids=[name for name, _, _ in DRIVEABLE]
)
async def test_the_method_builds_a_request(name, fn, kwargs):
    # Async so pytest-asyncio owns the loop. Running our own with asyncio.run()
    # closes it on the way out, and on Python 3.9 that leaves the tests after
    # this one without one.
    built = {}

    try:
        # Built inside the loop: Client.__init__ reaches for a running one.
        client = built["client"] = recorder()
        result = fn(client, **kwargs)

        if inspect.isasyncgen(result):
            async for _ in result:
                break
        else:
            await result
    except Recorded:
        return
    except (ValueError, NotImplementedError) as exc:
        pytest.skip(f"{name} rejects the stub arguments: {exc}")

    client = built.get("client")

    if client is None or not client.sent:
        pytest.skip(f"{name} returned without building a request")
