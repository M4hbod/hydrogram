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

import html
from typing import TYPE_CHECKING

import pyrogram
from pyrogram import enums, filters, raw, types, utils
from pyrogram.types.object import Object
from pyrogram.types.pyromod import ListenerTypes
from pyrogram.types.update import Update

if TYPE_CHECKING:
    from datetime import datetime


class Link(str):
    __slots__ = ("style", "text", "url")

    HTML = "<a href={url}>{text}</a>"
    MARKDOWN = "[{text}]({url})"

    def __init__(self, url: str, text: str, style: enums.ParseMode):
        super().__init__()

        self.url = url
        self.text = text
        self.style = style

    @staticmethod
    def format(url: str, text: str, style: enums.ParseMode):
        fmt = Link.MARKDOWN if style == enums.ParseMode.MARKDOWN else Link.HTML

        return fmt.format(url=url, text=html.escape(text))

    def __new__(cls, url, text, style):
        return str.__new__(cls, Link.format(url, text, style))

    def __call__(self, other: str | None = None, *, style: str | None = None):
        return Link.format(self.url, other or self.text, style or self.style)

    def __str__(self):
        return Link.format(self.url, self.text, self.style)


class User(Object, Update):
    """A Telegram user or bot.

    Parameters:
        id (``int``):
            Unique identifier for this user or bot.

        is_self(``bool``, *optional*):
            True, if this user is you yourself.

        is_contact(``bool``, *optional*):
            True, if this user is in your contacts.

        is_mutual_contact(``bool``, *optional*):
            True, if you both have each other's contact.

        is_deleted(``bool``, *optional*):
            True, if this user is deleted.

        is_bot (``bool``, *optional*):
            True, if this user is a bot.

        is_verified (``bool``, *optional*):
            True, if this user has been verified by Telegram.

        is_restricted (``bool``, *optional*):
            True, if this user has been restricted. Bots only.
            See *restriction_reason* for details.

        is_scam (``bool``, *optional*):
            True, if this user has been flagged for scam.

        is_fake (``bool``, *optional*):
            True, if this user has been flagged for impersonation.

        is_support (``bool``, *optional*):
            True, if this user is part of the Telegram support team.

        is_premium (``bool``, *optional*):
            True, if this user is a premium user.

        first_name (``str``, *optional*):
            User's or bot's first name.

        last_name (``str``, *optional*):
            User's or bot's last name.

        full_name (``str``, *property*):
            Full name of the other party in a private chat.

        status (:obj:`~pyrogram.enums.UserStatus`, *optional*):
            User's last seen & online status. ``None``, for bots.

        last_online_date (:py:obj:`~datetime.datetime`, *optional*):
            Last online date of a user. Only available in case status is :obj:`~pyrogram.enums.UserStatus.OFFLINE`.

        next_offline_date (:py:obj:`~datetime.datetime`, *optional*):
            Date when a user will automatically go offline. Only available in case status is :obj:`~pyrogram.enums.UserStatus.ONLINE`.

        username (``str``, *optional*):
            User's or bot's username.

        active_usernames (List of ``str``, *optional*):
            If non-empty, the list of all active chat usernames; for private chats, supergroups and channels.

        usernames (List of :obj:`~pyrogram.types.Username`, *optional*):
            The list of user's collectible (and basic) usernames if availables.

        language_code (``str``, *optional*):
            IETF language tag of the user's language.

        emoji_status (:obj:`~pyrogram.types.EmojiStatus`, *optional*):
            Emoji status.

        dc_id (``int``, *optional*):
            User's or bot's assigned DC (data center). Available only in case the user has set a public profile photo.
            Note that this information is approximate; it is based on where Telegram stores a user profile pictures and
            does not by any means tell you the user location (i.e. a user might travel far away, but will still connect
            to its assigned DC). More info at `FAQs </faq#what-are-the-ip-addresses-of-telegram-data-centers>`_.

        phone_number (``str``, *optional*):
            User's phone number.

        photo (:obj:`~pyrogram.types.ChatPhoto`, *optional*):
            User's or bot's current profile photo. Suitable for downloads only.

        restrictions (List of :obj:`~pyrogram.types.Restriction`, *optional*):
            The list of reasons why this bot might be unavailable to some users.
            This field is available only in case *is_restricted* is True.

        mention (``str``, *property*):
            Generate a text mention for this user.
            You can use ``user.mention()`` to mention the user using their first name (styled using html), or
            ``user.mention("another name")`` for a custom name. To choose a different style
            ("HTML" or "MARKDOWN") use ``user.mention(style=ParseMode.MARKDOWN)``.
    """

    def __init__(
        self,
        *,
        client: pyrogram.Client | None = None,
        id: int,
        is_self: bool | None = None,
        is_contact: bool | None = None,
        is_mutual_contact: bool | None = None,
        is_deleted: bool | None = None,
        is_bot: bool | None = None,
        is_restricted: bool | None = None,
        is_support: bool | None = None,
        is_premium: bool | None = None,
        is_contact_require_premium: bool | None = None,
        is_close_friend: bool | None = None,
        is_stories_hidden: bool | None = None,
        is_stories_unavailable: bool | None = None,
        is_min: bool | None = None,
        verification_status: types.VerificationStatus | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        status: enums.UserStatus | None = None,
        last_online_date: datetime | None = None,
        next_offline_date: datetime | None = None,
        username: str | None = None,
        usernames: list[types.Username] | None = None,
        language_code: str | None = None,
        emoji_status: types.EmojiStatus | None = None,
        dc_id: int | None = None,
        phone_number: str | None = None,
        personal_photo: types.ChatPhoto | None = None,
        photo: types.ChatPhoto | None = None,
        public_photo: types.ChatPhoto | None = None,
        restrictions: list[types.Restriction] | None = None,
        accent_color_id: int | None = None,
        background_custom_emoji_id: str | None = None,
        profile_accent_color_id: int | None = None,
        profile_background_custom_emoji_id: str | None = None,
        added_to_attachment_menu: bool | None = None,
        active_users_count: int | None = None,
        inline_need_location: bool | None = None,
        inline_query_placeholder: str | None = None,
        can_be_edited: bool | None = None,
        can_be_added_to_attachment_menu: bool | None = None,
        can_join_groups: bool | None = None,
        can_read_all_group_messages: bool | None = None,
        can_connect_to_business: bool | None = None,
        can_manage_bots: bool | None = None,
        has_main_web_app: bool | None = None,
        has_topics: bool | None = None,
        allows_users_to_create_topics: bool | None = None,
        paid_message_star_count: int | None = None,
        settings: types.ChatSettings | None = None,
        common_chats: int | None = None,
        is_blocked: bool | None = None,
        is_phone_calls_available: bool | None = None,
        is_phone_calls_private: bool | None = None,
        is_video_calls_available: bool | None = None,
        is_wallpaper_overridden: bool | None = None,
        is_translations_disabled: bool | None = None,
        is_pinned_stories_available: bool | None = None,
        is_blocked_my_stories_from: bool | None = None,
        is_read_dates_available: bool | None = None,
        is_ads_enabled: bool | None = None,
        can_pin_message: bool | None = None,
        can_schedule_messages: bool | None = None,
        can_send_voice_messages: bool | None = None,
        can_view_revenue: bool | None = None,
        bot_can_manage_emoji_status: bool | None = None,
        display_gifts_button: bool | None = None,
        uses_unofficial_app: bool | None = None,
        bio: str | None = None,
        pinned_message: types.Message | None = None,
        folder_id: int | None = None,
        message_auto_delete_time: int | None = None,
        theme: str | None = None,
        private_forward_name: str | None = None,
        chat_admin_rights: types.ChatAdministratorRights | None = None,
        channel_admin_rights: types.ChatAdministratorRights | None = None,
        chat_background: types.ChatBackground | None = None,
        stories: list[types.Story] | None = None,
        business_away_message: types.BusinessMessage | None = None,
        business_greeting_message: types.BusinessMessage | None = None,
        business_work_hours: types.BusinessMessage | None = None,
        business_location: types.Location | None = None,
        business_intro: types.BusinessIntro | None = None,
        birthday: types.Birthday | None = None,
        personal_channel: types.Chat | None = None,
        personal_channel_message: types.Message | None = None,
        gift_count: int | None = None,
        bot_verification: types.BotVerification | None = None,
        main_profile_tab: enums.ProfileTab | None = None,
        first_profile_audio: types.Audio | None = None,
        rating: types.UserRating | None = None,
        pending_rating: types.UserRating | None = None,
        pending_rating_date: datetime | None = None,
        accepted_gift_types: types.AcceptedGiftTypes | None = None,
        note: types.FormattedText | None = None,
        supports_guest_queries: bool | None = None,
        supports_join_request_queries: bool | None = None,
        community_id: int | None = None,
        community: types.Community | None = None,
        raw: raw.base.User | raw.base.UserStatus | None = None,
        active_usernames: list[str] | None = None,
        is_fake: bool | None = None,
        is_scam: bool | None = None,
        is_verified: bool | None = None,
    ):
        super().__init__(client)

        self.id = id
        self.is_self = is_self
        self.is_contact = is_contact
        self.is_mutual_contact = is_mutual_contact
        self.is_deleted = is_deleted
        self.is_bot = is_bot
        self.is_restricted = is_restricted
        self.is_support = is_support
        self.is_premium = is_premium
        self.is_contact_require_premium = is_contact_require_premium
        self.is_close_friend = is_close_friend
        self.is_stories_hidden = is_stories_hidden
        self.is_stories_unavailable = is_stories_unavailable
        self.verification_status = verification_status
        self.is_min = is_min
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.last_online_date = last_online_date
        self.next_offline_date = next_offline_date
        self.username = username
        self.usernames = usernames
        self.language_code = language_code
        self.emoji_status = emoji_status
        self.dc_id = dc_id
        self.phone_number = phone_number
        self.personal_photo = personal_photo
        self.photo = photo
        self.public_photo = public_photo
        self.restrictions = restrictions
        self.accent_color_id = accent_color_id
        self.background_custom_emoji_id = background_custom_emoji_id
        self.profile_accent_color_id = profile_accent_color_id
        self.profile_background_custom_emoji_id = profile_background_custom_emoji_id
        self.added_to_attachment_menu = added_to_attachment_menu
        self.active_users_count = active_users_count
        self.inline_need_location = inline_need_location
        self.inline_query_placeholder = inline_query_placeholder
        self.can_be_edited = can_be_edited
        self.can_be_added_to_attachment_menu = can_be_added_to_attachment_menu
        self.can_join_groups = can_join_groups
        self.can_read_all_group_messages = can_read_all_group_messages
        self.can_connect_to_business = can_connect_to_business
        self.can_manage_bots = can_manage_bots
        self.has_main_web_app = has_main_web_app
        self.has_topics = has_topics
        self.allows_users_to_create_topics = allows_users_to_create_topics
        self.paid_message_star_count = paid_message_star_count
        self.settings = settings
        self.common_chats = common_chats
        self.is_blocked = is_blocked
        self.is_phone_calls_available = is_phone_calls_available
        self.is_phone_calls_private = is_phone_calls_private
        self.is_video_calls_available = is_video_calls_available
        self.is_wallpaper_overridden = is_wallpaper_overridden
        self.is_translations_disabled = is_translations_disabled
        self.is_pinned_stories_available = is_pinned_stories_available
        self.is_blocked_my_stories_from = is_blocked_my_stories_from
        self.is_read_dates_available = is_read_dates_available
        self.is_ads_enabled = is_ads_enabled
        self.can_pin_message = can_pin_message
        self.can_schedule_messages = can_schedule_messages
        self.can_send_voice_messages = can_send_voice_messages
        self.can_view_revenue = can_view_revenue
        self.bot_can_manage_emoji_status = bot_can_manage_emoji_status
        self.display_gifts_button = display_gifts_button
        self.uses_unofficial_app = uses_unofficial_app
        self.bio = bio
        self.pinned_message = pinned_message
        self.folder_id = folder_id
        self.message_auto_delete_time = message_auto_delete_time
        self.theme = theme
        self.private_forward_name = private_forward_name
        self.chat_admin_rights = chat_admin_rights
        self.channel_admin_rights = channel_admin_rights
        self.chat_background = chat_background
        self.stories = stories
        self.business_away_message = business_away_message
        self.business_greeting_message = business_greeting_message
        self.business_work_hours = business_work_hours
        self.business_location = business_location
        self.business_intro = business_intro
        self.birthday = birthday
        self.personal_channel = personal_channel
        self.personal_channel_message = personal_channel_message
        self.gift_count = gift_count
        self.bot_verification = bot_verification
        self.main_profile_tab = main_profile_tab
        self.first_profile_audio = first_profile_audio
        self.rating = rating
        self.pending_rating = pending_rating
        self.pending_rating_date = pending_rating_date
        self.accepted_gift_types = accepted_gift_types
        self.note = note
        self.supports_guest_queries = supports_guest_queries
        self.supports_join_request_queries = supports_join_request_queries
        self.community_id = community_id
        self.community = community
        self.raw = raw
        self.active_usernames = active_usernames
        self.is_fake = is_fake
        self.is_scam = is_scam
        self.is_verified = is_verified

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name])) or None

    @property
    def mention(self):
        return Link(
            f"tg://user?id={self.id}",
            self.first_name or "Deleted Account",
            self._client.parse_mode,
        )

    @staticmethod
    def _parse(client, user: raw.base.User) -> User | None:
        if not isinstance(user, raw.types.User):
            return None

        accent_color_id = None
        background_custom_emoji_id = None
        profile_accent_color_id = None
        profile_background_custom_emoji_id = None

        if isinstance(user.color, raw.types.PeerColor):
            accent_color_id = user.color.color
            background_custom_emoji_id = str(user.color.background_emoji_id)

        elif isinstance(user.color, raw.types.PeerColorCollectible):
            accent_color_id = user.color.accent_color
            background_custom_emoji_id = str(user.color.background_emoji_id)

        if isinstance(user.profile_color, raw.types.PeerColor):
            profile_accent_color_id = user.profile_color.color
            profile_background_custom_emoji_id = str(user.profile_color.background_emoji_id)

        elif isinstance(user.profile_color, raw.types.PeerColorCollectible):
            profile_accent_color_id = user.profile_color.accent_color
            profile_background_custom_emoji_id = str(user.profile_color.background_emoji_id)

        return User(
            id=user.id,
            is_self=user.is_self,
            is_contact=user.contact,
            is_mutual_contact=user.mutual_contact,
            is_deleted=user.deleted,
            is_bot=user.bot,
            is_restricted=user.restricted,
            is_support=user.support,
            is_premium=user.premium,
            is_contact_require_premium=user.contact_require_premium,
            is_close_friend=user.close_friend,
            is_stories_hidden=user.stories_hidden,
            is_stories_unavailable=user.stories_unavailable,
            is_min=user.min,
            verification_status=types.VerificationStatus._parse(user),
            first_name=user.first_name,
            last_name=user.last_name,
            **User._parse_status(user.status, user.bot),
            username=user.username or (user.usernames[0].username if user.usernames else None),
            usernames=types.List([types.Username._parse(r) for r in user.usernames or []]) or None,
            language_code=user.lang_code,
            emoji_status=types.EmojiStatus._parse(client, user.emoji_status),
            dc_id=getattr(user.photo, "dc_id", None),
            phone_number=user.phone,
            photo=types.ChatPhoto._parse(client, user.photo, user.id, user.access_hash),
            restrictions=types.List([
                types.Restriction._parse(r) for r in user.restriction_reason or []
            ])
            or None,
            accent_color_id=accent_color_id,
            background_custom_emoji_id=background_custom_emoji_id,
            profile_accent_color_id=profile_accent_color_id,
            profile_background_custom_emoji_id=profile_background_custom_emoji_id,
            added_to_attachment_menu=user.attach_menu_enabled,
            active_users_count=user.bot_active_users,
            inline_need_location=user.bot_inline_geo,
            inline_query_placeholder=user.bot_inline_placeholder,
            can_be_edited=user.bot_can_edit,
            can_be_added_to_attachment_menu=user.bot_attach_menu,
            can_join_groups=user.bot_nochats,
            can_read_all_group_messages=user.bot_chat_history,
            can_connect_to_business=user.bot_business,
            can_manage_bots=user.bot_can_manage_bots,
            has_main_web_app=user.bot_has_main_app,
            has_topics=user.bot_forum_view,
            allows_users_to_create_topics=user.bot_forum_can_manage_topics,
            paid_message_star_count=user.send_paid_messages_stars,
            supports_guest_queries=user.bot_guestchat,
            supports_join_request_queries=user.bot_guard,
            community_id=user.linked_community_id,
            raw=user,
            client=client,
        )

    @staticmethod
    def _parse_status(user_status: raw.base.UserStatus, is_bot: bool = False):
        if isinstance(user_status, raw.types.UserStatusOnline):
            status, date = enums.UserStatus.ONLINE, user_status.expires
        elif isinstance(user_status, raw.types.UserStatusOffline):
            status, date = enums.UserStatus.OFFLINE, user_status.was_online
        elif isinstance(user_status, raw.types.UserStatusRecently):
            status, date = enums.UserStatus.RECENTLY, None
        elif isinstance(user_status, raw.types.UserStatusLastWeek):
            status, date = enums.UserStatus.LAST_WEEK, None
        elif isinstance(user_status, raw.types.UserStatusLastMonth):
            status, date = enums.UserStatus.LAST_MONTH, None
        else:
            status, date = enums.UserStatus.LONG_AGO, None

        last_online_date = None
        next_offline_date = None

        if is_bot:
            status = None

        if status == enums.UserStatus.ONLINE:
            next_offline_date = utils.timestamp_to_datetime(date)

        if status == enums.UserStatus.OFFLINE:
            last_online_date = utils.timestamp_to_datetime(date)

        return {
            "status": status,
            "last_online_date": last_online_date,
            "next_offline_date": next_offline_date,
        }

    @staticmethod
    def _parse_user_status(client, user_status: raw.types.UpdateUserStatus):
        return User(
            id=user_status.user_id,
            **User._parse_status(user_status.status),
            raw=user_status,
            client=client,
        )

    def listen(
        self,
        filters: filters.Filter | None = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: int | None = None,
        unallowed_click_alert: bool = True,
        chat_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
    ):
        """
        Bound method *listen* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.listen(user_id=user.id)

        Example:
            .. code-block:: python

                user.listen()

        Parameters:
            filters (``Optional[pyrogram.Filter]``):
                Same as :meth:`pyrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`pyrogram.Client.listen`.

            timeout (``Optional[int]``):
                Same as :meth:`pyrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`pyrogram.Client.listen`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`pyrogram.Client.listen`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`pyrogram.Client.listen`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`pyrogram.Client.listen`.

        Returns:
            ``Union[Message, CallbackQuery]``: The Message or CallbackQuery that fulfilled the listener.
        """
        return self._client.listen(
            user_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    def ask(
        self,
        text: str,
        filters: filters.Filter | None = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: int | None = None,
        unallowed_click_alert: bool = True,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
        *args,
        **kwargs,
    ):
        """
        Bound method *ask* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.ask(user_id=user.id)

        Example:
            .. code-block:: python

                user.ask("Hello!")

        Parameters:
            text (``str``):
                Same as :meth:`pyrogram.Client.ask`.

            filters (``Optional[pyrogram.Filter]``):
                Same as :meth:`pyrogram.Client.ask`.

            listener_type (``ListenerTypes``):
                Same as :meth:`pyrogram.Client.ask`.

            timeout (``Optional[int]``):
                Same as :meth:`pyrogram.Client.ask`.

            unallowed_click_alert (``bool``):
                Same as :meth:`pyrogram.Client.ask`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`pyrogram.Client.ask`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`pyrogram.Client.ask`.

            args (``Any``):
                Same as :meth:`pyrogram.Client.ask`.

            kwargs (``Any``):
                Same as :meth:`pyrogram.Client.ask`.

        Returns:
            ``Union[Message, CallbackQuery]``: The Message or CallbackQuery that fulfilled the listener.
        """
        return self._client.ask(
            *args,
            chat_id=self.id,
            text=text,
            user_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            message_id=message_id,
            inline_message_id=inline_message_id,
            **kwargs,
        )

    def stop_listening(
        self,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        chat_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
    ):
        """
        Stops listening for messages from the user. Calls Client.stop_listening() with the user_id set to the user's id.

        Parameters:
            listener_type (``ListenerTypes``):
                Same as :meth:`pyrogram.Client.stop_listening`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`pyrogram.Client.stop_listening`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`pyrogram.Client.stop_listening`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`pyrogram.Client.stop_listening`.

        Returns:
            ``None``
        """
        return self._client.stop_listening(
            user_id=self.id,
            listener_type=listener_type,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    async def archive(self):
        """Bound method *archive* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.archive_chats(123456789)

        Example:
            .. code-block:: python

               await user.archive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.archive_chats(self.id)

    async def unarchive(self):
        """Bound method *unarchive* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unarchive_chats(123456789)

        Example:
            .. code-block:: python

                await user.unarchive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unarchive_chats(self.id)

    def block(self):
        """Bound method *block* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.block_user(123456789)

        Example:
            .. code-block:: python

                await user.block()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.block_user(self.id)

    def unblock(self):
        """Bound method *unblock* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.unblock_user(123456789)

        Example:
            .. code-block:: python

                user.unblock()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.unblock_user(self.id)

    def get_common_chats(self):
        """Bound method *get_common_chats* of :obj:`~pyrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.get_common_chats(123456789)

        Example:
            .. code-block:: python

                user.get_common_chats()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.get_common_chats(self.id)
