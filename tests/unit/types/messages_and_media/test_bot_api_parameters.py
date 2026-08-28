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

"""The Bot-API-7 parameter objects.

These replace flat parameters that could not express the combinations Telegram now supports:
``reply_to_message_id`` could not carry a quote or a position, and ``disable_web_page_preview``
could only turn a preview off, never choose its URL or size.
"""

from __future__ import annotations

import pytest

from pyrogram import enums, raw, types


def web_page(url: str = "https://example.com/"):
    return raw.types.WebPage(id=1, url=url, display_url=url, hash=0)


def media(url: str = "https://example.com/", **kwargs):
    return raw.types.MessageMediaWebPage(webpage=web_page(url), **kwargs)


# --- ReplyParameters --------------------------------------------------------


def test_reply_parameters_is_keyword_only():
    """Positional construction is rejected: the fields are not meaningfully ordered."""
    with pytest.raises(TypeError):
        types.ReplyParameters(123)


def test_reply_parameters_defaults_are_all_none():
    params = types.ReplyParameters()
    assert params.message_id is None
    assert params.quote is None
    assert params.quote_entities is None


def test_reply_parameters_keeps_every_field():
    entities = [types.MessageEntity(type=enums.MessageEntityType.BOLD, offset=0, length=4)]
    params = types.ReplyParameters(
        message_id=1,
        story_id=2,
        chat_id="me",
        ephemeral_message_id=3,
        quote="bold",
        quote_parse_mode=enums.ParseMode.HTML,
        quote_entities=entities,
        quote_position=5,
        checklist_task_id=6,
        poll_option_id="opt",
    )
    assert (params.message_id, params.story_id, params.chat_id) == (1, 2, "me")
    assert (params.ephemeral_message_id, params.quote_position) == (3, 5)
    assert params.quote == "bold"
    assert params.quote_parse_mode is enums.ParseMode.HTML
    assert params.quote_entities == entities
    assert (params.checklist_task_id, params.poll_option_id) == (6, "opt")


def test_reply_parameters_is_serialisable_like_every_other_object():
    params = types.ReplyParameters(message_id=1, quote="q")
    text = str(params)
    assert '"message_id": 1' in text
    assert '"quote": "q"' in text
    assert "story_id" not in text, "unset fields must not appear"


# --- LinkPreviewOptions -----------------------------------------------------


def test_link_preview_options_is_keyword_only():
    with pytest.raises(TypeError):
        types.LinkPreviewOptions(True)


def test_parse_from_web_page_media_is_enabled():
    options = types.LinkPreviewOptions._parse(media())
    assert options.is_disabled is False
    assert options.url == "https://example.com/"


def test_parse_carries_the_size_preferences():
    options = types.LinkPreviewOptions._parse(media(force_small_media=True), invert_media=True)
    assert options.prefer_small_media is True
    assert options.show_above_text is True


def test_parse_of_a_not_modified_web_page_falls_through():
    """WebPageNotModified carries no URL, so it is not a preview we can describe."""
    not_modified = raw.types.MessageMediaWebPage(webpage=raw.types.WebPageNotModified())
    assert types.LinkPreviewOptions._parse(not_modified) is None


def test_parse_of_a_not_modified_web_page_with_a_url_is_disabled():
    not_modified = raw.types.MessageMediaWebPage(webpage=raw.types.WebPageNotModified())
    options = types.LinkPreviewOptions._parse(not_modified, url="https://example.com/")
    assert options.is_disabled is True
    assert options.url == "https://example.com/"


def test_parse_of_unrelated_media_without_a_url_is_none():
    assert types.LinkPreviewOptions._parse(raw.types.MessageMediaEmpty()) is None


def test_parse_of_unrelated_media_with_a_url_is_a_disabled_preview():
    options = types.LinkPreviewOptions._parse(
        raw.types.MessageMediaEmpty(), url="https://example.com/"
    )
    assert options.is_disabled is True


def test_link_preview_options_keeps_every_field():
    options = types.LinkPreviewOptions(
        is_disabled=False,
        url="https://example.com/",
        prefer_small_media=True,
        prefer_large_media=False,
        show_above_text=True,
    )
    assert options.is_disabled is False
    assert options.prefer_small_media is True
    assert options.prefer_large_media is False
    assert options.show_above_text is True
