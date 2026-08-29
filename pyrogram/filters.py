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

import inspect
import re
from re import Pattern
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

import pyrogram
from pyrogram import enums
from pyrogram.types import (
    CallbackQuery,
    ChatBoostUpdated,
    ChatJoinRequest,
    ChatMemberUpdated,
    ChosenInlineResult,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    ShippingQuery,
    Story,
    Update,
)


class Filter:
    commands: set[str]
    prefixes: set[str]
    case_sensitive: bool
    p: Pattern

    async def __call__(self, client: pyrogram.Client, update: Update) -> Awaitable[bool]:
        raise NotImplementedError

    def __invert__(self) -> InvertFilter:
        return InvertFilter(self)

    def __and__(self, other: Filter) -> AndFilter:
        return AndFilter(self, other)

    def __or__(self, other: Filter) -> OrFilter:
        return OrFilter(self, other)


class InvertFilter(Filter):
    def __init__(self, base: Filter) -> None:
        self.base = base

    async def __call__(self, client: pyrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        return not x


class AndFilter(Filter):
    def __init__(self, base: Filter, other: Filter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: pyrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        if not x:
            return False

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return bool(x) and bool(y)


class OrFilter(Filter):
    def __init__(self, base: Filter, other: Filter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: pyrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        if x:
            return True

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return bool(x) or bool(y)


def create(
    func: Callable[..., bool | Awaitable[bool]],
    name: str | None = None,
    **kwargs: Any,
) -> Filter:
    """Easily create a custom filter.

    Custom filters give you extra control over which updates are allowed or not to be processed
    by your handlers.

    Parameters:
        func (``Callable``):
            A function that accepts three positional arguments *(filter, client, update)* and
            returns a boolean: True if the update should be handled, False otherwise.
            The *filter* argument refers to the filter itself and can be used to access
            keyword arguments (read below). The *client* argument refers to the
            :obj:`~pyrogram.Client` that received the update. The *update* argument type
            will vary depending on which `Handler <handlers>`_ is coming from. For example, in
            a :obj:`~pyrogram.handlers.MessageHandler` the *update* argument will be a
            :obj:`~pyrogram.types.Message`; in a :obj:`~pyrogram.handlers.CallbackQueryHandler`
            the *update* will be a :obj:`~pyrogram.types.CallbackQuery`. Your function body
            can then access the incoming update attributes and decide whether to allow it or not.

        name (``str``, *optional*):
            Your filter's name. Can be anything you like.
            Defaults to "CustomFilter".

        **kwargs (``any``, *optional*):
            Any keyword argument you would like to pass. Useful when creating parameterized
            custom filters, such as :meth:`~pyrogram.filters.command` or
            :meth:`~pyrogram.filters.regex`.
    """
    return type(
        name or func.__name__ or "CustomFilter",
        (Filter,),
        {"__call__": func, **kwargs},
    )()


# Which update types actually carry which field. A callback query has a sender
# but no sender chat; a reaction-count update has a chat but no sender -- so a
# filter that reads a field off whatever it is handed raises AttributeError on
# the update types that do not have it, inside the handler worker where it is
# logged and swallowed. Naming the types instead makes the filter simply not
# match. Kept honest by `tests/contract/test_filter_update_shapes.py`.
_WITH_A_SENDER = (
    CallbackQuery,
    ChatJoinRequest,
    ChatMemberUpdated,
    ChosenInlineResult,
    InlineQuery,
    Message,
    PreCheckoutQuery,
    ShippingQuery,
    Story,
)

_WITH_A_CHAT = (
    ChatBoostUpdated,
    ChatJoinRequest,
    ChatMemberUpdated,
    Message,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    Story,
)

_WITH_A_SENDER_CHAT = (Message, Story)

_CAN_BE_OUTGOING = (Message, Story)

# `business_connection_id`, `quote` and `topic` live on `Message` alone, so the
# filters that read them cannot take the field off the update the way the ones
# above do. They go through the message the update is about instead, which for a
# callback query is the message the button sits under.
_WITH_A_MESSAGE = (CallbackQuery,)


def _sender_of(update: Update):
    return update.from_user if isinstance(update, _WITH_A_SENDER) else None


def _chat_of(update: Update):
    if isinstance(update, CallbackQuery):
        return update.message.chat if update.message else None

    return update.chat if isinstance(update, _WITH_A_CHAT) else None


def _sender_chat_of(update: Update):
    return update.sender_chat if isinstance(update, _WITH_A_SENDER_CHAT) else None


def _is_outgoing(update: Update) -> bool:
    return bool(update.outgoing) if isinstance(update, _CAN_BE_OUTGOING) else False


def _message_of(update: Update) -> Message | None:
    if isinstance(update, Message):
        return update

    return update.message if isinstance(update, _WITH_A_MESSAGE) else None


def _attribute_filter(attribute: str) -> Callable[[Filter, pyrogram.Client, Message], bool]:
    def func(_: Filter, __: pyrogram.Client, m: Message) -> bool:
        return bool(getattr(m, attribute, None))

    return func


def _chat_type_filter(chat_types: set[enums.ChatType], update: Update) -> bool:
    chat = _chat_of(update)

    return bool(chat and chat.type in chat_types)


def all_filter(_: Filter, __: pyrogram.Client, ___: Update) -> bool:
    return True


all = create(all_filter)
"""Filter all messages."""


def me_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    sender = _sender_of(update)

    return bool(sender.is_self if sender else _is_outgoing(update))


me = create(me_filter)
"""Filter messages generated by you yourself."""


def bot_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    sender = _sender_of(update)

    return bool(sender and sender.is_bot)


bot = create(bot_filter)
"""Filter messages coming from bots."""


def incoming_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return not _is_outgoing(update)


incoming = create(incoming_filter)
"""Filter incoming messages. Messages sent to your own chat (Saved Messages) are also
recognised as incoming.
"""


def outgoing_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return _is_outgoing(update)


outgoing = create(outgoing_filter)
"""Filter outgoing messages. Messages sent to your own chat (Saved Messages)
are not recognized as outgoing.
"""

text = create(_attribute_filter("text"), "text_filter")
"""Filter text messages."""

reply = create(_attribute_filter("reply_to_message_id"), "reply_filter")
"""Filter messages that are replies to other messages."""

forwarded = create(_attribute_filter("forward_date"), "forwarded_filter")
"""Filter messages that are forwarded."""

caption = create(_attribute_filter("caption"), "caption_filter")
"""Filter media messages that contain captions."""

audio = create(_attribute_filter("audio"), "audio_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Audio` objects."""

document = create(_attribute_filter("document"), "document_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Document` objects."""

photo = create(_attribute_filter("photo"), "photo_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Photo` objects."""

sticker = create(_attribute_filter("sticker"), "sticker_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Sticker` objects."""

animation = create(_attribute_filter("animation"), "animation_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Animation` objects."""

game = create(_attribute_filter("game"), "game_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Game` objects."""

video = create(_attribute_filter("video"), "video_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Video` objects."""

media_group = create(_attribute_filter("media_group_id"), "media_group_filter")
"""Filter messages containing photos or videos being part of an album."""

voice = create(_attribute_filter("voice"), "voice_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Voice` note objects."""

video_note = create(_attribute_filter("video_note"), "video_note_filter")
"""Filter messages that contain :obj:`~pyrogram.types.VideoNote` objects."""

contact = create(_attribute_filter("contact"), "contact_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Contact` objects."""

location = create(_attribute_filter("location"), "location_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Location` objects."""

venue = create(_attribute_filter("venue"), "venue_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Venue` objects."""

web_page = create(_attribute_filter("web_page"), "web_page_filter")
"""Filter messages sent with a webpage preview."""

poll = create(_attribute_filter("poll"), "poll_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Poll` objects."""

dice = create(_attribute_filter("dice"), "dice_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Dice` objects."""

media_spoiler = create(_attribute_filter("has_media_spoiler"), "media_spoiler_filter")
"""Filter media messages that contain a spoiler."""


def private_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return _chat_type_filter({enums.ChatType.PRIVATE, enums.ChatType.BOT}, update)


private = create(private_filter)
"""Filter messages sent in private chats."""


def group_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return _chat_type_filter({enums.ChatType.GROUP, enums.ChatType.SUPERGROUP}, update)


group = create(group_filter)
"""Filter messages sent in group or supergroup chats."""


def channel_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return _chat_type_filter({enums.ChatType.CHANNEL}, update)


channel = create(channel_filter)
"""Filter messages sent in channels."""

new_chat_members = create(_attribute_filter("new_chat_members"), "new_chat_members_filter")
"""Filter service messages for new chat members."""

left_chat_member = create(_attribute_filter("left_chat_member"), "left_chat_member_filter")
"""Filter service messages for members that left the chat."""

new_chat_title = create(_attribute_filter("new_chat_title"), "new_chat_title_filter")
"""Filter service messages for new chat titles."""

new_chat_photo = create(_attribute_filter("new_chat_photo"), "new_chat_photo_filter")
"""Filter service messages for new chat photos."""

delete_chat_photo = create(_attribute_filter("delete_chat_photo"), "delete_chat_photo_filter")
"""Filter service messages for deleted photos."""

group_chat_created = create(_attribute_filter("group_chat_created"), "group_chat_created_filter")
"""Filter service messages for group chat creations."""

supergroup_chat_created = create(
    _attribute_filter("supergroup_chat_created"), "supergroup_chat_created_filter"
)
"""Filter service messages for supergroup chat creations."""

channel_chat_created = create(
    _attribute_filter("channel_chat_created"), "channel_chat_created_filter"
)
"""Filter service messages for channel chat creations."""

migrate_to_chat_id = create(_attribute_filter("migrate_to_chat_id"), "migrate_to_chat_id_filter")
"""Filter service messages that contain migrate_to_chat_id."""

migrate_from_chat_id = create(
    _attribute_filter("migrate_from_chat_id"), "migrate_from_chat_id_filter"
)
"""Filter service messages that contain migrate_from_chat_id."""

pinned_message = create(_attribute_filter("pinned_message"), "pinned_message_filter")
"""Filter service messages for pinned messages."""

game_high_score = create(_attribute_filter("game_high_score"), "game_high_score_filter")
"""Filter service messages for game high scores."""


def reply_keyboard_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return isinstance(m.reply_markup, ReplyKeyboardMarkup)


reply_keyboard = create(reply_keyboard_filter)
"""Filter messages containing reply keyboard markups"""


def inline_keyboard_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return isinstance(m.reply_markup, InlineKeyboardMarkup)


inline_keyboard = create(inline_keyboard_filter)
"""Filter messages containing inline keyboard markups"""

mentioned = create(_attribute_filter("mentioned"), "mentioned_filter")
"""Filter messages containing mentions"""

via_bot = create(_attribute_filter("via_bot"), "via_bot_filter")
"""Filter messages sent via inline bots"""

video_chat_started = create(_attribute_filter("video_chat_started"), "video_chat_started_filter")
"""Filter messages for started video chats"""

video_chat_ended = create(_attribute_filter("video_chat_ended"), "video_chat_ended_filter")
"""Filter messages for ended video chats"""

video_chat_members_invited = create(
    _attribute_filter("video_chat_members_invited"), "video_chat_members_invited_filter"
)
"""Filter messages for voice chat invited members"""


def service_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return bool(m.service)


service = create(service_filter)
"""Filter service messages.

A service message contains any of the following fields set: *left_chat_member*,
*new_chat_title*, *new_chat_photo*, *delete_chat_photo*, *group_chat_created*,
*supergroup_chat_created*, *channel_chat_created*, *migrate_to_chat_id*,
*migrate_from_chat_id*, *pinned_message*, *game_score*, *video_chat_started*,
*video_chat_ended*, *video_chat_members_invited*.
"""


def media_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return bool(m.media)


media = create(media_filter)
"""Filter media messages.

A media message contains any of the following fields set: *audio*, *document*, *photo*,
*sticker*, *video*, *animation*, *voice*, *video_note*, *contact*, *location*, *venue*, *poll*.
"""

scheduled = create(_attribute_filter("scheduled"), "scheduled_filter")
"""Filter messages that have been scheduled (not yet sent)."""

from_scheduled = create(_attribute_filter("from_scheduled"), "from_scheduled_filter")
"""Filter new automatically sent messages that were previously scheduled."""


def linked_channel_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return bool(m.forward_from_chat and not m.from_user)


linked_channel = create(linked_channel_filter)
"""Filter messages that are automatically forwarded from the linked channel to the group chat."""


def admin_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    chat = _chat_of(update)

    return bool(chat and chat.is_admin)


admin = create(admin_filter)
"""Filter updates from chats where you have admin rights."""


def direct_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return _chat_type_filter({enums.ChatType.DIRECT}, update)


direct = create(direct_filter)
"""Filter updates sent in a direct messages chat."""


def forum_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    chat = _chat_of(update)

    return bool(chat and chat.is_forum)


forum = create(forum_filter)
"""Filter updates sent in forums."""


def sender_chat_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    return bool(_sender_chat_of(update))


sender_chat = create(sender_chat_filter)
"""Filter updates sent on behalf of a chat rather than a user."""


def business_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    message = _message_of(update)

    return bool(message and message.business_connection_id)


business = create(business_filter)
"""Filter updates that arrived through a business connection."""


def quote_filter(_: Filter, __: pyrogram.Client, update: Update) -> bool:
    message = _message_of(update)

    return bool(message and message.quote)


quote = create(quote_filter)
"""Filter messages that quote part of the message they reply to."""


chat_shared = create(_attribute_filter("chat_shared"), "chat_shared_filter")
"""Filter service messages for a shared chat."""

users_shared = create(_attribute_filter("users_shared"), "users_shared_filter")
"""Filter service messages for shared users."""

gift = create(_attribute_filter("gift"), "gift_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Gift` objects."""

gift_code = create(_attribute_filter("premium_gift_code"), "gift_code_filter")
"""Filter messages that contain :obj:`~pyrogram.types.PremiumGiftCode` objects."""

giveaway = create(_attribute_filter("giveaway"), "giveaway_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Giveaway` objects."""

giveaway_winners = create(_attribute_filter("giveaway_winners"), "giveaway_winners_filter")
"""Filter messages that contain :obj:`~pyrogram.types.GiveawayWinners` objects."""

story = create(_attribute_filter("story"), "story_filter")
"""Filter messages that contain :obj:`~pyrogram.types.Story` objects."""

successful_payment = create(_attribute_filter("successful_payment"), "successful_payment_filter")
"""Filter service messages for a successful payment."""

paid_message = create(_attribute_filter("send_paid_messages_stars"), "paid_message_filter")
"""Filter messages the sender paid Telegram Stars to send."""

ephemeral = create(_attribute_filter("ephemeral_message_id"), "ephemeral_filter")
"""Filter ephemeral messages."""


def live_location_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    return bool(m.location and m.location.live_period)


live_location = create(live_location_filter)
"""Filter messages that contain a :obj:`~pyrogram.types.Location` being shared live."""


def self_destruction_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    # The ttl is on the media rather than on the message, and only these four
    # kinds can carry one.
    return any(media and media.ttl_seconds for media in (m.photo, m.voice, m.video, m.video_note))


self_destruction = create(self_destruction_filter)
"""Filter media messages that destroy themselves after being viewed."""


def _gift_offer_in(state: enums.GiftPurchaseOfferState):
    def func(_: Filter, __: pyrogram.Client, m: Message) -> bool:
        offer = m.upgraded_gift_purchase_offer

        return bool(offer and offer.state == state)

    return func


gift_offer = create(_gift_offer_in(enums.GiftPurchaseOfferState.PENDING), "gift_offer_filter")
"""Filter messages carrying a gift purchase offer that is still pending."""

gift_offer_accepted = create(
    _gift_offer_in(enums.GiftPurchaseOfferState.ACCEPTED), "gift_offer_accepted_filter"
)
"""Filter messages carrying a gift purchase offer that was accepted."""


def gift_offer_rejected_filter(_: Filter, __: pyrogram.Client, m: Message) -> bool:
    # Two shapes mean the same thing: an offer whose state says rejected, and the
    # separate service message the rejection produces.
    offer = m.upgraded_gift_purchase_offer

    return bool(
        (offer and offer.state == enums.GiftPurchaseOfferState.REJECTED)
        or m.upgraded_gift_purchase_offer_rejected
    )


gift_offer_rejected = create(gift_offer_rejected_filter)
"""Filter messages carrying a gift purchase offer that was rejected."""


class topic(Filter, set):  # noqa: N801
    """Filter updates coming from one or more forum topics.

    Parameters:
        topics (``int`` | ``list``, *optional*):
            Pass one or more topic ids to filter updates from those topics.
            Defaults to None (no topics).
    """

    def __init__(self, topics: int | list[int] | None = None) -> None:
        topics = [] if topics is None else topics if isinstance(topics, list) else [topics]

        super().__init__(topics)

    async def __call__(self, _: pyrogram.Client, update: Update) -> bool:
        message = _message_of(update)

        return bool(message and message.topic and message.topic.id in self)


def command(
    commands: str | list[str],
    prefixes: str | list[str] = "/",
    case_sensitive: bool = False,
) -> Filter:
    """Filter commands, i.e.: text messages starting with "/" or any other custom prefix.

    Parameters:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *command*
            field of the :obj:`~pyrogram.types.Message`.

        prefixes (``str`` | ``list``, *optional*):
            A prefix or a list of prefixes as string the filter should look for.
            Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
            Pass None or "" (empty string) to allow commands with no prefix at all.

        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, command="Start" would trigger /Start but not /start.
    """
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    def func(flt: Filter, client: pyrogram.Client, message: Message) -> bool:
        username = client.me.username or ""  # type: ignore
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        for prefix in flt.prefixes:
            if not text.startswith(prefix):
                continue

            without_prefix = text[len(prefix) :]

            for cmd in flt.commands:
                if not re.match(
                    rf"^(?:{cmd}(?:@?{username})?)(?:\s|$)",
                    without_prefix,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                ):
                    continue

                without_command = re.sub(
                    rf"{cmd}(?:@?{username})?\s?",
                    "",
                    without_prefix,
                    count=1,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                )

                message.command = [cmd] + [
                    re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                    for m in command_re.finditer(without_command)
                ]

                return True

        return False

    commands_list = [commands] if isinstance(commands, str) else commands
    commands_set = {c if case_sensitive else c.lower() for c in commands_list}

    if prefixes is None:
        prefixes_list = []
    elif isinstance(prefixes, str):
        prefixes_list = [prefixes]
    else:
        prefixes_list = prefixes
    prefixes_set = set(prefixes_list) if prefixes_list else {""}

    return create(
        func,
        "CommandFilter",
        commands=commands_set,
        prefixes=prefixes_set,
        case_sensitive=case_sensitive,
    )


def regex(pattern: str | Pattern, flags: int = 0) -> Filter:
    """Filter updates that match a given regular expression pattern.

    Can be applied to handlers that receive one of the following updates:

    - :obj:`~pyrogram.types.Message`: The filter will match ``text`` or ``caption``.
    - :obj:`~pyrogram.types.CallbackQuery`: The filter will match ``data``.
    - :obj:`~pyrogram.types.InlineQuery`: The filter will match ``query``.

    When a pattern matches, all the
    `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_ are
    stored in the ``matches`` field of the update object itself.

    Parameters:
        pattern (``str`` | ``Pattern``):
            The regex pattern as string or as pre-compiled pattern.

        flags (``int``, *optional*):
            Regex flags.
    """

    def func(flt: Filter, __: pyrogram.Client, update: Update) -> bool:
        if isinstance(update, Message):
            value = update.text or update.caption
        elif isinstance(update, CallbackQuery):
            value = update.data
        elif isinstance(update, InlineQuery):
            value = update.query
        else:
            raise ValueError(f"Regex filter doesn't work with {type(update)}")

        if value:
            update.matches = list(flt.p.finditer(value)) or None

        return bool(update.matches)

    return create(
        func,
        "RegexFilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags),
    )


class user(Filter, set):  # noqa: N801
    """Filter messages coming from one or more users.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_
    to manipulate the users container.

    Parameters:
        users (``int`` | ``str`` | ``list``):
            Pass one or more user ids/usernames to filter users.
            For you yourself, "me" or "self" can be used as well.
            Defaults to None (no users).
    """

    def __init__(self, users: int | str | list[int | str] | None = None):
        users = [] if users is None else users if isinstance(users, list) else [users]

        super().__init__(
            "me" if u in {"me", "self"} else u.lower().strip("@") if isinstance(u, str) else u
            for u in users
        )

    async def __call__(self, _, message: Message):
        return message.from_user and (
            message.from_user.id in self
            or (message.from_user.username and message.from_user.username.lower() in self)
            or ("me" in self and message.from_user.is_self)
        )


class chat(Filter, set):  # noqa: N801
    """Filter messages coming from one or more chats.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_
    to manipulate the chats container.

    Parameters:
        chats (``int`` | ``str`` | ``list``):
            Pass one or more chat ids/usernames to filter chats.
            For your personal cloud (Saved Messages) you can simply use "me" or "self".
            Defaults to None (no chats).
    """

    def __init__(self, chats: int | str | list[int | str] | None = None):
        chats = [] if chats is None else chats if isinstance(chats, list) else [chats]

        super().__init__(
            "me" if c in {"me", "self"} else c.lower().strip("@") if isinstance(c, str) else c
            for c in chats
        )

    async def __call__(self, _, message: Message):
        return message.chat and (
            message.chat.id in self
            or (message.chat.username and message.chat.username.lower() in self)
            or (
                "me" in self
                and message.from_user
                and message.from_user.is_self
                and not message.outgoing
            )
        )
