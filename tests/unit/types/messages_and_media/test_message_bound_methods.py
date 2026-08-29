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

"""The bound methods on ``Message``: what they delegate to, and with what."""

from __future__ import annotations

import inspect

import pytest

from pyrogram import enums, types
from pyrogram.types.messages_and_media.message import Str

ALIASES = [
    ("answer", "reply_text"),
    ("answer_animation", "reply_animation"),
    ("answer_audio", "reply_audio"),
    ("answer_cached_media", "reply_cached_media"),
    ("answer_checklist", "reply_checklist"),
    ("answer_contact", "reply_contact"),
    ("answer_dice", "reply_dice"),
    ("answer_document", "reply_document"),
    ("answer_game", "reply_game"),
    ("answer_inline_bot_result", "reply_inline_bot_result"),
    ("answer_invoice", "reply_invoice"),
    ("answer_location", "reply_location"),
    ("answer_media_group", "reply_media_group"),
    ("answer_paid_media", "reply_paid_media"),
    ("answer_photo", "reply_photo"),
    ("answer_poll", "reply_poll"),
    ("answer_rich", "reply_rich"),
    ("answer_sticker", "reply_sticker"),
    ("answer_venue", "reply_venue"),
    ("answer_video", "reply_video"),
    ("answer_video_note", "reply_video_note"),
    ("answer_voice", "reply_voice"),
]


@pytest.mark.parametrize(("alias", "target"), ALIASES)
def test_an_answer_alias_is_the_same_object_as_its_reply(alias, target):
    # Not a wrapper: a second implementation would drift from the first, and
    # the two names are meant to be the same method under two spellings.
    assert getattr(types.Message, alias) is getattr(types.Message, target)


NEW_MEMBERS = [
    "reply_dice",
    "reply_invoice",
    "reply_paid_media",
    "reply_checklist",
    "reply_rich",
    "edit_checklist",
    "edit_live_location",
    "stop_live_location",
    "copy_media_group",
    "read",
    "view",
    "summarize",
    "pay",
    "accept_gift_purchase_offer",
    "reject_gift_purchase_offer",
]


@pytest.mark.parametrize("name", NEW_MEMBERS)
def test_the_new_bound_methods_are_coroutines(name):
    assert inspect.iscoroutinefunction(getattr(types.Message, name))


@pytest.mark.parametrize("name", ["content", "html_text", "md_text"])
def test_the_text_properties_are_properties(name):
    assert isinstance(inspect.getattr_static(types.Message, name), property)


def test_content_prefers_text_then_caption_and_never_returns_none():
    # It feeds html_text and md_text, so None here becomes an AttributeError
    # two calls away from the cause.
    assert types.Message(id=1, text="hello").content == "hello"
    assert types.Message(id=1, caption="a caption").content == "a caption"
    # An empty Str, not None: html_text and md_text read attributes off it.
    assert types.Message(id=1).content == Str("")


def test_html_and_markdown_render_the_entities_on_the_content():
    # The parser hands text back as a Str carrying its own entities; that is
    # what html_text and md_text unparse.
    entities = [types.MessageEntity(type=enums.MessageEntityType.BOLD, offset=0, length=4)]
    message = types.Message(id=1, text=Str("bold").init(entities), entities=entities)

    assert message.html_text == "<b>bold</b>"
    assert message.md_text == "**bold**"


def test_the_text_properties_do_not_raise_on_a_message_with_no_text():
    # content falls back to an empty Str precisely so these two stay callable.
    message = types.Message(id=1)

    # The point is that they return rather than raise; empty is the right answer.
    assert not message.html_text
    assert not message.md_text


def test_no_deprecated_forwarding_shim_was_ported():
    # forward_from and friends are Kurigram properties that log a warning and
    # read forward_origin. Breaking changes are not shimmed here.
    for name in (
        "forward_from",
        "forward_from_chat",
        "forward_from_message_id",
        "forward_sender_name",
        "forward_signature",
        "forward_date",
    ):
        assert not hasattr(types.Message, name), f"{name} is a deprecated shim"

    assert "forward_origin" in inspect.signature(types.Message.__init__).parameters
