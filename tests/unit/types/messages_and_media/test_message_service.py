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

"""Service-message parsing.

`Message._parse_service` grew from 18 handled `MessageAction` constructors to 67 in stage 4.2. An
unhandled action does not raise -- it produces a `Message` with `service` unset and the
corresponding attribute missing -- so the failure mode is a service message that silently looks
like nothing happened. These tests parse each action Telegram can send and assert something came
back.
"""

from __future__ import annotations

import inspect
import json

import pytest

from pyrogram import raw, types
from pyrogram.client import Cache


def buildable_actions():
    """MessageAction constructors that need no arguments, so they can be built generically."""
    out = []
    for name in sorted(dir(raw.types)):
        if not name.startswith("MessageAction"):
            continue
        cls = getattr(raw.types, name)
        if not inspect.isclass(cls):
            continue
        required = [
            p
            for k, p in inspect.signature(cls.__init__).parameters.items()
            if k != "self" and p.default is inspect.Parameter.empty
        ]
        if not required:
            out.append((name, cls))
    return out


ACTIONS = buildable_actions()


# The parser resolves peer_id against the users/chats maps that arrive with the update, so the
# sender has to be present -- an absent peer is a KeyError, not a None.
USERS = {7: raw.types.User(id=7, first_name="Test", access_hash=0)}


class FakeClient:
    """Enough Client for the parser: a message cache and the fetch switches.

    The fetch flags are off so parsing never reaches out to the network -- the point of these
    tests is the parsing, not the round trips it can trigger.
    """

    def __init__(self):
        self.message_cache = Cache(64)
        self.topic_cache = Cache(64)
        self.fetch_replies = False
        self.fetch_topics = False
        self.fetch_stories = False
        self.me = None


def service_message(action):
    return raw.types.MessageService(
        id=1,
        peer_id=raw.types.PeerUser(user_id=7),
        # Real service messages carry a sender; some actions (joins, for one) look it up.
        from_id=raw.types.PeerUser(user_id=7),
        date=1_700_000_000,
        action=action,
    )


def test_the_action_sweep_found_something():
    assert len(ACTIONS) >= 10, f"only {len(ACTIONS)} zero-argument actions found"


@pytest.mark.parametrize(("name", "cls"), ACTIONS, ids=[n for n, _ in ACTIONS])
async def test_every_zero_argument_action_parses(name, cls):
    parsed = await types.Message._parse(FakeClient(), service_message(cls()), USERS, {})

    assert parsed is not None, f"{name} produced no Message"
    assert parsed.id == 1
    assert parsed.date is not None and parsed.date.tzinfo is not None


async def test_a_pinned_message_is_recognised_as_a_service_message():
    parsed = await types.Message._parse(
        FakeClient(), service_message(raw.types.MessageActionPinMessage()), USERS, {}
    )
    assert parsed.service is not None, "pinned-message services must set `service`"


async def test_an_unknown_action_still_produces_a_message():
    """Forward compatibility: a layer newer than ours must not crash the parser."""

    class FutureAction(raw.types.MessageActionEmpty):
        pass

    parsed = await types.Message._parse(FakeClient(), service_message(FutureAction()), USERS, {})
    assert parsed is not None


async def test_a_plain_text_message_parses():
    message = raw.types.Message(
        id=2,
        peer_id=raw.types.PeerUser(user_id=7),
        date=1_700_000_000,
        message="hello",
    )
    parsed = await types.Message._parse(FakeClient(), message, USERS, {})
    assert parsed.text == "hello"
    assert parsed.service is None


async def test_message_str_does_not_leak_the_raw_object():
    message = raw.types.Message(
        id=3, peer_id=raw.types.PeerUser(user_id=7), date=1_700_000_000, message="x"
    )
    parsed = await types.Message._parse(FakeClient(), message, USERS, {})
    assert "raw" not in json.loads(str(parsed))


# --- ordinary messages ------------------------------------------------------


def plain_message(**kwargs):
    base = {
        "id": 10,
        "peer_id": raw.types.PeerUser(user_id=7),
        "from_id": raw.types.PeerUser(user_id=7),
        "date": 1_700_000_000,
        "message": "hello",
    }
    base.update(kwargs)
    return raw.types.Message(**base)


