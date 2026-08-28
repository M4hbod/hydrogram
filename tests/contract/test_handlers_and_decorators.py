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

"""Every handler is reachable, and every decorator registers the right one.

A decorator that registers a handler the dispatcher never routes is silent: the bot starts, the
callback is never called, and nothing in the logs says why. These tests tie the three pieces
together -- the decorator on `Client`, the `Handler` subclass it registers, and the dispatcher's
routing table.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

import pyrogram
from pyrogram import handlers
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers.handler import Handler
from pyrogram.methods.utilities import add_handler as add_handler_module

HANDLERS = sorted(
    name for name in handlers.__all__ if name.endswith("Handler") and name != "Handler"
)

# on_x -> XHandler, by convention. Kept explicit so a rename has to be deliberate.
DECORATORS = {
    "on_message": "MessageHandler",
    "on_edited_message": "EditedMessageHandler",
    "on_deleted_messages": "DeletedMessagesHandler",
    "on_callback_query": "CallbackQueryHandler",
    "on_inline_query": "InlineQueryHandler",
    "on_chosen_inline_result": "ChosenInlineResultHandler",
    "on_chat_member_updated": "ChatMemberUpdatedHandler",
    "on_chat_join_request": "ChatJoinRequestHandler",
    "on_user_status": "UserStatusHandler",
    "on_poll": "PollHandler",
    "on_raw_update": "RawUpdateHandler",
    # added in stage 4.3
    "on_story": "StoryHandler",
    "on_message_reaction": "MessageReactionHandler",
    "on_message_reaction_count": "MessageReactionCountHandler",
    "on_chat_boost": "ChatBoostHandler",
    "on_business_message": "BusinessMessageHandler",
    "on_edited_business_message": "EditedBusinessMessageHandler",
    "on_deleted_business_messages": "DeletedBusinessMessagesHandler",
    "on_business_connection": "BusinessConnectionHandler",
    "on_pre_checkout_query": "PreCheckoutQueryHandler",
    "on_shipping_query": "ShippingQueryHandler",
    "on_purchased_paid_media": "PurchasedPaidMediaHandler",
    "on_guest_message": "GuestMessageHandler",
    "on_managed_bot": "ManagedBotUpdatedHandler",
}


def test_the_handler_set_is_the_expected_size():
    assert len(HANDLERS) >= 27, f"only {len(HANDLERS)} handlers exported"


@pytest.mark.parametrize("name", HANDLERS)
def test_every_handler_derives_from_the_base(name):
    assert issubclass(getattr(handlers, name), Handler)


@pytest.mark.parametrize("name", HANDLERS)
def test_every_handler_takes_a_callback_and_filters(name):
    params = inspect.signature(getattr(handlers, name).__init__).parameters
    assert "callback" in params, f"{name} has no callback parameter"


@pytest.mark.parametrize("decorator", sorted(DECORATORS))
def test_the_decorator_exists_on_the_client(decorator):
    assert callable(getattr(pyrogram.Client, decorator, None)), f"Client.{decorator} is missing"


@pytest.mark.parametrize(("decorator", "handler"), sorted(DECORATORS.items()))
def test_the_decorator_registers_its_handler(decorator, handler):
    """The decorator attaches (handler_instance, group) to the callback for later registration."""

    def callback(client, update):  # pragma: no cover - never invoked
        return None

    # Called with `self=None` the decorator takes its "not bound to a client yet" path and
    # stashes the handler on the function, which is how smart plugins are registered.
    getattr(pyrogram.Client, decorator)(None)(callback)

    assert hasattr(callback, "handlers"), f"{decorator} registered nothing"
    assert type(callback.handlers[0][0]).__name__ == handler


# Client lifecycle handlers: fired by the Client around connect/start/stop, not by an update
# arriving through the dispatcher, so they have no routing entry by design.
LIFECYCLE_HANDLERS = {"ConnectHandler", "DisconnectHandler", "StartHandler", "StopHandler"}


def test_the_dispatcher_routes_every_update_handler():
    """A handler with no route is a callback that never fires, and nothing says why."""
    source = inspect.getsource(Dispatcher)
    unrouted = [h for h in HANDLERS if h not in source and h not in LIFECYCLE_HANDLERS]
    assert not unrouted, f"handlers with no dispatcher route: {unrouted}"


# Where each lifecycle callback is actually invoked. add_handler() stores them on the Client as
# `<name>_handler`; something else has to call them, and it is not the dispatcher's routing table.
LIFECYCLE_FIRED_BY = {
    "StartHandler": ("start_handler", "pyrogram.dispatcher"),
    "StopHandler": ("stop_handler", "pyrogram.dispatcher"),
    "ConnectHandler": ("connect_handler", "pyrogram.session.session"),
    "DisconnectHandler": ("disconnect_handler", "pyrogram.session.session"),
}


@pytest.mark.parametrize("name", sorted(LIFECYCLE_HANDLERS))
def test_lifecycle_handlers_are_stored_by_add_handler(name):
    assert name in inspect.getsource(add_handler_module), f"add_handler ignores {name}"


@pytest.mark.parametrize(
    ("name", "attribute", "module"),
    [(n, a, m) for n, (a, m) in sorted(LIFECYCLE_FIRED_BY.items())],
)
def test_lifecycle_callbacks_are_actually_invoked(name, attribute, module):
    """Registered but never called is the failure this catches."""
    source = inspect.getsource(importlib.import_module(module))
    assert f"{attribute}(" in source, f"{attribute} is stored but never invoked in {module}"
