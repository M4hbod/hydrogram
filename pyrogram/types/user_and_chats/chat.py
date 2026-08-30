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

from typing import TYPE_CHECKING, BinaryIO

import pyrogram
from pyrogram import enums, filters, raw, types, utils
from pyrogram.types import ListenerTypes
from pyrogram.types.object import Object

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from datetime import datetime


class Chat(Object):
    """A chat.

    Parameters:
        id (``int``):
            Unique identifier for this chat.

        type (:obj:`~pyrogram.enums.ChatType`):
            Type of chat.

        is_verified (``bool``, *optional*):
            True, if this chat has been verified by Telegram. Supergroups, channels and bots only.

        is_participants_hidden (``bool``, *optional*):
            True, if this chat members has been hidden.

        is_restricted (``bool``, *optional*):
            True, if this chat has been restricted. Supergroups, channels and bots only.
            See *restriction_reason* for details.

        is_creator (``bool``, *optional*):
            True, if this chat owner is the current user. Supergroups, channels and groups only.

        is_scam (``bool``, *optional*):
            True, if this chat has been flagged for scam.

        is_fake (``bool``, *optional*):
            True, if this chat has been flagged for impersonation.

        is_support (``bool``):
            True, if this chat is part of the Telegram support team. Users and bots only.

        is_forum (``bool``, *optional*):
            True, if the supergroup chat is a forum

        is_admin (``bool``, *optional*):
            True, if you have administrator rights in this chat.

        title (``str``, *optional*):
            Title, for supergroups, channels and basic group chats.

        username (``str``, *optional*):
            Username, for private chats, bots, supergroups and channels if available.

        active_usernames (List of ``str``, *optional*):
            If non-empty, the list of all active chat usernames; for private chats, supergroups and channels.

        usernames (List of :obj:`~pyrogram.types.Username`, *optional*):
            The list of chat's collectible (and basic) usernames if availables.

        first_name (``str``, *optional*):
            First name of the other party in a private chat, for private chats and bots.

        last_name (``str``, *optional*):
            Last name of the other party in a private chat, for private chats.

        full_name (``str``, *property*):
            Full name of the other party in a private chat, for private chats and bots.

        photo (:obj:`~pyrogram.types.ChatPhoto`, *optional*):
            Chat photo. Suitable for downloads only.

        bio (``str``, *optional*):
            Bio of the other party in a private chat.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        description (``str``, *optional*):
            Description, for groups, supergroups and channel chats.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        dc_id (``int``, *optional*):
            The chat assigned DC (data center). Available only in case the chat has a photo.
            Note that this information is approximate; it is based on where Telegram stores the current chat photo.
            It is accurate only in case the owner has set the chat photo, otherwise the dc_id will be the one assigned
            to the administrator who set the current chat photo.

        has_protected_content (``bool``, *optional*):
            True, if messages from the chat can't be forwarded to other chats.

        invite_link (``str``, *optional*):
            Chat invite link, for groups, supergroups and channels.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        pinned_message (:obj:`~pyrogram.types.Message`, *optional*):
            Pinned message, for groups, supergroups channels and own chat.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        background (:obj:`~pyrogram.types.ChatBackground`, *optional*):
            A chat background.

        sticker_set_name (``str``, *optional*):
            For supergroups, name of group sticker set.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        can_set_sticker_set (``bool``, *optional*):
            True, if the group sticker set can be changed by you.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        members_count (``int``, *optional*):
            Chat members count, for groups, supergroups and channels only.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        restrictions (List of :obj:`~pyrogram.types.Restriction`, *optional*):
            The list of reasons why this chat might be unavailable to some users.
            This field is available only in case *is_restricted* is True.

        permissions (:obj:`~pyrogram.types.ChatPermissions` *optional*):
            Default chat member permissions, for groups and supergroups.

        distance (``int``, *optional*):
            Distance in meters of this group chat from your location.
            Returned only in :meth:`~pyrogram.Client.get_nearby_chats`.

        linked_chat (:obj:`~pyrogram.types.Chat`, *optional*):
            The linked discussion group (in case of channels) or the linked channel (in case of supergroups).
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        send_as_chat (:obj:`~pyrogram.types.Chat`, *optional*):
            The default "send_as" chat.
            Returned only in :meth:`~pyrogram.Client.get_chat`.

        available_reactions (:obj:`~pyrogram.types.ChatReactions`, *optional*):
            Available reactions in the chat.
            Returned only in :meth:`~pyrogram.Client.get_chat`.
    """

    def __init__(
        self,
        *,
        client: pyrogram.Client | None = None,
        id: int | None = None,
        type: enums.ChatType | None = None,
        is_forum: bool | None = None,
        is_direct_messages: bool | None = None,
        is_min: bool | None = None,
        is_members_hidden: bool | None = None,
        is_restricted: bool | None = None,
        is_creator: bool | None = None,
        is_admin: bool | None = None,
        is_deactivated: bool | None = None,
        is_support: bool | None = None,
        is_stories_hidden: bool | None = None,
        is_stories_unavailable: bool | None = None,
        is_business_bot: bool | None = None,
        is_preview: bool | None = None,
        is_banned: bool | None = None,
        is_call_active: bool | None = None,
        is_call_not_empty: bool | None = None,
        is_public: bool | None = None,
        is_paid_reactions_available: bool | None = None,
        verification_status: types.VerificationStatus | None = None,
        can_send_gift: bool | None = None,
        title: str | None = None,
        username: str | None = None,
        usernames: list[types.Username] | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        personal_photo: types.ChatPhoto | None = None,
        photo: types.ChatPhoto | None = None,
        public_photo: types.ChatPhoto | None = None,
        stories: list[types.Story] | None = None,
        chat_background: types.ChatBackground | None = None,
        bio: str | None = None,
        description: str | None = None,
        show_message_sender_name: bool | None = None,
        sign_messages: bool | None = None,
        emoji_status: types.EmojiStatus | None = None,
        dc_id: int | None = None,
        folder_id: int | None = None,
        has_protected_content: bool | None = None,
        has_visible_history: bool | None = None,
        has_aggressive_anti_spam_enabled: bool | None = None,
        has_automatic_translation: bool | None = None,
        has_forum_tabs: bool | None = None,
        has_direct_messages_group: bool | None = None,
        invite_link: str | None = None,
        pinned_message: types.Message | None = None,
        sticker_set_name: str | None = None,
        custom_emoji_sticker_set_name: str | None = None,
        can_set_sticker_set: bool | None = None,
        can_send_paid_media: bool | None = None,
        members: list[types.User] | None = None,
        members_count: int | None = None,
        restrictions: list[types.Restriction] | None = None,
        permissions: types.ChatPermissions | None = None,
        personal_channel: types.Chat | None = None,
        personal_channel_message: types.Message | None = None,
        linked_chat_id: int | None = None,
        direct_messages_chat_id: int | None = None,
        parent_chat: types.Chat | None = None,
        linked_chat: types.Chat | None = None,
        send_as_chat: types.Chat | None = None,
        available_reactions: types.ChatReactions | None = None,
        level: int | None = None,
        accent_color_id: int | None = None,
        background_custom_emoji_id: str | None = None,
        profile_accent_color_id: int | None = None,
        profile_background_custom_emoji_id: str | None = None,
        business_away_message: types.BusinessMessage | None = None,
        business_greeting_message: types.BusinessMessage | None = None,
        business_work_hours: types.BusinessMessage | None = None,
        business_location: types.Location | None = None,
        business_intro: types.BusinessIntro | None = None,
        birthday: types.Birthday | None = None,
        message_auto_delete_time: int | None = None,
        unrestrict_boost_count: int | None = None,
        slow_mode_delay: int | None = None,
        slowmode_next_send_date: datetime | None = None,
        join_by_request: bool | None = None,
        join_requests_count: int | None = None,
        banned_until_date: datetime | None = None,
        subscription_until_date: datetime | None = None,
        reactions_limit: int | None = None,
        gift_count: int | None = None,
        bot_verification: types.BotVerification | None = None,
        main_profile_tab: enums.ProfileTab | None = None,
        first_profile_audio: types.Audio | None = None,
        rating: types.UserRating | None = None,
        pending_rating: types.UserRating | None = None,
        pending_rating_date: datetime | None = None,
        settings: types.ChatSettings | None = None,
        admins_count: int | None = None,
        kicked_count: int | None = None,
        banned_count: int | None = None,
        available_min_id: int | None = None,
        boosts_applied: int | None = None,
        channel_admin_rights: types.ChatAdministratorRights | None = None,
        chat_admin_rights: types.ChatAdministratorRights | None = None,
        bot_can_manage_emoji_status: bool | None = None,
        can_delete_channel: bool | None = None,
        can_pin_message: bool | None = None,
        can_schedule_messages: bool | None = None,
        can_set_location: bool | None = None,
        can_set_username: bool | None = None,
        can_view_participants: bool | None = None,
        can_view_revenue: bool | None = None,
        can_view_stars_revenue: bool | None = None,
        can_view_stats: bool | None = None,
        can_send_voice_messages: bool | None = None,
        can_manage_bots: bool | None = None,
        common_chats: int | None = None,
        is_ads_enabled: bool | None = None,
        is_blocked: bool | None = None,
        is_blocked_my_stories_from: bool | None = None,
        is_contact_require_premium: bool | None = None,
        is_phone_calls_available: bool | None = None,
        is_phone_calls_private: bool | None = None,
        is_pinned_stories_available: bool | None = None,
        is_read_dates_available: bool | None = None,
        is_translations_disabled: bool | None = None,
        is_video_calls_available: bool | None = None,
        is_wallpaper_overridden: bool | None = None,
        migrated_from_chat_id: int | None = None,
        migrated_from_max_message_id: int | None = None,
        online_count: int | None = None,
        private_forward_name: str | None = None,
        read_inbox_max_id: int | None = None,
        read_outbox_max_id: int | None = None,
        is_ads_restricted: bool | None = None,
        stats_dc_id: int | None = None,
        theme: str | None = None,
        unread_count: int | None = None,
        view_forum_as_messages: bool | None = None,
        paid_message_star_count: int | None = None,
        is_paid_messages_available: bool | None = None,
        display_gifts_button: bool | None = None,
        uses_unofficial_app: bool | None = None,
        accepted_gift_types: types.AcceptedGiftTypes | None = None,
        note: types.FormattedText | None = None,
        guard_bot: types.User | None = None,
        community_id: int | None = None,
        community: types.Community | None = None,
        raw: raw.types.UserFull | raw.types.ChatFull | raw.types.ChannelFull | None = None,
        active_usernames: list[str] | None = None,
        background: str | None = None,
        distance: int | None = None,
        is_fake: bool | None = None,
        is_participants_hidden: bool | None = None,
        is_scam: bool | None = None,
        is_verified: bool | None = None,
    ):
        super().__init__(client)

        self.id = id
        self.type = type
        self.is_forum = is_forum
        self.is_direct_messages = is_direct_messages
        self.is_min = is_min
        self.is_members_hidden = is_members_hidden
        self.is_restricted = is_restricted
        self.is_creator = is_creator
        self.is_admin = is_admin
        self.is_deactivated = is_deactivated
        self.is_support = is_support
        self.is_stories_hidden = is_stories_hidden
        self.is_stories_unavailable = is_stories_unavailable
        self.is_business_bot = is_business_bot
        self.is_preview = is_preview
        self.is_banned = is_banned
        self.is_call_active = is_call_active
        self.is_call_not_empty = is_call_not_empty
        self.is_public = is_public
        self.is_paid_reactions_available = is_paid_reactions_available
        self.verification_status = verification_status
        self.can_send_gift = can_send_gift
        self.title = title
        self.username = username
        self.usernames = usernames
        self.first_name = first_name
        self.last_name = last_name
        self.personal_photo = personal_photo
        self.photo = photo
        self.public_photo = public_photo
        self.stories = stories
        self.chat_background = chat_background
        self.bio = bio
        self.description = description
        self.show_message_sender_name = show_message_sender_name
        self.sign_messages = sign_messages
        self.emoji_status = emoji_status
        self.dc_id = dc_id
        self.folder_id = folder_id
        self.has_protected_content = has_protected_content
        self.has_visible_history = has_visible_history
        self.has_aggressive_anti_spam_enabled = has_aggressive_anti_spam_enabled
        self.has_automatic_translation = has_automatic_translation
        self.has_forum_tabs = has_forum_tabs
        self.has_direct_messages_group = has_direct_messages_group
        self.invite_link = invite_link
        self.pinned_message = pinned_message
        self.sticker_set_name = sticker_set_name
        self.custom_emoji_sticker_set_name = custom_emoji_sticker_set_name
        self.can_set_sticker_set = can_set_sticker_set
        self.can_send_paid_media = can_send_paid_media
        self.members = members
        self.members_count = members_count
        self.restrictions = restrictions
        self.permissions = permissions
        self.personal_channel = personal_channel
        self.personal_channel_message = personal_channel_message
        self.linked_chat_id = linked_chat_id
        self.direct_messages_chat_id = direct_messages_chat_id
        self.parent_chat = parent_chat
        self.linked_chat = linked_chat
        self.send_as_chat = send_as_chat
        self.available_reactions = available_reactions
        self.level = level
        self.accent_color_id = accent_color_id
        self.background_custom_emoji_id = background_custom_emoji_id
        self.profile_accent_color_id = profile_accent_color_id
        self.profile_background_custom_emoji_id = profile_background_custom_emoji_id
        self.business_away_message = business_away_message
        self.business_greeting_message = business_greeting_message
        self.business_work_hours = business_work_hours
        self.business_location = business_location
        self.business_intro = business_intro
        self.birthday = birthday
        self.message_auto_delete_time = message_auto_delete_time
        self.unrestrict_boost_count = unrestrict_boost_count
        self.slow_mode_delay = slow_mode_delay
        self.slowmode_next_send_date = slowmode_next_send_date
        self.join_by_request = join_by_request
        self.join_requests_count = join_requests_count
        self.banned_until_date = banned_until_date
        self.subscription_until_date = subscription_until_date
        self.reactions_limit = reactions_limit
        self.gift_count = gift_count
        self.bot_verification = bot_verification
        self.main_profile_tab = main_profile_tab
        self.first_profile_audio = first_profile_audio
        self.rating = rating
        self.pending_rating = pending_rating
        self.pending_rating_date = pending_rating_date
        self.settings = settings
        self.admins_count = admins_count
        self.kicked_count = kicked_count
        self.banned_count = banned_count
        self.available_min_id = available_min_id
        self.boosts_applied = boosts_applied
        self.channel_admin_rights = channel_admin_rights
        self.chat_admin_rights = chat_admin_rights
        self.bot_can_manage_emoji_status = bot_can_manage_emoji_status
        self.can_delete_channel = can_delete_channel
        self.can_pin_message = can_pin_message
        self.can_schedule_messages = can_schedule_messages
        self.can_set_location = can_set_location
        self.can_set_username = can_set_username
        self.can_view_participants = can_view_participants
        self.can_view_revenue = can_view_revenue
        self.can_view_stars_revenue = can_view_stars_revenue
        self.can_view_stats = can_view_stats
        self.can_send_voice_messages = can_send_voice_messages
        self.can_manage_bots = can_manage_bots
        self.common_chats = common_chats
        self.is_ads_enabled = is_ads_enabled
        self.is_blocked = is_blocked
        self.is_blocked_my_stories_from = is_blocked_my_stories_from
        self.is_contact_require_premium = is_contact_require_premium
        self.is_phone_calls_available = is_phone_calls_available
        self.is_phone_calls_private = is_phone_calls_private
        self.is_pinned_stories_available = is_pinned_stories_available
        self.is_read_dates_available = is_read_dates_available
        self.is_translations_disabled = is_translations_disabled
        self.is_video_calls_available = is_video_calls_available
        self.is_wallpaper_overridden = is_wallpaper_overridden
        self.migrated_from_chat_id = migrated_from_chat_id
        self.migrated_from_max_message_id = migrated_from_max_message_id
        self.online_count = online_count
        self.private_forward_name = private_forward_name
        self.read_inbox_max_id = read_inbox_max_id
        self.read_outbox_max_id = read_outbox_max_id
        self.is_ads_restricted = is_ads_restricted
        self.stats_dc_id = stats_dc_id
        self.theme = theme
        self.unread_count = unread_count
        self.view_forum_as_messages = view_forum_as_messages
        self.paid_message_star_count = paid_message_star_count
        self.is_paid_messages_available = is_paid_messages_available
        self.display_gifts_button = display_gifts_button
        self.uses_unofficial_app = uses_unofficial_app
        self.accepted_gift_types = accepted_gift_types
        self.note = note
        self.guard_bot = guard_bot
        self.community_id = community_id
        self.community = community
        self.raw = raw
        self.active_usernames = active_usernames
        self.background = background
        self.distance = distance
        self.is_fake = is_fake
        self.is_participants_hidden = is_participants_hidden
        self.is_scam = is_scam
        self.is_verified = is_verified

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name])) or None

    @staticmethod
    def _parse_user_chat(
        client,
        user: raw.types.User,
    ) -> Chat | None:
        if user is None or isinstance(user, raw.types.UserEmpty):
            return None

        peer_id = user.id

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

        return Chat(
            id=peer_id,
            type=enums.ChatType.BOT if user.bot else enums.ChatType.PRIVATE,
            is_restricted=user.restricted,
            is_support=user.support,
            is_stories_hidden=user.stories_hidden,
            is_stories_unavailable=user.stories_unavailable,
            is_business_bot=user.bot_business,
            verification_status=types.VerificationStatus._parse(user),
            username=user.username or (user.usernames[0].username if user.usernames else None),
            usernames=types.List([types.Username._parse(r) for r in user.usernames or []]) or None,
            first_name=user.first_name,
            last_name=user.last_name,
            photo=types.ChatPhoto._parse(client, user.photo, peer_id, user.access_hash),
            restrictions=types.List([
                types.Restriction._parse(r) for r in user.restriction_reason or []
            ])
            or None,
            dc_id=getattr(getattr(user, "photo", None), "dc_id", None),
            emoji_status=types.EmojiStatus._parse(client, user.emoji_status),
            accent_color_id=accent_color_id,
            background_custom_emoji_id=background_custom_emoji_id,
            profile_accent_color_id=profile_accent_color_id,
            profile_background_custom_emoji_id=profile_background_custom_emoji_id,
            paid_message_star_count=user.send_paid_messages_stars,
            can_manage_bots=user.bot_can_manage_bots,
            community_id=utils.get_channel_id(user.linked_community_id)
            if user.linked_community_id is not None
            else None,
            raw=user,
            client=client,
        )

    @staticmethod
    def _parse_chat_chat(client, chat: raw.types.Chat) -> Chat | None:
        if chat is None or isinstance(chat, raw.types.ChatEmpty):
            return None

        peer_id = -chat.id
        usernames = getattr(chat, "usernames", [])

        if isinstance(chat, raw.types.ChatForbidden):
            return Chat(
                id=peer_id,
                type=enums.ChatType.GROUP,
                title=chat.title,
                is_banned=True,
                raw=chat,
                client=client,
            )

        return Chat(
            id=peer_id,
            type=enums.ChatType.GROUP,
            title=chat.title,
            is_creator=chat.creator,
            is_admin=True if chat.admin_rights else None,
            is_deactivated=chat.deactivated,
            is_call_active=chat.call_active,
            is_call_not_empty=chat.call_not_empty,
            usernames=types.List([types.Username._parse(r) for r in usernames or []]) or None,
            photo=types.ChatPhoto._parse(client, chat.photo, peer_id, 0),
            permissions=types.ChatPermissions._parse(chat.default_banned_rights),
            members_count=chat.participants_count,
            dc_id=getattr(getattr(chat, "photo", None), "dc_id", None),
            has_protected_content=chat.noforwards,
            raw=chat,
            client=client,
        )

    @staticmethod
    def _parse_channel_chat(
        client,
        channel: raw.types.Channel,
    ) -> Chat | None:
        if channel is None:
            return None

        peer_id = utils.get_channel_id(channel.id)
        restriction_reason = getattr(channel, "restriction_reason", [])
        usernames = getattr(channel, "usernames", [])

        if isinstance(channel, raw.types.ChannelForbidden):
            return Chat(
                id=peer_id,
                type=enums.ChatType.DIRECT
                if channel.monoforum
                else enums.ChatType.SUPERGROUP
                if channel.megagroup
                else enums.ChatType.CHANNEL,
                title=channel.title,
                is_banned=True,
                banned_until_date=utils.timestamp_to_datetime(
                    getattr(channel, "until_date", None)
                ),
                raw=channel,
                client=client,
            )

        chat_type = enums.ChatType.CHANNEL

        if channel.monoforum:
            chat_type = enums.ChatType.DIRECT
        elif channel.forum:
            chat_type = enums.ChatType.FORUM
        elif channel.megagroup:
            chat_type = enums.ChatType.SUPERGROUP

        accent_color_id = None
        background_custom_emoji_id = None
        profile_accent_color_id = None
        profile_background_custom_emoji_id = None

        if isinstance(channel.color, raw.types.PeerColor):
            accent_color_id = channel.color.color
            background_custom_emoji_id = str(channel.color.background_emoji_id)

        elif isinstance(channel.color, raw.types.PeerColorCollectible):
            accent_color_id = channel.color.accent_color
            background_custom_emoji_id = str(channel.color.background_emoji_id)

        if isinstance(channel.profile_color, raw.types.PeerColor):
            profile_accent_color_id = channel.profile_color.color
            profile_background_custom_emoji_id = str(channel.profile_color.background_emoji_id)

        elif isinstance(channel.profile_color, raw.types.PeerColorCollectible):
            profile_accent_color_id = channel.profile_color.accent_color
            profile_background_custom_emoji_id = str(channel.profile_color.background_emoji_id)

        return Chat(
            id=peer_id,
            type=chat_type,
            is_forum=channel.forum,
            is_direct_messages=channel.monoforum,
            is_min=channel.min,
            is_restricted=channel.restricted,
            is_creator=channel.creator,
            is_admin=True if channel.admin_rights else None,
            is_stories_hidden=channel.stories_hidden,
            is_stories_unavailable=channel.stories_unavailable,
            is_call_active=channel.call_active,
            is_call_not_empty=channel.call_not_empty,
            verification_status=types.VerificationStatus._parse(channel),
            title=channel.title,
            username=channel.username
            or (channel.usernames[0].username if channel.usernames else None),
            usernames=types.List([types.Username._parse(r) for r in usernames or []]) or None,
            photo=types.ChatPhoto._parse(
                client, channel.photo, peer_id, getattr(channel, "access_hash", 0)
            ),
            show_message_sender_name=channel.signature_profiles,
            sign_messages=channel.signatures,
            restrictions=types.List([
                types.Restriction._parse(r) for r in restriction_reason or []
            ])
            or None,
            permissions=types.ChatPermissions._parse(channel.default_banned_rights),
            members_count=channel.participants_count,
            dc_id=getattr(getattr(channel, "photo", None), "dc_id", None),
            emoji_status=types.EmojiStatus._parse(client, channel.emoji_status),
            has_protected_content=channel.noforwards,
            level=channel.level,
            accent_color_id=accent_color_id,
            background_custom_emoji_id=background_custom_emoji_id,
            profile_accent_color_id=profile_accent_color_id,
            profile_background_custom_emoji_id=profile_background_custom_emoji_id,
            subscription_until_date=utils.timestamp_to_datetime(channel.subscription_until_date),
            paid_message_star_count=channel.send_paid_messages_stars,
            has_automatic_translation=channel.autotranslation,
            has_forum_tabs=channel.forum_tabs,
            has_direct_messages_group=channel.broadcast_messages_allowed,
            community_id=utils.get_channel_id(channel.linked_community_id)
            if channel.linked_community_id is not None
            else None,
            raw=channel,
            client=client,
        )

    @staticmethod
    def _parse(
        client,
        message: raw.types.Message | raw.types.MessageService,
        users: dict,
        chats: dict,
        is_chat: bool,
    ) -> Chat:
        from_id = utils.get_raw_peer_id(message.from_id)
        peer_id = utils.get_raw_peer_id(message.peer_id)
        chat_id = (peer_id or from_id) if is_chat else (from_id or peer_id)

        if isinstance(message.peer_id, raw.types.PeerUser):
            return Chat._parse_user_chat(client, users[chat_id])

        if isinstance(message.peer_id, raw.types.PeerChat):
            return Chat._parse_chat_chat(client, chats[chat_id])

        return Chat._parse_channel_chat(client, chats[chat_id])

    @staticmethod
    def _parse_dialog(client, peer, users: dict, chats: dict):
        if isinstance(peer, raw.types.PeerUser):
            return Chat._parse_user_chat(client, users[peer.user_id])
        if isinstance(peer, raw.types.PeerChat):
            return Chat._parse_chat_chat(client, chats[peer.chat_id])
        return Chat._parse_channel_chat(client, chats[peer.channel_id])

    @staticmethod
    async def _parse_full_user(
        client: pyrogram.Client,
        user: raw.types.UserFull,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
    ) -> Chat:
        parsed_chat = Chat._parse_user_chat(client, users[user.id])
        parsed_chat.raw = user

        parsed_chat.settings = await types.ChatSettings._parse(client, user.settings, users)
        # parsed_chat.notify_settings
        parsed_chat.common_chats = user.common_chats_count
        parsed_chat.is_blocked = user.blocked
        parsed_chat.is_phone_calls_available = user.phone_calls_available
        parsed_chat.is_phone_calls_private = user.phone_calls_private
        parsed_chat.can_pin_message = user.can_pin_message
        parsed_chat.can_schedule_messages = user.has_scheduled
        parsed_chat.is_video_calls_available = user.video_calls_available
        parsed_chat.can_send_voice_messages = not user.voice_messages_forbidden
        parsed_chat.is_translations_disabled = user.translations_disabled
        parsed_chat.is_pinned_stories_available = user.stories_pinned_available
        parsed_chat.is_blocked_my_stories_from = user.blocked_my_stories_from
        parsed_chat.is_wallpaper_overridden = user.wallpaper_overridden
        parsed_chat.is_contact_require_premium = user.contact_require_premium
        parsed_chat.is_read_dates_available = not user.read_dates_private
        parsed_chat.is_ads_enabled = user.sponsored_enabled
        parsed_chat.can_view_revenue = user.can_view_revenue
        parsed_chat.bot_can_manage_emoji_status = user.bot_can_manage_emoji_status
        parsed_chat.bio = user.about or None
        parsed_chat.personal_photo = types.ChatPhoto._parse(
            client, user.personal_photo, users[user.id].id, users[user.id].access_hash
        )
        parsed_chat.photo = types.ChatPhoto._parse(
            client, user.profile_photo, users[user.id].id, users[user.id].access_hash
        )
        parsed_chat.public_photo = types.ChatPhoto._parse(
            client, user.fallback_photo, users[user.id].id, users[user.id].access_hash
        )
        # parsed_chat.bot_info = user.bot_info

        if user.pinned_msg_id:
            parsed_chat.pinned_message = await client.get_messages(
                chat_id=parsed_chat.id, pinned=True
            )

        parsed_chat.folder_id = user.folder_id
        parsed_chat.message_auto_delete_time = user.ttl_period
        parsed_chat.theme = await types.ChatTheme._parse(client, user.theme)
        parsed_chat.private_forward_name = user.private_forward_name
        parsed_chat.chat_admin_rights = types.ChatAdministratorRights._parse(
            user.bot_group_admin_rights
        )
        parsed_chat.channel_admin_rights = types.ChatAdministratorRights._parse(
            user.bot_broadcast_admin_rights
        )
        parsed_chat.chat_background = types.ChatBackground._parse(client, user.wallpaper)

        if user.stories:
            parsed_chat.stories = (
                types.List([
                    await types.Story._parse(client, story, user.stories.peer, users, chats)
                    for story in user.stories.stories
                ])
                or None
            )

        parsed_chat.business_work_hours = types.BusinessWorkingHours._parse(
            user.business_work_hours
        )
        parsed_chat.business_location = types.Location._parse_business(user.business_location)
        parsed_chat.business_greeting_message = await types.BusinessMessage._parse(
            client, user.business_greeting_message, users
        )
        parsed_chat.business_away_message = await types.BusinessMessage._parse(
            client, user.business_away_message, users
        )
        parsed_chat.business_intro = await types.BusinessIntro._parse(client, user.business_intro)
        parsed_chat.birthday = types.Birthday._parse(user.birthday)

        if user.personal_channel_id:
            parsed_chat.personal_channel = Chat._parse_channel_chat(
                client, chats[user.personal_channel_id]
            )
            parsed_chat.personal_channel_message = await client.get_messages(
                chat_id=parsed_chat.personal_channel.id, message_ids=user.personal_channel_message
            )

        parsed_chat.gift_count = user.stargifts_count
        # parsed_chat.starref_program
        parsed_chat.bot_verification = await types.BotVerification._parse(
            client, user.bot_verification, users
        )
        parsed_chat.main_profile_tab = (
            enums.ProfileTab(type(user.main_tab)) if user.main_tab else None
        )

        if user.saved_music:
            attributes = {type(i): i for i in user.saved_music.attributes}

            if raw.types.DocumentAttributeAudio in attributes:
                parsed_chat.first_profile_audio = types.Audio._parse(
                    client,
                    user.saved_music,
                    attributes[raw.types.DocumentAttributeAudio],
                    getattr(
                        attributes.get(raw.types.DocumentAttributeFilename),
                        "file_name",
                        None,
                    ),
                )

        parsed_chat.rating = types.UserRating._parse(user.stars_rating)
        parsed_chat.pending_rating = types.UserRating._parse(user.stars_my_pending_rating)
        parsed_chat.pending_rating_date = utils.timestamp_to_datetime(
            user.stars_my_pending_rating_date
        )
        parsed_chat.paid_message_star_count = user.send_paid_messages_stars
        parsed_chat.display_gifts_button = user.display_gifts_button
        parsed_chat.uses_unofficial_app = user.unofficial_security_risk
        parsed_chat.accepted_gift_types = types.AcceptedGiftTypes._parse(user.disallowed_gifts)
        parsed_chat.note = await types.FormattedText._parse(client, user.note)

        if parsed_chat.community_id:
            parsed_chat.community = await types.Community._parse(
                client, chats.get(utils.get_raw_peer_id(parsed_chat.community_id))
            )

        return parsed_chat

    @staticmethod
    async def _parse_full_chat(
        client: pyrogram.Client,
        chat: raw.types.ChatFull,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
    ) -> Chat:
        parsed_chat = Chat._parse_chat_chat(client, chats[chat.id])
        parsed_chat.raw = chat

        parsed_chat.description = chat.about or None

        if isinstance(chat.participants, raw.types.ChatParticipants):
            parsed_chat.members_count = len(chat.participants.participants)

        # parsed_chat.notify_settings
        parsed_chat.can_set_username = chat.can_set_username
        parsed_chat.can_schedule_messages = chat.has_scheduled
        parsed_chat.is_translations_disabled = chat.translations_disabled

        if isinstance(chat.exported_invite, raw.types.ChatInviteExported):
            parsed_chat.invite_link = chat.exported_invite.link

        # parsed_chat.bot_info

        if chat.pinned_msg_id:
            parsed_chat.pinned_message = await client.get_messages(
                chat_id=parsed_chat.id, pinned=True
            )

        parsed_chat.folder_id = chat.folder_id
        # parsed_chat.call
        parsed_chat.message_auto_delete_time = chat.ttl_period
        # parsed_chat.groupcall_default_join_as
        parsed_chat.theme = chat.theme_emoticon
        parsed_chat.join_requests_count = chat.requests_pending
        # parsed_chat.recent_requesters
        parsed_chat.available_reactions = types.ChatReactions._parse(
            client, chat.available_reactions
        )
        parsed_chat.reactions_limit = chat.reactions_limit

        return parsed_chat

    @staticmethod
    async def _parse_full_channel(
        client: pyrogram.Client,
        channel: raw.types.ChannelFull,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
    ) -> Chat:
        parsed_chat = Chat._parse_channel_chat(client, chats[channel.id])
        parsed_chat.raw = channel

        parsed_chat.description = channel.about or None
        parsed_chat.read_inbox_max_id = channel.read_inbox_max_id
        parsed_chat.read_outbox_max_id = channel.read_outbox_max_id
        parsed_chat.unread_count = channel.unread_count
        # parsed_chat.chat_photo
        # parsed_chat.notify_settings
        # parsed_chat.bot_info
        # parsed_chat.pts
        parsed_chat.can_view_participants = channel.can_view_participants
        parsed_chat.can_set_username = channel.can_set_username
        parsed_chat.can_set_sticker_set = channel.can_set_stickers
        parsed_chat.has_visible_history = channel.hidden_prehistory
        parsed_chat.can_set_location = channel.can_set_location
        parsed_chat.can_schedule_messages = channel.has_scheduled
        parsed_chat.can_view_stats = channel.can_view_stats
        parsed_chat.is_blocked = channel.blocked
        parsed_chat.can_delete_channel = channel.can_delete_channel
        parsed_chat.has_aggressive_anti_spam_enabled = channel.antispam
        parsed_chat.is_members_hidden = channel.participants_hidden
        parsed_chat.is_translations_disabled = channel.translations_disabled
        parsed_chat.is_pinned_stories_available = channel.stories_pinned_available
        parsed_chat.view_forum_as_messages = channel.view_forum_as_messages
        parsed_chat.is_ads_restricted = channel.restricted_sponsored
        parsed_chat.can_view_revenue = channel.can_view_revenue
        parsed_chat.can_send_paid_media = channel.paid_media_allowed
        parsed_chat.can_view_stars_revenue = channel.can_view_stars_revenue
        parsed_chat.is_paid_reactions_available = channel.paid_messages_available
        parsed_chat.can_send_gift = channel.stargifts_available
        parsed_chat.members_count = channel.participants_count
        parsed_chat.admins_count = channel.admins_count
        parsed_chat.kicked_count = channel.kicked_count
        parsed_chat.banned_count = channel.banned_count
        parsed_chat.online_count = channel.online_count

        if isinstance(channel.exported_invite, raw.types.ChatInviteExported):
            parsed_chat.invite_link = channel.exported_invite.link

        parsed_chat.migrated_from_chat_id = channel.migrated_from_chat_id
        parsed_chat.migrated_from_max_id = channel.migrated_from_max_id

        if channel.pinned_msg_id:
            parsed_chat.pinned_message = await client.get_messages(
                chat_id=parsed_chat.id, pinned=True
            )

        # parsed_chat.stickerset
        parsed_chat.available_min_id = channel.available_min_id
        parsed_chat.folder_id = channel.folder_id

        if chats.get(channel.linked_chat_id):
            parsed_chat.linked_chat_id = utils.get_channel_id(channel.linked_chat_id)
            parsed_chat.linked_chat = Chat._parse_channel_chat(
                client, chats[channel.linked_chat_id]
            )

        if chats.get(chats[channel.id].linked_monoforum_id):
            parsed_chat.direct_messages_chat_id = utils.get_channel_id(
                chats[channel.id].linked_monoforum_id
            )
            parsed_chat.parent_chat = Chat._parse_channel_chat(
                client, chats[chats[channel.id].linked_monoforum_id]
            )

        # parsed_chat.location
        parsed_chat.slow_mode_delay = channel.slowmode_seconds
        parsed_chat.slowmode_next_send_date = utils.timestamp_to_datetime(
            channel.slowmode_next_send_date
        )
        parsed_chat.stats_dc_id = channel.stats_dc
        # parsed_chat.call
        parsed_chat.message_auto_delete_time = channel.ttl_period
        # parsed_chat.pending_suggestions
        # parsed_chat.groupcall_default_join_as
        parsed_chat.theme = channel.theme_emoticon
        parsed_chat.join_requests_count = channel.requests_pending
        # parsed_chat.recent_requesters

        if channel.default_send_as:
            if isinstance(channel.default_send_as, raw.types.PeerUser):
                send_as_raw = users[channel.default_send_as.user_id]
            else:
                send_as_raw = chats[channel.default_send_as.channel_id]

            parsed_chat.send_as_chat = Chat._parse_chat(client, send_as_raw)

        parsed_chat.available_reactions = types.ChatReactions._parse(
            client, channel.available_reactions
        )
        parsed_chat.reactions_limit = channel.reactions_limit

        if channel.stories:
            parsed_chat.stories = (
                types.List([
                    await types.Story._parse(client, story, channel.stories.peer, users, chats)
                    for story in channel.stories.stories
                ])
                or None
            )

        parsed_chat.chat_background = types.ChatBackground._parse(client, channel.wallpaper)
        parsed_chat.boosts_applied = channel.boosts_applied
        parsed_chat.unrestrict_boost_count = channel.boosts_unrestrict
        parsed_chat.custom_emoji_sticker_set_name = getattr(channel.emojiset, "short_name", None)
        parsed_chat.bot_verification = await types.BotVerification._parse(
            client, channel.bot_verification, users
        )
        parsed_chat.main_profile_tab = (
            enums.ProfileTab(type(channel.main_tab)) if channel.main_tab else None
        )
        parsed_chat.gift_count = channel.stargifts_count
        parsed_chat.sticker_set_name = getattr(channel.stickerset, "short_name", None)
        parsed_chat.is_paid_messages_available = channel.paid_messages_available
        parsed_chat.guard_bot = types.User._parse(client, users.get(channel.guard_bot_id))

        if parsed_chat.community_id:
            parsed_chat.community = await types.Community._parse(
                client, chats.get(utils.get_raw_peer_id(parsed_chat.community_id))
            )

        return parsed_chat

    @staticmethod
    async def _parse_full(
        client: pyrogram.Client,
        chat_full: raw.types.users.UserFull | raw.types.messages.ChatFull,
    ) -> Chat | None:
        users = {u.id: u for u in chat_full.users}
        chats = {c.id: c for c in chat_full.chats}

        if isinstance(chat_full, raw.types.users.UserFull):
            return await Chat._parse_full_user(client, chat_full.full_user, users, chats)
        if isinstance(chat_full, raw.types.messages.ChatFull) and isinstance(
            chat_full.full_chat, raw.types.ChatFull
        ):
            return await Chat._parse_full_chat(client, chat_full.full_chat, users, chats)
        if isinstance(chat_full, raw.types.messages.ChatFull) and isinstance(
            chat_full.full_chat, raw.types.ChannelFull
        ):
            return await Chat._parse_full_channel(client, chat_full.full_chat, users, chats)
        return None

    @staticmethod
    def _parse_chat(
        client, chat: raw.types.Chat | raw.types.User | raw.types.Channel | None
    ) -> Chat | None:
        """Parse any peer constructor into a :obj:`Chat`.

        Returns ``None`` for a missing peer, matching :meth:`User._parse`. Callers routinely look a
        peer up in the ``users``/``chats`` maps that came with an update and pass the result
        straight in; when the peer is not in the map the lookup yields ``None``, and every such
        call site would otherwise need its own guard.
        """
        if chat is None:
            return None
        if isinstance(chat, raw.types.Chat):
            return Chat._parse_chat_chat(client, chat)
        if isinstance(chat, raw.types.User):
            return Chat._parse_user_chat(client, chat)
        return Chat._parse_channel_chat(client, chat)

    def listen(
        self,
        filters: filters.Filter | None = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: int | None = None,
        unallowed_click_alert: bool = True,
        user_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
    ):
        """
        Bound method *listen* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.listen(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.listen()

        Parameters:
            filters (``Optional[filters.Filter]``):
                A filter to check if the listener should be fulfilled.

            listener_type (``ListenerTypes``):
                The type of listener to create. Defaults to :attr:`pyrogram.types.ListenerTypes.MESSAGE`.

            timeout (``Optional[int]``):
                The maximum amount of time to wait for the listener to be fulfilled. Defaults to ``None``.

            unallowed_click_alert (``bool``):
                Whether to alert the user if they click on a button that is not intended for them. Defaults to ``True``.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to listen for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to listen for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to listen for. Defaults to ``None``.

        Returns:
            Union[:obj:`~pyrogram.types.Message`, :obj:`~pyrogram.types.CallbackQuery`]: The Message or CallbackQuery
        """
        return self._client.listen(
            chat_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            user_id=user_id,
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
        user_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
        *args,
        **kwargs,
    ):
        """
        Bound method *ask* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.ask(chat_id=chat_id, text=text)

        Example:

            .. code-block:: python

                await chat.ask("What's your name?")

        Parameters:
            text (``str``):
                The text to send.

            filters (``Optional[filters.Filter]``):
                Same as :meth:`pyrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`pyrogram.Client.listen`.

            timeout (``Optional[int]``):
                Same as :meth:`pyrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`pyrogram.Client.listen`.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to listen for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to listen for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to listen for. Defaults to ``None``.

            args (``Any``):
                Additional arguments to pass to :meth:`pyrogram.Client.send_message`.

            kwargs (``Any``):
                Additional keyword arguments to pass to :meth:`pyrogram.Client.send_message`.

        Returns:
            Union[:obj:`~pyrogram.types.Message`, :obj:`~pyrogram.types.CallbackQuery`]: The Message or CallbackQuery
        """
        return self._client.ask(
            *args,
            chat_id=self.id,
            text=text,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            **kwargs,
        )

    def stop_listening(
        self,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        user_id: int | str | list[int | str] | None = None,
        message_id: int | list[int] | None = None,
        inline_message_id: str | list[str] | None = None,
    ):
        """
        Bound method *stop_listening* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.stop_listening(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.stop_listening()

        Parameters:
            listener_type (``ListenerTypes``):
                The type of listener to stop listening for. Defaults to :attr:`pyrogram.types.ListenerTypes.MESSAGE`.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to stop listening for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to stop listening for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to stop listening for. Defaults to ``None``.

        Returns:
            ``bool``: The return value of :meth:`pyrogram.Client.stop_listening`.
        """
        return self._client.stop_listening(
            chat_id=self.id,
            listener_type=listener_type,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    async def archive(self):
        """Bound method *archive* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.archive_chats(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.archive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.archive_chats(self.id)

    async def unarchive(self):
        """Bound method *unarchive* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unarchive_chats(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.unarchive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unarchive_chats(self.id)

    # TODO: Remove notes about "All Members Are Admins" for basic groups, the attribute doesn't exist anymore
    async def set_title(self, title: str) -> bool:
        """Bound method *set_title* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_title(chat_id=chat_id, title=title)

        Example:
            .. code-block:: python

                await chat.set_title("Lounge")

        Note:
            In regular groups (non-supergroups), this method will only work if the "All Members Are Admins"
            setting is off.

        Parameters:
            title (``str``):
                New chat title, 1-255 characters.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of Telegram RPC error.
            ValueError: In case a chat_id belongs to user.
        """

        return await self._client.set_chat_title(chat_id=self.id, title=title)

    async def set_description(self, description: str) -> bool:
        """Bound method *set_description* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_description(chat_id=chat_id, description=description)

        Example:
            .. code-block:: python

                await chat.set_chat_description("Don't spam!")

        Parameters:
            description (``str``):
                New chat description, 0-255 characters.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of Telegram RPC error.
            ValueError: If a chat_id doesn't belong to a supergroup or a channel.
        """

        return await self._client.set_chat_description(chat_id=self.id, description=description)

    async def set_photo(
        self,
        *,
        photo: str | BinaryIO | None = None,
        video: str | BinaryIO | None = None,
        video_start_ts: float | None = None,
    ) -> bool:
        """Bound method *set_photo* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_photo(chat_id=chat_id, photo=photo)

        Example:
            .. code-block:: python

                # Set chat photo using a local file
                await chat.set_photo(photo="photo.jpg")

                # Set chat photo using an existing Photo file_id
                await chat.set_photo(photo=photo.file_id)

                # Set chat video using a local file
                await chat.set_photo(video="video.mp4")

                # Set chat photo using an existing Video file_id
                await chat.set_photo(video=video.file_id)

        Parameters:
            photo (``str`` | ``BinaryIO``, *optional*):
                New chat photo. You can pass a :obj:`~pyrogram.types.Photo` file_id, a file path to upload a new photo
                from your local machine or a binary file-like object with its attribute
                ".name" set for in-memory uploads.

            video (``str`` | ``BinaryIO``, *optional*):
                New chat video. You can pass a :obj:`~pyrogram.types.Video` file_id, a file path to upload a new video
                from your local machine or a binary file-like object with its attribute
                ".name" set for in-memory uploads.

            video_start_ts (``float``, *optional*):
                The timestamp in seconds of the video frame to use as photo profile preview.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
            ValueError: if a chat_id belongs to user.
        """

        return await self._client.set_chat_photo(
            chat_id=self.id, photo=photo, video=video, video_start_ts=video_start_ts
        )

    async def ban_member(
        self, user_id: int | str, until_date: datetime = utils.zero_datetime()
    ) -> types.Message | bool:
        """Bound method *ban_member* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.ban_chat_member(chat_id=chat_id, user_id=user_id)

        Example:
            .. code-block:: python

                await chat.ban_member(123456789)

        Note:
            In regular groups (non-supergroups), this method will only work if the "All Members Are Admins" setting is
            off in the target group. Otherwise members may only be removed by the group's creator or by the member
            that added them.

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            until_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the user will be unbanned.
                If user is banned for more than 366 days or less than 30 seconds from the current time they are
                considered to be banned forever. Defaults to epoch (ban forever).

        Returns:
            :obj:`~pyrogram.types.Message` | ``bool``: On success, a service message will be returned (when applicable), otherwise, in
            case a message object couldn't be returned, True is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.ban_chat_member(
            chat_id=self.id, user_id=user_id, until_date=until_date
        )

    async def unban_member(self, user_id: int | str) -> bool:
        """Bound method *unban_member* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unban_chat_member(chat_id=chat_id, user_id=user_id)

        Example:
            .. code-block:: python

                await chat.unban_member(123456789)

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unban_chat_member(
            chat_id=self.id,
            user_id=user_id,
        )

    async def restrict_member(
        self,
        user_id: int | str,
        permissions: types.ChatPermissions,
        until_date: datetime = utils.zero_datetime(),
    ) -> types.Chat:
        """Bound method *unban_member* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.restrict_chat_member(
                chat_id=chat_id, user_id=user_id, permissions=ChatPermissions()
            )

        Example:
            .. code-block:: python

                await chat.restrict_member(user_id, ChatPermissions())

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            permissions (:obj:`~pyrogram.types.ChatPermissions`):
                New user permissions.

            until_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the user will be unbanned.
                If user is banned for more than 366 days or less than 30 seconds from the current time they are
                considered to be banned forever. Defaults to epoch (ban forever).

        Returns:
            :obj:`~pyrogram.types.Chat`: On success, a chat object is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.restrict_chat_member(
            chat_id=self.id,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date,
        )

    # Set None as privileges default due to issues with partially initialized module, because at the time Chat
    # is being initialized, ChatPrivileges would be required here, but was not initialized yet.
    async def promote_member(
        self, user_id: int | str, privileges: types.ChatPrivileges = None
    ) -> bool:
        """Bound method *promote_member* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.promote_chat_member(chat_id=chat_id, user_id=user_id)

        Example:

            .. code-block:: python

                await chat.promote_member(123456789)

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            privileges (:obj:`~pyrogram.types.ChatPrivileges`, *optional*):
                New user privileges.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.promote_chat_member(
            chat_id=self.id, user_id=user_id, privileges=privileges
        )

    async def join(self):
        """Bound method *join* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.join_chat(123456789)

        Example:
            .. code-block:: python

                await chat.join()

        Note:
            This only works for public groups, channels that have set a username or linked chats.

        Returns:
            :obj:`~pyrogram.types.Chat`: On success, a chat object is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.join_chat(self.username or self.id)

    async def leave(self):
        """Bound method *leave* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.leave_chat(123456789)

        Example:
            .. code-block:: python

                await chat.leave()

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.leave_chat(self.id)

    async def export_invite_link(self):
        """Bound method *export_invite_link* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            client.export_chat_invite_link(123456789)

        Example:
            .. code-block:: python

                chat.export_invite_link()

        Returns:
            ``str``: On success, the exported invite link is returned.

        Raises:
            ValueError: In case the chat_id belongs to a user.
        """

        return await self._client.export_chat_invite_link(self.id)

    async def get_member(
        self,
        user_id: int | str,
    ) -> types.ChatMember:
        """Bound method *get_member* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.get_chat_member(chat_id=chat_id, user_id=user_id)

        Example:
            .. code-block:: python

                await chat.get_member(user_id)

        Returns:
            :obj:`~pyrogram.types.ChatMember`: On success, a chat member is returned.
        """

        return await self._client.get_chat_member(self.id, user_id=user_id)

    def get_members(
        self,
        query: str = "",
        limit: int = 0,
        filter: enums.ChatMembersFilter = enums.ChatMembersFilter.SEARCH,
    ) -> AsyncGenerator[types.ChatMember, None] | None:
        """Bound method *get_members* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            async for member in client.get_chat_members(chat_id):
                print(member)

        Example:
            .. code-block:: python

                async for member in chat.get_members():
                    print(member)

        Parameters:
            query (``str``, *optional*):
                Query string to filter members based on their display names and usernames.
                Only applicable to supergroups and channels. Defaults to "" (empty string).
                A query string is applicable only for :obj:`~pyrogram.enums.ChatMembersFilter.SEARCH`,
                :obj:`~pyrogram.enums.ChatMembersFilter.BANNED` and :obj:`~pyrogram.enums.ChatMembersFilter.RESTRICTED`
                filters only.

            limit (``int``, *optional*):
                Limits the number of members to be retrieved.

            filter (:obj:`~pyrogram.enums.ChatMembersFilter`, *optional*):
                Filter used to select the kind of members you want to retrieve. Only applicable for supergroups
                and channels.

        Returns:
            ``Generator``: On success, a generator yielding :obj:`~pyrogram.types.ChatMember` objects is returned.
        """

        return self._client.get_chat_members(self.id, query=query, limit=limit, filter=filter)

    async def add_members(
        self,
        user_ids: int | str | list[int | str],
        forward_limit: int = 100,
    ) -> bool:
        """Bound method *add_members* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.add_chat_members(chat_id, user_id)

        Example:
            .. code-block:: python

                await chat.add_members(user_id)

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.add_chat_members(
            self.id, user_ids=user_ids, forward_limit=forward_limit
        )

    async def mark_unread(
        self,
    ) -> bool:
        """Bound method *mark_unread* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.mark_unread(chat_id)

        Example:
            .. code-block:: python

                await chat.mark_unread()

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.mark_chat_unread(self.id)

    async def set_protected_content(self, enabled: bool) -> bool:
        """Bound method *set_protected_content* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_protected_content(chat_id, enabled)

        Parameters:
            enabled (``bool``):
                Pass True to enable the protected content setting, False to disable.

        Example:
            .. code-block:: python

                await chat.set_protected_content(enabled)

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.set_chat_protected_content(self.id, enabled=enabled)

    async def unpin_all_messages(self) -> bool:
        """Bound method *unpin_all_messages* of :obj:`~pyrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            client.unpin_all_chat_messages(chat_id)

        Example:
            .. code-block:: python

                chat.unpin_all_messages()

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.unpin_all_chat_messages(self.id)