async def test_entities_are_parsed():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            message="bold text",
            entities=[raw.types.MessageEntityBold(offset=0, length=4)],
        ),
        USERS,
        {},
    )
    assert parsed.entities
    assert parsed.entities[0].offset == 0


async def test_a_message_without_entities_has_none():
    """`entities` is flags-gated, so it arrives absent rather than empty."""
    parsed = await types.Message._parse(FakeClient(), plain_message(), USERS, {})
    assert not parsed.entities


async def test_an_edited_message_carries_its_edit_date():
    parsed = await types.Message._parse(
        FakeClient(), plain_message(edit_date=1_700_000_500), USERS, {}
    )
    assert parsed.edit_date is not None
    assert parsed.edit_date.tzinfo is not None


async def test_outgoing_flag_survives():
    parsed = await types.Message._parse(FakeClient(), plain_message(out=True), USERS, {})
    assert parsed.outgoing is True


async def test_a_scheduled_message_is_flagged():
    parsed = await types.Message._parse(
        FakeClient(), plain_message(), USERS, {}, is_scheduled=True
    )
    assert parsed.scheduled is True


async def test_a_forwarded_message_records_its_origin():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            fwd_from=raw.types.MessageFwdHeader(
                date=1_699_000_000, from_id=raw.types.PeerUser(user_id=7)
            )
        ),
        USERS,
        {},
    )
    assert parsed.forward_origin is not None or parsed.forward_date is not None


async def test_a_media_message_sets_a_media_type():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            media=raw.types.MessageMediaContact(
                phone_number="+15551234567",
                first_name="A",
                last_name="B",
                vcard="",
                user_id=7,
            )
        ),
        USERS,
        {},
    )
    assert parsed.contact is not None
    assert parsed.media is not None


async def test_an_empty_media_is_tolerated():
    parsed = await types.Message._parse(
        FakeClient(), plain_message(media=raw.types.MessageMediaEmpty()), USERS, {}
    )
    assert parsed is not None


async def test_a_message_is_cached_after_parsing():
    """The parser writes into client.message_cache so replies can be resolved without a round trip."""
    client = FakeClient()
    parsed = await types.Message._parse(client, plain_message(), USERS, {})
    assert await client.message_cache.get((parsed.chat.id, parsed.id)) is not None


# --- media ------------------------------------------------------------------


@pytest.mark.parametrize(
    "media",
    [
        raw.types.MessageMediaEmpty(),
        raw.types.MessageMediaUnsupported(),
        raw.types.MessageMediaPhoto(),
        raw.types.MessageMediaDocument(),
    ],
    ids=["empty", "unsupported", "photo-without-file", "document-without-file"],
)
async def test_degenerate_media_does_not_crash_the_parser(media):
    """Telegram sends these when the media is expired, restricted, or newer than our layer."""
    parsed = await types.Message._parse(FakeClient(), plain_message(media=media), USERS, {})
    assert parsed is not None
    assert parsed.id == 10


async def test_a_venue_message_parses():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            media=raw.types.MessageMediaVenue(
                geo=raw.types.GeoPoint(long=1.0, lat=2.0, access_hash=0),
                title="Place",
                address="Street",
                provider="foursquare",
                venue_id="v1",
                venue_type="",
            )
        ),
        USERS,
        {},
    )
    assert parsed.venue is not None
    assert parsed.venue.title == "Place"


async def test_a_geo_message_parses():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            media=raw.types.MessageMediaGeo(
                geo=raw.types.GeoPoint(long=1.5, lat=2.5, access_hash=0)
            )
        ),
        USERS,
        {},
    )
    assert parsed.location is not None


async def test_a_dice_message_parses():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(media=raw.types.MessageMediaDice(value=4, emoticon="🎲")),
        USERS,
        {},
    )
    assert parsed.dice is not None
    assert parsed.dice.value == 4


async def test_a_webpage_message_keeps_link_preview_options():
    parsed = await types.Message._parse(
        FakeClient(),
        plain_message(
            message="see https://example.com",
            media=raw.types.MessageMediaWebPage(
                webpage=raw.types.WebPage(
                    id=1, url="https://example.com", display_url="example.com", hash=0
                )
            ),
        ),
        USERS,
        {},
    )
    assert parsed.link_preview_options is not None
    assert parsed.link_preview_options.url == "https://example.com"
