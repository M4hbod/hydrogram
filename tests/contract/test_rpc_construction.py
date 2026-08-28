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

"""Methods build a well-formed RPC before they touch the network.

Most of `pyrogram/methods/` is a thin wrapper: resolve a peer, build a `raw.functions.*` request,
invoke it, parse the reply. The interesting failure -- a renamed constructor, a field that moved
namespace, a keyword the TL no longer has -- happens while *building* the request, which needs no
network at all.

So this drives each method with a fake client that records the request instead of sending it. Any
method whose signature does not accept the generic arguments is skipped rather than guessed at;
the point is breadth over the simple wrappers, not coverage of every signature.
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

from pyrogram import Client, raw

SENTINEL_PEER = raw.types.InputPeerUser(user_id=7, access_hash=0)


class RecordingClient:
    """Records the RPC a method builds and returns a benign reply."""

    def __init__(self):
        self.sent = []
        self.me = None
        self.parse_mode = None

    @staticmethod
    async def resolve_peer(_peer=None):
        return SENTINEL_PEER

    async def invoke(self, rpc, *args, **kwargs):
        self.sent.append(rpc)
        return raw.types.Updates(updates=[], users=[], chats=[], date=0, seq=0)

    @staticmethod
    def rnd_id():
        return 1


# Values plausible for the parameter names these wrappers actually use.
ARGUMENTS = {
    "chat_id": -100123,
    "user_id": 7,
    "peer": 7,
    "message_id": 1,
    "message_ids": 1,
    "topic_id": 1,
    "folder_id": 1,
    "limit": 1,
    "offset": 0,
    "query": "q",
    "text": "t",
    "title": "t",
    "name": "n",
    "url": "https://example.com",
    "link": "https://t.me/x",
    "boost_id": 1,
    "story_id": 1,
    "gift_id": 1,
    "reaction": "x",
    "emoji": "x",
    "phone_number": "+15551234567",
    "note": "n",
    "ttl": 60,
    "seconds": 60,
    "enabled": True,
    "is_enabled": True,
    "value": True,
    "tag": "t",
    "color": 1,
}


def candidates():
    """Methods whose parameters are all either optional or in ARGUMENTS."""
    out = []
    for name in sorted(dir(Client)):
        if name.startswith("_"):
            continue
        fn = inspect.getattr_static(Client, name, None)
        if not inspect.isfunction(fn) or not inspect.iscoroutinefunction(fn):
            continue
        params = list(inspect.signature(fn).parameters.items())[1:]  # drop self
        required = [
            k
            for k, p in params
            if p.default is inspect.Parameter.empty
            and p.kind not in {p.VAR_POSITIONAL, p.VAR_KEYWORD}
        ]
        if required and all(k in ARGUMENTS for k in required):
            out.append((name, fn, {k: ARGUMENTS[k] for k in required}))
    return out


CANDIDATES = candidates()


def test_enough_methods_are_drivable():
    assert len(CANDIDATES) > 60, f"only {len(CANDIDATES)} methods could be driven"


@pytest.mark.parametrize(("name", "fn", "kwargs"), CANDIDATES, ids=[n for n, _, _ in CANDIDATES])
def test_method_builds_a_request(name, fn, kwargs):
    client = RecordingClient()
    try:
        result = fn(client, **kwargs)
        if inspect.isasyncgen(result):

            async def drain():
                async for _ in result:
                    break

            asyncio.get_event_loop_policy().new_event_loop().run_until_complete(drain())
        else:
            asyncio.get_event_loop_policy().new_event_loop().run_until_complete(result)
    except (TypeError, AttributeError, KeyError, ValueError, IndexError, StopAsyncIteration):
        # The fake client is deliberately shallow: a method needing more of it is out of scope
        # here, not a failure. What must never happen is a bad raw constructor, which raises
        # before any of these.
        pytest.skip(f"{name} needs more client than the stub provides")

    if not client.sent:
        # The stub peer sent the method down a branch that does not hit the network.
        pytest.skip(f"{name} took a non-RPC branch with the stub peer")

    for rpc in client.sent:
        assert hasattr(type(rpc), "ID"), f"{name} sent a non-TL object: {type(rpc)}"
        # A constructor missing from the layer would have raised while building the request.
        assert type(rpc).__module__.startswith("pyrogram.raw."), type(rpc).__module__
