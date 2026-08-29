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

import contextlib
import logging
from functools import partial
from typing import TYPE_CHECKING, BinaryIO

import pyrogram
from pyrogram import enums, filters, raw, types, utils
from pyrogram.errors import (
    ChannelForumMissing,
    ChannelInvalid,
    ChannelPrivate,
    ChatAdminRequired,
    MessageIdsEmpty,
    PeerIdInvalid,
)
from pyrogram.parser import Parser
from pyrogram.parser import utils as parser_utils
from pyrogram.types.object import Object
from pyrogram.types.pyromod import ListenerTypes
from pyrogram.types.update import Update

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from re import Match

log = logging.getLogger(__name__)


class Str(str):
    __slots__ = ("entities",)

    def __init__(self, *args):
        super().__init__()

        self.entities = None

    def init(self, entities):
        self.entities = entities

        return self

    @property
    def markdown(self):
        return Parser.unparse(self, self.entities, False)

    @property
    def html(self):
        return Parser.unparse(self, self.entities, True)

    def __getitem__(self, item):
        return parser_utils.remove_surrogates(parser_utils.add_surrogates(self)[item])


class Message(Object, Update):
    """A message.

    Parameters:
        id (``int``):
            Unique message identifier inside this chat, 0 for ephemeral messages.
            In specific instances (e.g., a message containing a video sent to a big chat), the server might automatically schedule a message instead of sending it immediately.
            In such cases, this message will be unusable until it is actually sent.

        from_user (:obj:`~pyrogram.types.User`, *optional*):
            Sender, empty for messages sent to channels.

        sender_chat (:obj:`~pyrogram.types.Chat`, *optional*):
            Sender of the message, sent on behalf of a chat.
            The channel itself for channel messages.
            The supergroup itself for messages from anonymous group administrators.
            The linked channel for messages automatically forwarded to the discussion group.

        sender_boost_count (``int``, *optional*):
            If the sender of the message boosted the chat, the number of boosts added by the user.

        sender_business_bot (:obj:`~pyrogram.types.User`, *optional*):
            The bot that actually sent the message on behalf of the business account. Available only for outgoing messages sent on behalf of the connected business account.

        sender_tag (``str``, *optional*):
            Tag or custom title of the sender of the message.
            For supergroups only.

        receiver_user (:obj:`~pyrogram.types.User`, *optional*):
            For ephemeral messages, the user who received the message.

        ephemeral_message_id (``int``, *optional*):
            For ephemeral messages, identifier of the ephemeral message inside this chat.
            The identifier may be reused for another ephemeral message after the message is deleted or expires.

        date (:py:obj:`~datetime.datetime`, *optional*):
            Date the message was sent.

        guest_query_id (``str``, *optional*):
            The unique identifier for the guest query.
            Use this identifier with the method :meth:`~pyrogram.Client.answer_guest_query` to send a response message.
            If non-empty, the message belongs to the chat where the guest bot was summoned, which may not coincide with other existing bot chats sharing the same identifier.

        chat (:obj:`~pyrogram.types.Chat`, *optional*):
            Conversation the message belongs to.

        topic_message (``bool``, *optional*):
            True, if the message is a forum topic message.

        automatic_forward (``bool``, *optional*):
            True, if the message is a channel post that was automatically forwarded to the connected discussion group.

        from_offline (``bool``, *optional*):
            True, if the message was sent by an implicit action, for example, as an away or a greeting business message, or as a scheduled message.

        topic (:obj:`~pyrogram.types.ForumTopic`, *optional*):
            Topic the message belongs to.

        forward_origin (:obj:`~pyrogram.types.MessageOrigin`, *optional*):
            Information about the original message for forwarded messages.

        message_thread_id (``int``, *optional*):
            Unique identifier of a message thread to which the message belongs.
            For forums only.

        direct_messages_topic_id (``int``, *optional*):
            Unique identifier of a topic in a channel direct messages chat administered by the current user.
            For direct chats only.

        effect_id (``int``, *optional*):
            Unique identifier of the message effect.
            For private chats only.

        rich_message (:obj:`~pyrogram.types.Message`, *optional*):
            Message is a rich formatted message.

        reply_to_message_id (``int``, *optional*):
            The id of the message which this message directly replied to.

        reply_to_story_id (``int``, *optional*):
            The id of the story which this message directly replied to.

        reply_to_story_user_id (``int``, *optional*):
            The id of the story sender which this message directly replied to.

        reply_to_top_message_id (``int``, *optional*):
            The id of the first message which started this message thread.

        reply_to_poll_option_id (``str``, *optional*):
            Persistent identifier of the specific poll option that is being replied to.

        reply_to_message (:obj:`~pyrogram.types.Message`, *optional*):
            For replies, the original message. Note that the Message object in this field will not contain
            further reply_to_message fields even if it itself is a reply.

        reply_to_story (:obj:`~pyrogram.types.Story`, *optional*):
            For replies, the original story.

        reply_to_checklist_task_id (``int``, *optional*):
            Identifier of the specific checklist task that is being replied to.

        mentioned (``bool``, *optional*):
            The message contains a mention.

        empty (``bool``, *optional*):
            The message is empty.
            A message can be empty in case it was deleted or you tried to retrieve a message that doesn't exist yet.

        service (:obj:`~pyrogram.enums.MessageServiceType`, *optional*):
            The message is a service message.
            This field will contain the enumeration type of the service message.
            You can use ``service = getattr(message, message.service.value)`` to access the service message.

        media (:obj:`~pyrogram.enums.MessageMediaType`, *optional*):
            The message is a media message.
            This field will contain the enumeration type of the media message.
            You can use ``media = getattr(message, message.media.value)`` to access the media message.

        paid_media (:obj:`~pyrogram.types.PaidMediaInfo`, *optional*):
            The message is a paid media message.

        checklist (:obj:`~pyrogram.types.Checklist`, *optional*):
            The message is a checklist message.

        show_caption_above_media (``bool``, *optional*):
            If True, caption must be shown above the message media.

        edit_date (:py:obj:`~datetime.datetime`, *optional*):
            Date the message was last edited.

        edit_hidden (``bool``, *optional*):
            The message shown as not modified.
            A message can be not modified in case it has received a reaction.

        media_group_id (``int``, *optional*):
            The unique identifier of a media message group this message belongs to.

        author_signature (``str``, *optional*):
            Signature of the post author for messages in channels, or the custom title of an anonymous group
            administrator.

        is_paid_post (``bool``, *optional*):
            True, if the message is a paid post.
            Note that such posts must not be deleted for 24 hours to receive the payment and can't be edited.

        has_protected_content (``bool``, *optional*):
            True, if the message can't be forwarded.

        has_media_spoiler (``bool``, *optional*):
            True, if the message media is covered by a spoiler animation.

        text (``str``, *optional*):
            For text messages, the actual UTF-8 text of the message, 0-4096 characters.
            If the message contains entities (bold, italic, ...) you can access *text.markdown* or
            *text.html* to get the marked up message text. In case there is no entity, the fields
            will contain the same text as *text*.

        entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text.

        caption_entities (List of :obj:`~pyrogram.types.MessageEntity`, *optional*):
            For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear
            in the caption.

        audio (:obj:`~pyrogram.types.Audio`, *optional*):
            Message is an audio file, information about the file.

        document (:obj:`~pyrogram.types.Document`, *optional*):
            Message is a general file, information about the file.

        photo (:obj:`~pyrogram.types.Photo`, *optional*):
            Message is a photo, information about the photo.

        live_photo (:obj:`~pyrogram.types.LivePhoto`, *optional*):
            Message is a live photo, information about the live photo.
            For backward compatibility, when this field is set, the photo field will also be set.

        sticker (:obj:`~pyrogram.types.Sticker`, *optional*):
            Message is a sticker, information about the sticker.

        animation (:obj:`~pyrogram.types.Animation`, *optional*):
            Message is an animation, information about the animation.

        game (:obj:`~pyrogram.types.Game`, *optional*):
            Message is a game, information about the game.

        giveaway (:obj:`~pyrogram.types.Giveaway`, *optional*):
            Message is a giveaway, information about the giveaway.

        invoice (:obj:`~pyrogram.types.Invoice`, *optional*):
            Message is a invoice, information about the invoice.
            `More about payments » <https://core.telegram.org/bots/api#payments>`_

        story (:obj:`~pyrogram.types.Story`, *optional*):
            Message is a story, information about the story.

        video (:obj:`~pyrogram.types.Video`, *optional*):
            Message is a video, information about the video.

        video_processing_pending (``bool``, *optional*):
            True, if the video is still processing.

        voice (:obj:`~pyrogram.types.Voice`, *optional*):
            Message is a voice message, information about the file.

        video_note (:obj:`~pyrogram.types.VideoNote`, *optional*):
            Message is a video note, information about the video message.

        caption (``str``, *optional*):
            Caption for the audio, document, photo, video or voice, 0-1024 characters.
            If the message contains caption entities (bold, italic, ...) you can access *caption.markdown* or
            *caption.html* to get the marked up caption text. In case there is no caption entity, the fields
            will contain the same text as *caption*.

        contact (:obj:`~pyrogram.types.Contact`, *optional*):
            Message is a shared contact, information about the contact.

        location (:obj:`~pyrogram.types.Location`, *optional*):
            Message is a shared location, information about the location.

        venue (:obj:`~pyrogram.types.Venue`, *optional*):
            Message is a venue, information about the venue.

        web_page (:obj:`~pyrogram.types.WebPage`, *optional*):
            Message was sent with a webpage preview.

        link_preview_options (:obj:`~pyrogram.types.LinkPreviewOptions`, *optional*):
            Options used for link preview generation for the message.

        poll (:obj:`~pyrogram.types.Poll`, *optional*):
            Message is a native poll, information about the poll.

        dice (:obj:`~pyrogram.types.Dice`, *optional*):
            A dice containing a value that is randomly generated by Telegram.

        new_chat_members (List of :obj:`~pyrogram.types.User`, *optional*):
            New members that were added to the group or supergroup and information about them
            (the bot itself may be one of these members).

        left_chat_member (:obj:`~pyrogram.types.User`, *optional*):
            A member was removed from the group, information about them (this member may be the bot itself).

        chat_owner_left (:obj:`~pyrogram.types.ChatOwnerLeft`, *optional*):
            Service message: chat owner has left.

        chat_owner_changed (:obj:`~pyrogram.types.ChatOwnerChanged`, *optional*):
            Service message: chat owner has changed.

        chat_join_type (:obj:`~pyrogram.enums.ChatJoinType`, *optional*):
            This field will contain the enumeration type of how the user had joined the chat.

        new_chat_title (``str``, *optional*):
            A chat title was changed to this value.

        new_chat_photo (:obj:`~pyrogram.types.Photo`, *optional*):
            A chat photo was change to this value.

        delete_chat_photo (``bool``, *optional*):
            Service message: the chat photo was deleted.

        group_chat_created (``bool``, *optional*):
            Service message: the group has been created.

        supergroup_chat_created (``bool``, *optional*):
            Service message: the supergroup has been created.
            This field can't be received in a message coming through updates, because bot can't be a member of a
            supergroup when it is created. It can only be found in reply_to_message if someone replies to a very
            first message in a directly created supergroup.

        channel_chat_created (``bool``, *optional*):
            Service message: the channel has been created.
            This field can't be received in a message coming through updates, because bot can't be a member of a
            channel when it is created. It can only be found in reply_to_message if someone replies to a very
            first message in a channel.

        migrate_to_chat_id (``int``, *optional*):
            The group has been migrated to a supergroup with the specified identifier.
            This number may be greater than 32 bits and some programming languages may have difficulty/silent defects
            in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float
            type are safe for storing this identifier.

        migrate_from_chat_id (``int``, *optional*):
            The supergroup has been migrated from a group with the specified identifier.
            This number may be greater than 32 bits and some programming languages may have difficulty/silent defects
            in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float
            type are safe for storing this identifier.

        pinned_message (:obj:`~pyrogram.types.Message`, *optional*):
            Specified message was pinned.
            Note that the Message object in this field will not contain further reply_to_message fields even if it
            is itself a reply.

        game_high_score (:obj:`~pyrogram.types.GameHighScore`, *optional*):
            The game score for a user.
            The reply_to_message field will contain the game Message.

        views (``int``, *optional*):
            Channel post views.

        forwards (``int``, *optional*):
            Channel post forwards.

        via_bot (:obj:`~pyrogram.types.User`):
            The information of the bot that generated the message from an inline query of a user.

        outgoing (``bool``, *optional*):
            Whether the message is incoming or outgoing.
            Messages received from other chats are incoming (*outgoing* is False).
            Messages sent from yourself to other chats are outgoing (*outgoing* is True).
            An exception is made for your own personal chat; messages sent there will be incoming.

        external_reply (:obj:`~pyrogram.types.ExternalReplyInfo`, *optional*):
            Information about the message that is being replied to, which may come from another chat or forum topic.

        quote (:obj:`~pyrogram.types.TextQuote`, *optional*):
            Chosen quote from the replied message.

        matches (List of regex Matches, *optional*):
            A list containing all `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_ that match
            the text of this message. Only applicable when using :obj:`Filters.regex <pyrogram.Filters.regex>`.

        command (List of ``str``, *optional*):
            A list containing the command and its arguments, if any.
            E.g.: "/start 1 2 3" would produce ["start", "1", "2", "3"].
            Only applicable when using :obj:`~pyrogram.filters.command`.

        forum_topic_created (:obj:`~pyrogram.types.ForumTopicCreated`, *optional*):
            Service message: forum topic created

        forum_topic_closed (:obj:`~pyrogram.types.ForumTopicClosed`, *optional*):
            Service message: forum topic closed

        forum_topic_reopened (:obj:`~pyrogram.types.ForumTopicReopened`, *optional*):
            Service message: forum topic reopened

        forum_topic_edited (:obj:`~pyrogram.types.ForumTopicEdited`, *optional*):
            Service message: forum topic edited

        general_forum_topic_hidden (:obj:`~pyrogram.types.GeneralForumTopicHidden`, *optional*):
            Service message: general forum topic hidden

        general_forum_topic_unhidden (:obj:`~pyrogram.types.GeneralForumTopicUnhidden`, *optional*):
            Service message: general forum topic unhidden

        video_chat_scheduled (:obj:`~pyrogram.types.VideoChatScheduled`, *optional*):
            Service message: voice chat scheduled.

        history_cleared (:obj:`~pyrogram.types.HistoryCleared`, *optional*):
            Service message: history cleared

        video_chat_started (:obj:`~pyrogram.types.VideoChatStarted`, *optional*):
            Service message: the voice chat started.

        video_chat_ended (:obj:`~pyrogram.types.VideoChatEnded`, *optional*):
            Service message: the voice chat has ended.

        video_chat_members_invited (:obj:`~pyrogram.types.VideoChatMembersInvited`, *optional*):
            Service message: new members were invited to the voice chat.

        phone_call_started (:obj:`~pyrogram.types.PhoneCallStarted`, *optional*):
            Service message: phone call started.

        phone_call_ended (:obj:`~pyrogram.types.PhoneCallEnded`, *optional*):
            Service message: phone call ended.

        web_app_data (:obj:`~pyrogram.types.WebAppData`, *optional*):
            Service message: web app data sent to the bot.

        paid_messages_refunded (:obj:`~pyrogram.types.PaidMessagesRefunded`, *optional*):
            Service message: paid messages refunded.

        paid_messages_price_changed (:obj:`~pyrogram.types.PaidMessagesPriceChanged`, *optional*):
            Service message: paid messages price.

        direct_message_price_changed (:obj:`~pyrogram.types.DirectMessagePriceChanged`, *optional*):
            Service message: direct messages price.

        checklist_tasks_done (:obj:`~pyrogram.types.ChecklistTasksDone`, *optional*):
            Service message: checklist tasks done.

        checklist_tasks_added (:obj:`~pyrogram.types.ChecklistTasksAdded`, *optional*):
            Service message: checklist tasks added.

        community_chat_added (:obj:`~pyrogram.types.CommunityChatAdded`, *optional*):
            Service message: chat added to a Community.

        community_chat_removed (:obj:`~pyrogram.types.CommunityChatRemoved`, *optional*):
            Service message: chat removed from a Community.

        premium_gift_code (:obj:`~pyrogram.types.PremiumGiftCode`, *optional*):
            Service message: premium gift code information.

        gifted_premium (:obj:`~pyrogram.types.GiftedPremium`, *optional*):
            Service message: gifted premium information.

        gifted_stars (:obj:`~pyrogram.types.GiftedStars`, *optional*):
            Service message: gifted stars information.

        gifted_ton (:obj:`~pyrogram.types.GiftedTon`, *optional*):
            Service message: gifted ton information.

        gift (:obj:`~pyrogram.types.Gift`, *optional*):
            Service message: star gift information.

        is_prepaid_upgrade (``bool``, *optional*):
            True, if the messages is about prepaid upgrade of the gift by another user.

        is_from_auction (``bool``, *optional*):
            True, if the message is a notification about a gift won on an auction.

        suggest_profile_photo (:obj:`~pyrogram.types.Photo`, *optional*):
            Service message: suggested profile photo.

        suggest_birthday (:obj:`~pyrogram.types.Birthday`, *optional*):
            Service message: suggested birthday.

        users_shared (:obj:`~pyrogram.types.UsersShared`, *optional*):
            Service message: users shared information.

        chat_shared (:obj:`~pyrogram.types.ChatShared`, *optional*):
            Service message: chat shared information.

        successful_payment (:obj:`~pyrogram.types.SuccessfulPayment`, *optional*):
            Service message: successful payment.

        refunded_payment (:obj:`~pyrogram.types.RefundedPayment`, *optional*):
            Service message: refunded payment.

        suggested_post_approval_failed (:obj:`~pyrogram.types.SuggestedPostApprovalFailed`, *optional*):
            Service message: suggested post approval failed.

        suggested_post_approved (:obj:`~pyrogram.types.SuggestedPostApproved`, *optional*):
            Service message: suggested post approved.

        suggested_post_declined (:obj:`~pyrogram.types.SuggestedPostDeclined`, *optional*):
            Service message: suggested post declined.

        suggested_post_paid (:obj:`~pyrogram.types.SuggestedPostPaid`, *optional*):
            Service message: suggested post paid.

        suggested_post_refunded (:obj:`~pyrogram.types.SuggestedPostRefunded`, *optional*):
            Service message: suggested post refunded.

        giveaway_created (``bool``, *optional*):
            Service message: giveaway launched.

        giveaway_winners (:obj:`~pyrogram.types.GiveawayWinners`, *optional*):
            A giveaway with public winners was completed.

        giveaway_completed (:obj:`~pyrogram.types.GiveawayCompleted`, *optional*):
            Service message: a giveaway without public winners was completed.

        managed_bot_created (:obj:`~pyrogram.types.ManagedBotCreated`, *optional*):
            Service message: user created a bot that will be managed by the current bot.

        poll_option_added (:obj:`~pyrogram.types.PollOptionAdded`, *optional*):
            Service message: answer option was added to a poll.

        poll_option_deleted (:obj:`~pyrogram.types.PollOptionDeleted`, *optional*):
            Service message: answer option was deleted from a poll.

        chat_set_theme (:obj:`~pyrogram.types.ChatTheme`, *optional*):
            Service message: The chat theme was changed.

        chat_set_background (:obj:`~pyrogram.types.ChatBackground`, *optional*):
            Service message: The chat background was changed.

        set_message_auto_delete_time (``int``, *optional*):
            Service message: The auto-delete or self-destruct timer for messages in the chat has been changed.

        chat_boost (``int``, *optional*):
            Service message: The chat was boosted by the sender of the message.
            Number of times the chat was boosted.

        write_access_allowed (:obj:`~pyrogram.types.WriteAccessAllowed`, *optional*):
            Service message: the user allowed the bot to write messages after adding it to the attachment or side menu, launching a Web App from a link, or accepting an explicit request from a Web App sent by the method `requestWriteAccess <https://core.telegram.org/bots/webapps#initializing-mini-apps>`__

        connected_website (``str``, *optional*):
            The domain name of the website on which the user has logged in. `More about Telegram Login <https://core.telegram.org/widgets/login>`__

        contact_registered (:obj:`~pyrogram.types.ContactRegistered`, *optional*):
            Service message: Contact registered in Telegram.

        proximity_alert_triggered (:obj:`~pyrogram.types.ProximityAlertTriggered`, *optional*):
            Service message: A user in the chat came within proximity alert range.

        giveaway_prize_stars (:obj:`~pyrogram.types.GiveawayPrizeStars`, *optional*):
            Service message: Stars were received by the current user from a giveaway.

        screenshot_taken (:obj:`~pyrogram.types.ScreenshotTaken`, *optional*):
            Service message: screenshot of a message in the chat has been taken.

        upgraded_gift_purchase_offer (:obj:`~pyrogram.types.UpgradedGiftPurchaseOffer`, *optional*):
            Service message: An offer to purchase an upgraded gift was sent or received.

        upgraded_gift_purchase_offer_rejected (:obj:`~pyrogram.types.UpgradedGiftPurchaseOfferRejected`, *optional*):
            Service message: An offer to purchase a gift was rejected or expired.

        chat_has_protected_content_toggled (:obj:`~pyrogram.types.ChatHasProtectedContentToggled`, *optional*):
            Service message: An ``has_protected_content`` setting was changed or request to change it was rejected in a chat.

        chat_has_protected_content_disable_requested (:obj:`~pyrogram.types.Chat`, *optional*):
            Service message: An process requested to disable ``has_protected_content`` in a chat.

        business_connection_id (``str``, *optional*):
            Unique identifier of the business connection from which the message was received.
            If non-empty, the message belongs to a chat of the corresponding business account that is independent from any potential bot chat which might share the same identifier.
            This update may at times be triggered by unavailable changes to message fields that are either unavailable or not actively used by the current bot.

        reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
            Additional interface options. An object for an inline keyboard, custom reply keyboard,
            instructions to remove reply keyboard or to force a reply from the user.

        reactions (:obj:`~pyrogram.types.MessageReactions`):
            Reactions of this message.

        send_paid_messages_stars (``int``, *optional*):
            The number of Telegram Stars the sender paid to send the message.

        unread_media (``bool``, *optional*):
            True, if there are unread media attachments in this message.

        silent (``bool``, *optional*):
            True, if the message sent without notification.

        legacy (``bool``, *optional*):
            True, if the message is a legacy message.
            This means that the message is based on the old layer and should be refetched with the new layer.

        pinned (``bool``, *optional*):
            True, if the message is pinned.

        restriction_reason (List of :obj:`~pyrogram.types.RestrictionReason`, *optional*):
            Contains a list of human-readable description of the reason why access to this message must be restricted.

        fact_check (:obj:`~pyrogram.types.FactCheck`, *optional*):
            Information about fact-check added to the message.

        suggested_post_info (:obj:`~pyrogram.types.SuggestedPostInfo`, *optional*):
            Information about the suggested post.

        channel_post (``bool``, *optional*):
            True, if the message is a channel post.

        repeat_period (``int``, *optional*):
            Period after which the message will be sent again in seconds.

        summary_language_code (``str``, *optional*):
            IETF language tag of the message language on which it can be summarized.
            None if summary isn't available for the message.

        guest_bot_caller_user (:obj:`~pyrogram.types.User`, *optional*):
            For a message sent by a guest bot, this is the user whose original message triggered the bot's response.

        guest_bot_caller_chat (:obj:`~pyrogram.types.Chat`, *optional*):
            For a message sent by a guest bot, this is the chat whose original message triggered the bot's response.

        raw (:obj:`~pyrogram.raw.types.Message`, *optional*):
            The raw message object, as received from the Telegram API.

        link (``str``, *property*):
            Generate a link to this message, only for groups and channels.

        content (``str``, *property*):
            The text or caption content of the message.
    """

    # TODO: replace media params to MessageContent class
    def __init__(
        self,
        *,
        client: pyrogram.Client | None = None,
        id: int,
        from_user: types.User | None = None,
        sender_chat: types.Chat | None = None,
        sender_boost_count: int | None = None,
        sender_business_bot: types.User | None = None,
        sender_tag: str | None = None,
        receiver_user: types.User | None = None,
        ephemeral_message_id: int | None = None,
        date: datetime | None = None,
        guest_query_id: str | None = None,
        chat: types.Chat | None = None,
        topic_message: bool | None = None,
        automatic_forward: bool | None = None,
        from_offline: bool | None = None,
        show_caption_above_media: bool | None = None,
        external_reply: types.ExternalReplyInfo | None = None,
        quote: types.TextQuote | None = None,
        topic: types.ForumTopic | None = None,
        forward_origin: types.MessageOrigin | None = None,
        message_thread_id: int | None = None,
        direct_messages_topic_id: int | None = None,
        effect_id: int | None = None,
        rich_message: types.RichMessage | None = None,
        reply_to_message_id: int | None = None,
        reply_to_story_id: int | None = None,
        reply_to_story_user_id: int | None = None,
        reply_to_top_message_id: int | None = None,
        reply_to_poll_option_id: str | None = None,
        reply_to_message: Message | None = None,
        reply_to_story: types.Story | None = None,
        reply_to_checklist_task_id: int | None = None,
        mentioned: bool | None = None,
        empty: bool | None = None,
        service: enums.MessageServiceType | None = None,
        scheduled: bool | None = None,
        from_scheduled: bool | None = None,
        media: enums.MessageMediaType | None = None,
        paid_media: types.PaidMediaInfo | None = None,
        checklist: types.Checklist | None = None,
        edit_date: datetime | None = None,
        edit_hidden: bool | None = None,
        media_group_id: int | None = None,
        author_signature: str | None = None,
        is_paid_post: bool | None = None,
        has_protected_content: bool | None = None,
        has_media_spoiler: bool | None = None,
        text: Str | None = None,
        entities: list[types.MessageEntity] | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        audio: types.Audio | None = None,
        document: types.Document | None = None,
        photo: types.Photo | None = None,
        live_photo: types.LivePhoto | None = None,
        sticker: types.Sticker | None = None,
        animation: types.Animation | None = None,
        game: types.Game | None = None,
        giveaway: types.Giveaway | None = None,
        giveaway_winners: types.GiveawayWinners | None = None,
        giveaway_completed: types.GiveawayCompleted | None = None,
        managed_bot_created: types.ManagedBotCreated | None = None,
        poll_option_added: types.PollOptionAdded | None = None,
        poll_option_deleted: types.PollOptionDeleted | None = None,
        invoice: types.Invoice | None = None,
        story: types.Story | None = None,
        video: types.Video | None = None,
        video_processing_pending: bool | None = None,
        voice: types.Voice | None = None,
        video_note: types.VideoNote | None = None,
        caption: Str | None = None,
        contact: types.Contact | None = None,
        location: types.Location | None = None,
        venue: types.Venue | None = None,
        web_page: types.WebPage | None = None,
        link_preview_options: types.LinkPreviewOptions | None = None,
        poll: types.Poll | None = None,
        dice: types.Dice | None = None,
        new_chat_members: list[types.User] | None = None,
        left_chat_member: types.User | None = None,
        chat_owner_left: types.ChatOwnerLeft | None = None,
        chat_owner_changed: types.ChatOwnerChanged | None = None,
        chat_join_type: enums.ChatJoinType | None = None,
        new_chat_title: str | None = None,
        new_chat_photo: types.Photo | None = None,
        delete_chat_photo: bool | None = None,
        group_chat_created: bool | None = None,
        supergroup_chat_created: bool | None = None,
        channel_chat_created: bool | None = None,
        migrate_to_chat_id: int | None = None,
        migrate_from_chat_id: int | None = None,
        pinned_message: Message | None = None,
        game_high_score: types.GameHighScore | None = None,
        views: int | None = None,
        forwards: int | None = None,
        via_bot: types.User | None = None,
        outgoing: bool | None = None,
        matches: list[Match] | None = None,
        command: list[str] | None = None,
        forum_topic_created: types.ForumTopicCreated | None = None,
        forum_topic_closed: types.ForumTopicClosed | None = None,
        forum_topic_reopened: types.ForumTopicReopened | None = None,
        forum_topic_edited: types.ForumTopicEdited | None = None,
        general_forum_topic_hidden: types.GeneralForumTopicHidden | None = None,
        general_forum_topic_unhidden: types.GeneralForumTopicUnhidden | None = None,
        video_chat_scheduled: types.VideoChatScheduled | None = None,
        history_cleared: types.HistoryCleared | None = None,
        video_chat_started: types.VideoChatStarted | None = None,
        video_chat_ended: types.VideoChatEnded | None = None,
        video_chat_members_invited: types.VideoChatMembersInvited | None = None,
        phone_call_started: types.PhoneCallStarted | None = None,
        phone_call_ended: types.PhoneCallEnded | None = None,
        web_app_data: types.WebAppData | None = None,
        paid_messages_refunded: types.PaidMessagesRefunded | None = None,
        paid_messages_price_changed: types.PaidMessagesPriceChanged | None = None,
        direct_message_price_changed: types.DirectMessagePriceChanged | None = None,
        checklist_tasks_done: list[types.ChecklistTasksDone] | None = None,
        checklist_tasks_added: list[types.ChecklistTasksAdded] | None = None,
        community_chat_added: list[types.CommunityChatAdded] | None = None,
        community_chat_removed: list[types.CommunityChatRemoved] | None = None,
        premium_gift_code: types.PremiumGiftCode | None = None,
        gifted_premium: types.GiftedPremium | None = None,
        gifted_stars: types.GiftedStars | None = None,
        gifted_ton: types.GiftedTon | None = None,
        gift: types.Gift | None = None,
        is_prepaid_upgrade: bool | None = None,
        is_from_auction: bool | None = None,
        suggest_profile_photo: types.Photo | None = None,
        suggest_birthday: types.Birthday | None = None,
        users_shared: types.UsersShared | None = None,
        chat_shared: types.ChatShared | None = None,
        successful_payment: types.SuccessfulPayment | None = None,
        refunded_payment: types.RefundedPayment | None = None,
        suggested_post_approval_failed: types.SuggestedPostApprovalFailed | None = None,
        suggested_post_approved: types.SuggestedPostApproved | None = None,
        suggested_post_declined: types.SuggestedPostDeclined | None = None,
        suggested_post_paid: types.SuggestedPostPaid | None = None,
        suggested_post_refunded: types.SuggestedPostRefunded | None = None,
        giveaway_created: bool | None = None,
        chat_set_theme: types.ChatTheme | None = None,
        chat_set_background: types.ChatBackground | None = None,
        set_message_auto_delete_time: int | None = None,
        chat_boost: int | None = None,
        write_access_allowed: types.WriteAccessAllowed | None = None,
        connected_website: str | None = None,
        contact_registered: types.ContactRegistered | None = None,
        proximity_alert_triggered: types.ProximityAlertTriggered | None = None,
        giveaway_prize_stars: types.GiveawayPrizeStars | None = None,
        screenshot_taken: types.ScreenshotTaken | None = None,
        upgraded_gift_purchase_offer: types.UpgradedGiftPurchaseOffer | None = None,
        upgraded_gift_purchase_offer_rejected: types.UpgradedGiftPurchaseOfferRejected
        | None = None,
        chat_has_protected_content_toggled: types.ChatHasProtectedContentToggled | None = None,
        chat_has_protected_content_disable_requested: types.ChatHasProtectedContentDisableRequested
        | None = None,
        business_connection_id: str | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply
        | None = None,
        reactions: types.MessageReactions | None = None,
        send_paid_messages_stars: int | None = None,
        unread_media: bool | None = None,
        silent: bool | None = None,
        legacy: bool | None = None,
        pinned: bool | None = None,
        restriction_reason: list[types.RestrictionReason] | None = None,
        fact_check: types.FactCheck | None = None,
        suggested_post_info: types.SuggestedPostInfo | None = None,
        channel_post: bool | None = None,
        repeat_period: int | None = None,
        summary_language_code: str | None = None,
        guest_bot_caller_user: types.User | None = None,
        guest_bot_caller_chat: types.Chat | None = None,
        raw: raw.types.Message | None = None,
    ):
        super().__init__(client)

        self.id = id
        self.from_user = from_user
        self.sender_chat = sender_chat
        self.sender_boost_count = sender_boost_count
        self.sender_business_bot = sender_business_bot
        self.sender_tag = sender_tag
        self.receiver_user = receiver_user
        self.ephemeral_message_id = ephemeral_message_id
        self.date = date
        self.guest_query_id = guest_query_id
        self.chat = chat
        self.topic_message = topic_message
        self.automatic_forward = automatic_forward
        self.from_offline = from_offline
        self.show_caption_above_media = show_caption_above_media
        self.external_reply = external_reply
        self.quote = quote
        self.topic = topic
        self.forward_origin = forward_origin
        self.message_thread_id = message_thread_id
        self.direct_messages_topic_id = direct_messages_topic_id
        self.effect_id = effect_id
        self.rich_message = rich_message
        self.reply_to_message_id = reply_to_message_id
        self.reply_to_story_id = reply_to_story_id
        self.reply_to_story_user_id = reply_to_story_user_id
        self.reply_to_top_message_id = reply_to_top_message_id
        self.reply_to_poll_option_id = reply_to_poll_option_id
        self.reply_to_message = reply_to_message
        self.reply_to_story = reply_to_story
        self.reply_to_checklist_task_id = reply_to_checklist_task_id
        self.mentioned = mentioned
        self.empty = empty
        self.service = service
        self.scheduled = scheduled
        self.from_scheduled = from_scheduled
        self.media = media
        self.paid_media = paid_media
        self.checklist = checklist
        self.edit_date = edit_date
        self.edit_hidden = edit_hidden
        self.media_group_id = media_group_id
        self.author_signature = author_signature
        self.is_paid_post = is_paid_post
        self.has_protected_content = has_protected_content
        self.has_media_spoiler = has_media_spoiler
        self.text = text
        self.entities = entities
        self.caption_entities = caption_entities
        self.audio = audio
        self.document = document
        self.photo = photo
        self.live_photo = live_photo
        self.sticker = sticker
        self.animation = animation
        self.game = game
        self.giveaway = giveaway
        self.giveaway_winners = giveaway_winners
        self.giveaway_completed = giveaway_completed
        self.managed_bot_created = managed_bot_created
        self.poll_option_added = poll_option_added
        self.poll_option_deleted = poll_option_deleted
        self.invoice = invoice
        self.story = story
        self.video = video
        self.video_processing_pending = video_processing_pending
        self.voice = voice
        self.video_note = video_note
        self.caption = caption
        self.contact = contact
        self.location = location
        self.venue = venue
        self.web_page = web_page
        self.link_preview_options = link_preview_options
        self.poll = poll
        self.dice = dice
        self.new_chat_members = new_chat_members
        self.left_chat_member = left_chat_member
        self.chat_owner_left = chat_owner_left
        self.chat_owner_changed = chat_owner_changed
        self.chat_join_type = chat_join_type
        self.new_chat_title = new_chat_title
        self.new_chat_photo = new_chat_photo
        self.delete_chat_photo = delete_chat_photo
        self.group_chat_created = group_chat_created
        self.supergroup_chat_created = supergroup_chat_created
        self.channel_chat_created = channel_chat_created
        self.migrate_to_chat_id = migrate_to_chat_id
        self.migrate_from_chat_id = migrate_from_chat_id
        self.pinned_message = pinned_message
        self.game_high_score = game_high_score
        self.views = views
        self.forwards = forwards
        self.via_bot = via_bot
        self.outgoing = outgoing
        self.matches = matches
        self.command = command
        self.giveaway_prize_stars = giveaway_prize_stars
        self.screenshot_taken = screenshot_taken
        self.upgraded_gift_purchase_offer = upgraded_gift_purchase_offer
        self.upgraded_gift_purchase_offer_rejected = upgraded_gift_purchase_offer_rejected
        self.chat_has_protected_content_toggled = chat_has_protected_content_toggled
        self.chat_has_protected_content_disable_requested = (
            chat_has_protected_content_disable_requested
        )
        self.business_connection_id = business_connection_id
        self.reply_markup = reply_markup
        self.forum_topic_created = forum_topic_created
        self.forum_topic_closed = forum_topic_closed
        self.forum_topic_reopened = forum_topic_reopened
        self.forum_topic_edited = forum_topic_edited
        self.general_forum_topic_hidden = general_forum_topic_hidden
        self.general_forum_topic_unhidden = general_forum_topic_unhidden
        self.video_chat_scheduled = video_chat_scheduled
        self.history_cleared = history_cleared
        self.video_chat_started = video_chat_started
        self.video_chat_ended = video_chat_ended
        self.video_chat_members_invited = video_chat_members_invited
        self.phone_call_started = phone_call_started
        self.phone_call_ended = phone_call_ended
        self.web_app_data = web_app_data
        self.paid_messages_refunded = paid_messages_refunded
        self.paid_messages_price_changed = paid_messages_price_changed
        self.direct_message_price_changed = direct_message_price_changed
        self.checklist_tasks_done = checklist_tasks_done
        self.checklist_tasks_added = checklist_tasks_added
        self.community_chat_added = community_chat_added
        self.community_chat_removed = community_chat_removed
        self.premium_gift_code = premium_gift_code
        self.gifted_premium = gifted_premium
        self.gifted_stars = gifted_stars
        self.gifted_ton = gifted_ton
        self.gift = gift
        self.is_prepaid_upgrade = is_prepaid_upgrade
        self.is_from_auction = is_from_auction
        self.suggest_profile_photo = suggest_profile_photo
        self.suggest_birthday = suggest_birthday
        self.users_shared = users_shared
        self.chat_shared = chat_shared
        self.successful_payment = successful_payment
        self.refunded_payment = refunded_payment
        self.suggested_post_approval_failed = suggested_post_approval_failed
        self.suggested_post_approved = suggested_post_approved
        self.suggested_post_declined = suggested_post_declined
        self.suggested_post_paid = suggested_post_paid
        self.suggested_post_refunded = suggested_post_refunded
        self.giveaway_created = giveaway_created
        self.chat_set_theme = chat_set_theme
        self.chat_set_background = chat_set_background
        self.set_message_auto_delete_time = set_message_auto_delete_time
        self.chat_boost = chat_boost
        self.write_access_allowed = write_access_allowed
        self.connected_website = connected_website
        self.contact_registered = contact_registered
        self.proximity_alert_triggered = proximity_alert_triggered
        self.reactions = reactions
        self.send_paid_messages_stars = send_paid_messages_stars
        self.unread_media = unread_media
        self.silent = silent
        self.legacy = legacy
        self.pinned = pinned
        self.restriction_reason = restriction_reason
        self.fact_check = fact_check
        self.suggested_post_info = suggested_post_info
        self.channel_post = channel_post
        self.repeat_period = repeat_period
        self.summary_language_code = summary_language_code
        self.guest_bot_caller_user = guest_bot_caller_user
        self.guest_bot_caller_chat = guest_bot_caller_chat
        self.raw = raw

    @staticmethod
    async def _parse_service(
        client: pyrogram.Client,
        message: raw.types.MessageService,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
        replies: int = 1,
        business_connection_id: str | None = None,
        raw_reply_to_message: raw.base.Message | None = None,
    ) -> Message:
        from_id = utils.get_raw_peer_id(message.from_id)
        peer_id = utils.get_raw_peer_id(message.peer_id)

        if (
            isinstance(message.from_id, raw.types.PeerUser)
            and isinstance(message.peer_id, raw.types.PeerUser)
            and (from_id not in users or peer_id not in users)
        ):
            try:
                r = await client.invoke(
                    raw.functions.users.GetUsers(
                        id=[
                            await client.resolve_peer(from_id),
                            await client.resolve_peer(peer_id),
                        ]
                    )
                )
            except PeerIdInvalid:
                pass
            else:
                users.update({i.id: i for i in r})

        from_user = types.User._parse(client, users.get(from_id or peer_id))
        sender_chat = (
            types.Chat._parse(client, message, users, chats, is_chat=False)
            if not from_user
            else None
        )
        chat = types.Chat._parse(client, message, users, chats, is_chat=True)

        action = message.action

        connected_website = None
        write_access_allowed = None
        chat_boost = None
        supergroup_chat_created = None
        channel_chat_created = None
        migrate_from_chat_id = None
        new_chat_members = None
        chat_join_type = None
        group_chat_created = None
        delete_chat_photo = None
        left_chat_member = None
        chat_owner_left = None
        chat_owner_changed = None
        new_chat_photo = None
        new_chat_title = None
        migrate_to_chat_id = None
        contact_registered = None
        text = None
        proximity_alert_triggered = None
        premium_gift_code = None
        gifted_premium = None
        gifted_stars = None
        gifted_ton = None
        giveaway_created = None
        giveaway_completed = None
        managed_bot_created = None
        video_chat_ended = None
        video_chat_started = None
        video_chat_scheduled = None
        history_cleared = None
        video_chat_members_invited = None
        successful_payment = None
        refunded_payment = None
        suggested_post_approval_failed = None
        suggested_post_declined = None
        suggested_post_approved = None
        suggested_post_paid = None
        suggested_post_refunded = None
        phone_call_ended = None
        phone_call_started = None
        giveaway_prize_stars = None
        users_shared = None
        chat_shared = None
        screenshot_taken = None
        upgraded_gift_purchase_offer = None
        upgraded_gift_purchase_offer_rejected = None
        chat_has_protected_content_toggled = None
        chat_has_protected_content_disable_requested = None
        # passport_data_send = None
        # passport_data_received = None
        chat_set_theme = None
        chat_set_background = None
        set_message_auto_delete_time = None
        gift = None
        is_prepaid_upgrade = None
        is_from_auction = None
        suggest_profile_photo = None
        suggest_birthday = None
        forum_topic_created = None
        forum_topic_edited = None
        general_forum_topic_hidden = None
        forum_topic_closed = None
        general_forum_topic_unhidden = None
        forum_topic_reopened = None
        web_app_data = None
        paid_messages_refunded = None
        paid_messages_price_changed = None
        direct_message_price_changed = None
        checklist_tasks_done = None
        checklist_tasks_added = None
        community_chat_added = None
        community_chat_removed = None

        service_type = enums.MessageServiceType.UNSUPPORTED

        if isinstance(action, raw.types.MessageActionBotAllowed):
            if getattr(action, "domain", None):
                service_type = enums.MessageServiceType.CONNECTED_WEBSITE
                connected_website = action.domain
            else:
                service_type = enums.MessageServiceType.WRITE_ACCESS_ALLOWED
                write_access_allowed = types.WriteAccessAllowed._parse(action)
        elif isinstance(action, raw.types.MessageActionBoostApply):
            service_type = enums.MessageServiceType.CHAT_BOOST
            chat_boost = action.boosts
        elif isinstance(action, raw.types.MessageActionChannelCreate):
            service_type = enums.MessageServiceType.CHANNEL_CHAT_CREATED

            if chat.type == enums.ChatType.SUPERGROUP:
                supergroup_chat_created = True
                service_type = enums.MessageServiceType.SUPERGROUP_CHAT_CREATED
            else:
                channel_chat_created = True
                service_type = enums.MessageServiceType.CHANNEL_CHAT_CREATED
        elif isinstance(action, raw.types.MessageActionChannelMigrateFrom):
            service_type = enums.MessageServiceType.MIGRATE_FROM_CHAT_ID
            migrate_from_chat_id = -action.chat_id
        elif isinstance(action, raw.types.MessageActionChatAddUser):
            service_type = enums.MessageServiceType.NEW_CHAT_MEMBERS
            new_chat_members = [types.User._parse(client, users[i]) for i in action.users]
            chat_join_type = enums.ChatJoinType.BY_ADD
        elif isinstance(action, raw.types.MessageActionChatCreate):
            service_type = enums.MessageServiceType.GROUP_CHAT_CREATED
            group_chat_created = True
        elif isinstance(action, raw.types.MessageActionChatDeletePhoto):
            service_type = enums.MessageServiceType.DELETE_CHAT_PHOTO
            delete_chat_photo = True
        elif isinstance(action, raw.types.MessageActionChatDeleteUser):
            service_type = enums.MessageServiceType.LEFT_CHAT_MEMBER
            left_chat_member = types.User._parse(client, users[action.user_id])
        elif isinstance(action, raw.types.MessageActionNewCreatorPending):
            service_type = enums.MessageServiceType.CHAT_OWNER_LEFT
            chat_owner_left = await types.ChatOwnerLeft._parse(client, action, users)
        elif isinstance(action, raw.types.MessageActionChangeCreator):
            service_type = enums.MessageServiceType.CHAT_OWNER_CHANGED
            chat_owner_changed = await types.ChatOwnerChanged._parse(client, action, users)
        elif isinstance(action, raw.types.MessageActionChatEditPhoto):
            service_type = enums.MessageServiceType.NEW_CHAT_PHOTO
            new_chat_photo = types.Photo._parse(client, action.photo)
        elif isinstance(action, raw.types.MessageActionChatEditTitle):
            service_type = enums.MessageServiceType.NEW_CHAT_TITLE
            new_chat_title = action.title
        elif isinstance(action, raw.types.MessageActionChatJoinedByLink):
            service_type = enums.MessageServiceType.NEW_CHAT_MEMBERS
            new_chat_members = [
                types.User._parse(client, users[utils.get_raw_peer_id(message.from_id)])
            ]
            chat_join_type = enums.ChatJoinType.BY_LINK
        elif isinstance(action, raw.types.MessageActionChatJoinedByRequest):
            service_type = enums.MessageServiceType.NEW_CHAT_MEMBERS
            new_chat_members = [
                types.User._parse(client, users[utils.get_raw_peer_id(message.from_id)])
            ]
            chat_join_type = enums.ChatJoinType.BY_REQUEST
        elif isinstance(action, raw.types.MessageActionChatMigrateTo):
            service_type = enums.MessageServiceType.MIGRATE_TO_CHAT_ID
            migrate_to_chat_id = utils.get_channel_id(action.channel_id)
        elif isinstance(action, raw.types.MessageActionContactSignUp):
            service_type = enums.MessageServiceType.CONTACT_REGISTERED
            contact_registered = types.ContactRegistered()
        elif isinstance(action, raw.types.MessageActionCustomAction):
            service_type = enums.MessageServiceType.CUSTOM_ACTION
            text = action.message
        # TODO: elif isinstance(action, raw.types.MessageActionEmpty):
        elif isinstance(action, raw.types.MessageActionGeoProximityReached):
            service_type = enums.MessageServiceType.PROXIMITY_ALERT_TRIGGERED
            proximity_alert_triggered = await types.ProximityAlertTriggered._parse(
                client, action, users, chats
            )
        elif isinstance(action, raw.types.MessageActionGiftCode):
            service_type = enums.MessageServiceType.PREMIUM_GIFT_CODE
            premium_gift_code = await types.PremiumGiftCode._parse(client, action, users, chats)
        elif isinstance(action, raw.types.MessageActionGiftPremium):
            service_type = enums.MessageServiceType.GIFTED_PREMIUM
            gifted_premium = await types.GiftedPremium._parse(
                client,
                action,
                gifter=users.get(from_id),
                receiver=users.get(peer_id or from_id),
                users=users,
            )
        elif isinstance(action, raw.types.MessageActionGiftStars):
            service_type = enums.MessageServiceType.GIFTED_STARS
            gifted_stars = await types.GiftedStars._parse(
                client, action, gifter=users.get(from_id), receiver=users.get(peer_id or from_id)
            )
        elif isinstance(action, raw.types.MessageActionGiftTon):
            service_type = enums.MessageServiceType.GIFTED_TON
            gifted_ton = await types.GiftedTon._parse(
                client, action, gifter=users.get(from_id), receiver=users.get(peer_id or from_id)
            )
        elif isinstance(action, raw.types.MessageActionGiveawayLaunch):
            service_type = enums.MessageServiceType.GIVEAWAY_CREATED
            giveaway_created = types.GiveawayCreated._parse(client, action)
        elif isinstance(action, raw.types.MessageActionGiveawayResults):
            service_type = enums.MessageServiceType.GIVEAWAY_COMPLETED
            giveaway_completed = await types.GiveawayCompleted._parse(
                client,
                action,
                types.Chat._parse(client, message, users, chats, is_chat=True),
                getattr(getattr(message, "reply_to", None), "reply_to_msg_id", None),
            )
        elif isinstance(action, raw.types.MessageActionManagedBotCreated):
            service_type = enums.MessageServiceType.MANAGED_BOT_CREATED
            managed_bot_created = await types.ManagedBotCreated._parse(client, action, users)
        elif isinstance(action, raw.types.MessageActionGroupCall):
            if action.duration:
                service_type = enums.MessageServiceType.VIDEO_CHAT_ENDED
                video_chat_ended = types.VideoChatEnded._parse(action)
            else:
                service_type = enums.MessageServiceType.VIDEO_CHAT_STARTED
                video_chat_started = types.VideoChatStarted()
        elif isinstance(action, raw.types.MessageActionGroupCallScheduled):
            service_type = enums.MessageServiceType.VIDEO_CHAT_SCHEDULED
            video_chat_scheduled = types.VideoChatScheduled._parse(action)
        if isinstance(action, raw.types.MessageActionHistoryClear):
            service_type = enums.MessageServiceType.HISTORY_CLEARED
            history_cleared = types.HistoryCleared()
        elif isinstance(action, raw.types.MessageActionInviteToGroupCall):
            service_type = enums.MessageServiceType.VIDEO_CHAT_MEMBERS_INVITED
            video_chat_members_invited = types.VideoChatMembersInvited._parse(
                client, action, users
            )
        elif isinstance(
            action, (raw.types.MessageActionPaymentSent, raw.types.MessageActionPaymentSentMe)
        ):
            service_type = enums.MessageServiceType.SUCCESSFUL_PAYMENT
            successful_payment = types.SuccessfulPayment._parse(action)
        elif isinstance(action, raw.types.MessageActionPaymentRefunded):
            service_type = enums.MessageServiceType.REFUNDED_PAYMENT
            refunded_payment = types.RefundedPayment._parse(action)
        elif isinstance(action, raw.types.MessageActionSuggestedPostApproval):
            if action.balance_too_low:
                service_type = enums.MessageServiceType.SUGGESTED_POST_APPROVAL_FAILED
                suggested_post_approval_failed = await types.SuggestedPostApprovalFailed._parse(
                    client, message
                )
            elif action.rejected:
                service_type = enums.MessageServiceType.SUGGESTED_POST_DECLINED
                suggested_post_declined = await types.SuggestedPostDeclined._parse(client, message)
            else:
                service_type = enums.MessageServiceType.SUGGESTED_POST_APPROVED
                suggested_post_approved = await types.SuggestedPostApproved._parse(client, message)
        elif isinstance(action, raw.types.MessageActionSuggestedPostSuccess):
            service_type = enums.MessageServiceType.SUGGESTED_POST_PAID
            suggested_post_paid = await types.SuggestedPostPaid._parse(client, message)
        elif isinstance(action, raw.types.MessageActionSuggestedPostRefund):
            service_type = enums.MessageServiceType.SUGGESTED_POST_REFUNDED
            suggested_post_refunded = await types.SuggestedPostRefunded._parse(client, message)
        elif isinstance(action, raw.types.MessageActionPhoneCall):
            if action.reason:
                service_type = enums.MessageServiceType.PHONE_CALL_ENDED
                phone_call_ended = types.PhoneCallEnded._parse(action)
            else:
                service_type = enums.MessageServiceType.PHONE_CALL_STARTED
                phone_call_started = types.PhoneCallStarted._parse(action)
        elif isinstance(action, raw.types.MessageActionPrizeStars):
            service_type = enums.MessageServiceType.GIVEAWAY_PRIZE_STARS
            giveaway_prize_stars = await types.GiveawayPrizeStars._parse(client, action, chats)
        elif isinstance(
            action,
            (raw.types.MessageActionRequestedPeer, raw.types.MessageActionRequestedPeerSentMe),
        ):
            requested_chat = await types.ChatShared._parse(client, action, chats)

            if requested_chat is None:
                service_type = enums.MessageServiceType.USERS_SHARED
                users_shared = await types.UsersShared._parse(client, action, users)
            else:
                service_type = enums.MessageServiceType.CHAT_SHARED
                chat_shared = requested_chat
        elif isinstance(action, raw.types.MessageActionScreenshotTaken):
            service_type = enums.MessageServiceType.SCREENSHOT_TAKEN
            screenshot_taken = types.ScreenshotTaken()
        elif isinstance(action, raw.types.MessageActionStarGiftPurchaseOffer):
            service_type = enums.MessageServiceType.UPGRADED_GIFT_PURCHASE_OFFER
            upgraded_gift_purchase_offer = await types.UpgradedGiftPurchaseOffer._parse(
                client, action, users, chats
            )
        elif isinstance(action, raw.types.MessageActionStarGiftPurchaseOfferDeclined):
            service_type = enums.MessageServiceType.UPGRADED_GIFT_PURCHASE_OFFER_REJECTED
            upgraded_gift_purchase_offer_rejected = (
                await types.UpgradedGiftPurchaseOfferRejected._parse(
                    client,
                    action,
                    getattr(message.reply_to, "reply_to_msg_id", None),
                    users,
                    chats,
                )
            )
        elif isinstance(action, raw.types.MessageActionNoForwardsToggle):
            service_type = enums.MessageServiceType.CHAT_HAS_PROTECTED_CONTENT_TOGGLED
            chat_has_protected_content_toggled = types.ChatHasProtectedContentToggled._parse(
                getattr(message.reply_to, "reply_to_msg_id", None), action
            )
        elif isinstance(action, raw.types.MessageActionNoForwardsRequest):
            service_type = enums.MessageServiceType.CHAT_HAS_PROTECTED_CONTENT_DISABLE_REQUESTED
            chat_has_protected_content_disable_requested = (
                types.ChatHasProtectedContentDisableRequested._parse(action)
            )
        # TODO: elif isinstance(action, raw.types.MessageActionSecureValuesSent):
        # service_type = enums.MessageServiceType.PASSPORT_DATA_SEND
        # passport_data_send = ...
        # TODO: elif isinstance(action, raw.types.MessageActionSecureValuesSentMe):
        # service_type = enums.MessageServiceType.PASSPORT_DATA_RECEIVED
        # passport_data_received = ...
        elif isinstance(action, raw.types.MessageActionSetChatTheme):
            service_type = enums.MessageServiceType.CHAT_SET_THEME
            chat_set_theme = await types.ChatTheme._parse(client, action.theme)
        elif isinstance(action, raw.types.MessageActionSetChatWallPaper):
            service_type = enums.MessageServiceType.CHAT_SET_BACKGROUND
            chat_set_background = types.ChatBackground._parse(
                client, action.wallpaper, action.same, action.for_both
            )
        elif isinstance(action, raw.types.MessageActionSetMessagesTTL):
            service_type = enums.MessageServiceType.SET_MESSAGE_AUTO_DELETE_TIME
            set_message_auto_delete_time = action.period
        elif isinstance(
            action, (raw.types.MessageActionStarGift, raw.types.MessageActionStarGiftUnique)
        ):
            service_type = enums.MessageServiceType.GIFT
            is_prepaid_upgrade = action.prepaid_upgrade
            is_from_auction = getattr(action, "auction_acquired", None)
            gift = await types.Gift._parse(client, action, users=users, chats=chats)
        elif isinstance(action, raw.types.MessageActionSuggestProfilePhoto):
            service_type = enums.MessageServiceType.SUGGEST_PROFILE_PHOTO
            suggest_profile_photo = types.Photo._parse(client, action.photo)
        elif isinstance(action, raw.types.MessageActionSuggestBirthday):
            service_type = enums.MessageServiceType.SUGGEST_BIRTHDAY
            suggest_birthday = types.Birthday._parse(action.birthday)
        elif isinstance(action, raw.types.MessageActionTopicCreate):
            service_type = enums.MessageServiceType.FORUM_TOPIC_CREATED
            forum_topic_created = types.ForumTopicCreated._parse(message)
        elif isinstance(action, raw.types.MessageActionTopicEdit):
            if action.hidden is True:
                service_type = enums.MessageServiceType.GENERAL_FORUM_TOPIC_HIDDEN
                general_forum_topic_hidden = types.GeneralForumTopicHidden()
            elif action.hidden is False:
                service_type = enums.MessageServiceType.GENERAL_FORUM_TOPIC_UNHIDDEN
                general_forum_topic_unhidden = types.GeneralForumTopicUnhidden()
            elif action.closed is True:
                service_type = enums.MessageServiceType.FORUM_TOPIC_CLOSED
                forum_topic_closed = types.ForumTopicClosed()
            elif action.closed is False:
                service_type = enums.MessageServiceType.FORUM_TOPIC_REOPENED
                forum_topic_reopened = types.ForumTopicReopened()
            else:
                service_type = enums.MessageServiceType.FORUM_TOPIC_EDITED
                forum_topic_edited = types.ForumTopicEdited._parse(action)
        elif isinstance(
            action,
            (raw.types.MessageActionWebViewDataSent, raw.types.MessageActionWebViewDataSentMe),
        ):
            service_type = enums.MessageServiceType.WEB_APP_DATA
            web_app_data = types.WebAppData._parse(action)
        elif isinstance(action, raw.types.MessageActionPaidMessagesRefunded):
            service_type = enums.MessageServiceType.PAID_MESSAGES_REFUNDED
            paid_messages_refunded = types.PaidMessagesRefunded._parse(action)
        elif isinstance(action, raw.types.MessageActionPaidMessagesPrice):
            if chat.type == enums.ChatType.DIRECT:
                service_type = enums.MessageServiceType.DIRECT_MESSAGE_PRICE_CHANGED
                direct_message_price_changed = types.DirectMessagePriceChanged._parse(action)
            else:
                service_type = enums.MessageServiceType.PAID_MESSAGES_PRICE_CHANGED
                paid_messages_price_changed = types.PaidMessagesPriceChanged._parse(action)
        elif isinstance(action, raw.types.MessageActionTodoCompletions):
            service_type = enums.MessageServiceType.CHECKLIST_TASKS_DONE
            checklist_tasks_done = types.ChecklistTasksDone._parse(message)
        elif isinstance(action, raw.types.MessageActionTodoAppendTasks):
            service_type = enums.MessageServiceType.CHECKLIST_TASKS_ADDED
            checklist_tasks_added = await types.ChecklistTasksAdded._parse(
                client, message, users, chats
            )
        elif isinstance(action, raw.types.MessageActionChangeCommunity):
            if action.community_id:
                service_type = enums.MessageServiceType.COMMUNITY_CHAT_ADDED
                community_chat_added = await types.CommunityChatAdded._parse(client, action, chats)
            else:
                service_type = enums.MessageServiceType.COMMUNITY_CHAT_REMOVED
                community_chat_removed = types.CommunityChatRemoved()

        parsed_message = Message(
            id=message.id,
            date=utils.timestamp_to_datetime(message.date),
            chat=chat,
            from_user=from_user,
            sender_chat=sender_chat,
            service=service_type,
            connected_website=connected_website,
            write_access_allowed=write_access_allowed,
            chat_boost=chat_boost,
            supergroup_chat_created=supergroup_chat_created,
            channel_chat_created=channel_chat_created,
            migrate_from_chat_id=migrate_from_chat_id,
            new_chat_members=new_chat_members,
            chat_join_type=chat_join_type,
            group_chat_created=group_chat_created,
            delete_chat_photo=delete_chat_photo,
            left_chat_member=left_chat_member,
            chat_owner_left=chat_owner_left,
            chat_owner_changed=chat_owner_changed,
            new_chat_photo=new_chat_photo,
            new_chat_title=new_chat_title,
            migrate_to_chat_id=migrate_to_chat_id,
            contact_registered=contact_registered,
            text=text,
            proximity_alert_triggered=proximity_alert_triggered,
            premium_gift_code=premium_gift_code,
            gifted_premium=gifted_premium,
            gifted_stars=gifted_stars,
            gifted_ton=gifted_ton,
            giveaway_created=giveaway_created,
            giveaway_completed=giveaway_completed,
            managed_bot_created=managed_bot_created,
            video_chat_ended=video_chat_ended,
            video_chat_started=video_chat_started,
            video_chat_scheduled=video_chat_scheduled,
            history_cleared=history_cleared,
            video_chat_members_invited=video_chat_members_invited,
            successful_payment=successful_payment,
            refunded_payment=refunded_payment,
            suggested_post_approval_failed=suggested_post_approval_failed,
            suggested_post_declined=suggested_post_declined,
            suggested_post_approved=suggested_post_approved,
            suggested_post_paid=suggested_post_paid,
            suggested_post_refunded=suggested_post_refunded,
            suggest_birthday=suggest_birthday,
            phone_call_ended=phone_call_ended,
            phone_call_started=phone_call_started,
            giveaway_prize_stars=giveaway_prize_stars,
            users_shared=users_shared,
            chat_shared=chat_shared,
            screenshot_taken=screenshot_taken,
            upgraded_gift_purchase_offer=upgraded_gift_purchase_offer,
            upgraded_gift_purchase_offer_rejected=upgraded_gift_purchase_offer_rejected,
            chat_has_protected_content_toggled=chat_has_protected_content_toggled,
            chat_has_protected_content_disable_requested=chat_has_protected_content_disable_requested,
            chat_set_theme=chat_set_theme,
            chat_set_background=chat_set_background,
            set_message_auto_delete_time=set_message_auto_delete_time,
            gift=gift,
            is_prepaid_upgrade=is_prepaid_upgrade,
            is_from_auction=is_from_auction,
            suggest_profile_photo=suggest_profile_photo,
            forum_topic_created=forum_topic_created,
            forum_topic_edited=forum_topic_edited,
            general_forum_topic_hidden=general_forum_topic_hidden,
            forum_topic_closed=forum_topic_closed,
            general_forum_topic_unhidden=general_forum_topic_unhidden,
            forum_topic_reopened=forum_topic_reopened,
            web_app_data=web_app_data,
            paid_messages_refunded=paid_messages_refunded,
            paid_messages_price_changed=paid_messages_price_changed,
            direct_message_price_changed=direct_message_price_changed,
            checklist_tasks_done=checklist_tasks_done,
            checklist_tasks_added=checklist_tasks_added,
            community_chat_added=community_chat_added,
            community_chat_removed=community_chat_removed,
            reactions=await types.MessageReactions._parse(client, message.reactions, users, chats),
            business_connection_id=business_connection_id,
            raw=message,
            client=client,
        )

        if message.reply_to:
            parsed_message = await types.Message.__parse_reply(
                client=client,
                parsed_message=parsed_message,
                message=message,
                users=users,
                chats=chats,
                replies=replies,
                business_connection_id=business_connection_id,
                raw_reply_to_message=raw_reply_to_message,
            )

        if isinstance(action, raw.types.MessageActionGameScore):
            parsed_message.service = enums.MessageServiceType.GAME_HIGH_SCORE
            parsed_message.game_high_score = types.GameHighScore._parse_action(
                client, message, users
            )
        elif isinstance(action, raw.types.MessageActionPinMessage):
            parsed_message.service = enums.MessageServiceType.PINNED_MESSAGE
            parsed_message.pinned_message = parsed_message.reply_to_message  # Why...
        elif isinstance(action, raw.types.MessageActionPollAppendAnswer):
            parsed_message.service = enums.MessageServiceType.POLL_OPTION_ADDED
            parsed_message.poll_option_added = await types.PollOptionAdded._parse(
                client, parsed_message.reply_to_message, action
            )
        elif isinstance(action, raw.types.MessageActionPollDeleteAnswer):
            parsed_message.service = enums.MessageServiceType.POLL_OPTION_DELETED
            parsed_message.poll_option_deleted = await types.PollOptionDeleted._parse(
                client, parsed_message.reply_to_message, action
            )

        await client.message_cache.set((parsed_message.chat.id, parsed_message.id), parsed_message)

        return parsed_message

    @staticmethod
    async def _parse_message(
        client: pyrogram.Client,
        message: raw.types.Message,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
        topics: dict[int, raw.base.ForumTopic] | None = None,
        is_scheduled: bool = False,
        replies: int = 1,
        business_connection_id: str | None = None,
        guest_query_id: str | None = None,
        raw_reply_to_message: raw.base.Message | None = None,
    ) -> Message:
        from_id = utils.get_raw_peer_id(message.from_id)
        peer_id = utils.get_raw_peer_id(message.peer_id)

        if (
            isinstance(message.from_id, raw.types.PeerUser)
            and isinstance(message.peer_id, raw.types.PeerUser)
            and (from_id not in users or peer_id not in users)
        ):
            try:
                r = await client.invoke(
                    raw.functions.users.GetUsers(
                        id=[
                            await client.resolve_peer(from_id),
                            await client.resolve_peer(peer_id),
                        ]
                    )
                )
            except PeerIdInvalid:
                pass
            else:
                users.update({i.id: i for i in r})

        from_user = types.User._parse(client, users.get(from_id or peer_id))
        sender_chat = (
            types.Chat._parse(client, message, users, chats, is_chat=False)
            if not from_user
            else None
        )
        chat = types.Chat._parse(client, message, users, chats, is_chat=True)

        entities = types.List(
            filter(
                lambda x: x is not None,
                [
                    types.MessageEntity._parse(client, entity, users)
                    for entity in (message.entities or [])
                ],
            )
        )

        forward_header = message.fwd_from
        forward_origin = None

        if forward_header:
            forward_origin = await types.MessageOrigin._parse(
                client,
                forward_header,
                users,
                chats,
            )

        photo = None
        live_photo = None
        location = None
        contact = None
        venue = None
        game = None
        giveaway = None
        giveaway_winners = None
        invoice = None
        story = None
        audio = None
        voice = None
        animation = None
        video = None
        video_note = None
        sticker = None
        document = None
        web_page = None
        link_preview_options = None
        poll = None
        dice = None
        paid_media = None
        checklist = None

        media = message.media
        media_type = None
        has_media_spoiler = None

        if media:
            if isinstance(media, raw.types.MessageMediaPhoto):
                if media.live_photo:
                    doc = media.video

                    if isinstance(doc, raw.types.Document):
                        attributes = {type(i): i for i in doc.attributes}

                        if raw.types.DocumentAttributeVideo in attributes:
                            video_attributes = attributes[raw.types.DocumentAttributeVideo]

                            live_photo = types.LivePhoto._parse(client, doc, video_attributes)

                    media_type = enums.MessageMediaType.LIVE_PHOTO
                else:
                    media_type = enums.MessageMediaType.PHOTO

                photo = types.Photo._parse(client, media.photo, media.ttl_seconds)
                has_media_spoiler = media.spoiler
            elif isinstance(media, raw.types.MessageMediaGeo):
                location = types.Location._parse(media.geo)
                media_type = enums.MessageMediaType.LOCATION
            elif isinstance(media, raw.types.MessageMediaGeoLive):
                location = types.Location._parse_media(media)
                media_type = enums.MessageMediaType.LOCATION
            elif isinstance(media, raw.types.MessageMediaContact):
                contact = types.Contact._parse(client, media)
                media_type = enums.MessageMediaType.CONTACT
            elif isinstance(media, raw.types.MessageMediaVenue):
                venue = types.Venue._parse(client, media)
                media_type = enums.MessageMediaType.VENUE
            elif isinstance(media, raw.types.MessageMediaGame):
                game = types.Game._parse(client, media)
                media_type = enums.MessageMediaType.GAME
            elif isinstance(media, raw.types.MessageMediaGiveaway):
                giveaway = await types.Giveaway._parse(client, media, chats)
                media_type = enums.MessageMediaType.GIVEAWAY
            elif isinstance(media, raw.types.MessageMediaGiveawayResults):
                giveaway_winners = await types.GiveawayWinners._parse(client, media, users, chats)
                media_type = enums.MessageMediaType.GIVEAWAY_WINNERS
            elif isinstance(media, raw.types.MessageMediaInvoice):
                invoice = types.Invoice._parse(client, media)
                media_type = enums.MessageMediaType.INVOICE
            elif isinstance(media, raw.types.MessageMediaStory):
                story = await types.Story._parse(client, media, media.peer, users, chats)
                media_type = enums.MessageMediaType.STORY
            elif isinstance(media, raw.types.MessageMediaDocument):
                doc = media.document
                has_media_spoiler = media.spoiler

                if isinstance(doc, raw.types.Document):
                    attributes = {type(i): i for i in doc.attributes}

                    file_name = getattr(
                        attributes.get(raw.types.DocumentAttributeFilename), "file_name", None
                    )

                    if raw.types.DocumentAttributeAnimated in attributes:
                        video_attributes = attributes.get(raw.types.DocumentAttributeVideo)

                        if video_attributes and video_attributes.round_message:
                            video_note = types.VideoNote._parse(
                                client, doc, video_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VIDEO_NOTE
                        else:
                            animation = types.Animation._parse(
                                client, doc, video_attributes, file_name
                            )
                            media_type = enums.MessageMediaType.ANIMATION
                    elif raw.types.DocumentAttributeSticker in attributes:
                        sticker = await types.Sticker._parse(client, doc, attributes)
                        media_type = enums.MessageMediaType.STICKER
                    elif raw.types.DocumentAttributeVideo in attributes:
                        video_attributes = attributes[raw.types.DocumentAttributeVideo]

                        if video_attributes.round_message:
                            video_note = types.VideoNote._parse(
                                client, doc, video_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VIDEO_NOTE
                        else:
                            video = types.Video._parse(
                                client,
                                doc,
                                video_attributes,
                                file_name,
                                media.ttl_seconds,
                                media.video_cover,
                                media.video_timestamp,
                                media.alt_documents,
                            )
                            media_type = enums.MessageMediaType.VIDEO
                    elif raw.types.DocumentAttributeAudio in attributes:
                        audio_attributes = attributes[raw.types.DocumentAttributeAudio]

                        if audio_attributes.voice:
                            voice = types.Voice._parse(
                                client, doc, audio_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VOICE
                        else:
                            audio = types.Audio._parse(client, doc, audio_attributes, file_name)
                            media_type = enums.MessageMediaType.AUDIO
                    else:
                        document = types.Document._parse(client, doc, file_name)
                        media_type = enums.MessageMediaType.DOCUMENT
            elif isinstance(media, raw.types.MessageMediaWebPage):
                media_type = enums.MessageMediaType.WEB_PAGE
                web_page = types.WebPage._parse(client, media)
            elif isinstance(media, raw.types.MessageMediaPoll):
                poll = await types.Poll._parse(
                    client,
                    media,
                    description=await types.FormattedText._parse(
                        client,
                        raw.types.TextWithEntities(
                            text=message.message, entities=message.entities
                        ),
                    )
                    if message.message
                    else None,
                    users=users,
                    chats=chats,
                )
                media_type = enums.MessageMediaType.POLL
            elif isinstance(media, raw.types.MessageMediaDice):
                dice = types.Dice._parse(client, media)
                media_type = enums.MessageMediaType.DICE
            elif isinstance(media, raw.types.MessageMediaPaidMedia):
                paid_media = types.PaidMediaInfo._parse(client, media)
                media_type = enums.MessageMediaType.PAID_MEDIA
            elif isinstance(media, raw.types.MessageMediaToDo):
                media_type = enums.MessageMediaType.CHECKLIST
                checklist = await types.Checklist._parse(client, media, users, chats)
            else:
                media_type = enums.MessageMediaType.UNSUPPORTED
                media = None

        link_preview_options = types.LinkPreviewOptions._parse(
            media,
            getattr(getattr(media, "webpage", None), "url", utils.get_first_url(message.message)),
            message.invert_media,
        )

        reply_markup = message.reply_markup

        if reply_markup:
            if isinstance(reply_markup, raw.types.ReplyKeyboardForceReply):
                reply_markup = types.ForceReply.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyKeyboardMarkup):
                reply_markup = types.ReplyKeyboardMarkup.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyInlineMarkup):
                reply_markup = types.InlineKeyboardMarkup.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyKeyboardHide):
                reply_markup = types.ReplyKeyboardRemove.read(reply_markup)
            else:
                reply_markup = None

        reactions = await types.MessageReactions._parse(client, message.reactions, users, chats)

        parsed_message = Message(
            id=message.id,
            effect_id=getattr(message, "effect", None),
            rich_message=await types.RichMessage._parse(
                client, message.rich_message, users, chats
            ),
            date=utils.timestamp_to_datetime(message.date),
            guest_query_id=str(guest_query_id) if guest_query_id else None,
            chat=chat,
            from_user=from_user,
            sender_chat=sender_chat,
            sender_business_bot=types.User._parse(
                client, users.get(getattr(message, "via_business_bot_id", None))
            ),
            sender_tag=message.from_rank,
            text=(
                Str(message.message).init(entities) or None
                if media is None or web_page is not None
                else None
            ),
            caption=(
                Str(message.message).init(entities) or None
                if media is not None and web_page is None
                else None
            ),
            entities=(entities or None if media is None or web_page is not None else None),
            caption_entities=(
                entities or None if media is not None and web_page is None else None
            ),
            author_signature=message.post_author,
            is_paid_post=bool(getattr(message.suggested_post, "price", None)),
            has_protected_content=message.noforwards,
            has_media_spoiler=has_media_spoiler,
            forward_origin=forward_origin,
            mentioned=message.mentioned,
            scheduled=is_scheduled,
            from_scheduled=message.from_scheduled,
            media=media_type,
            paid_media=paid_media,
            checklist=checklist,
            show_caption_above_media=message.invert_media,
            edit_date=utils.timestamp_to_datetime(message.edit_date),
            edit_hidden=message.edit_hide,
            media_group_id=message.grouped_id,
            photo=photo,
            live_photo=live_photo,
            location=location,
            contact=contact,
            venue=venue,
            audio=audio,
            voice=voice,
            animation=animation,
            game=game,
            giveaway=giveaway,
            giveaway_winners=giveaway_winners,
            invoice=invoice,
            story=story,
            video=video,
            video_processing_pending=message.video_processing_pending,
            video_note=video_note,
            sticker=sticker,
            document=document,
            web_page=web_page,
            link_preview_options=link_preview_options,
            poll=poll,
            dice=dice,
            views=message.views,
            forwards=message.forwards,
            sender_boost_count=message.from_boosts_applied,
            via_bot=types.User._parse(client, users.get(message.via_bot_id)),
            outgoing=message.out,
            business_connection_id=business_connection_id,
            reply_markup=reply_markup,
            reactions=reactions,
            from_offline=message.offline,
            send_paid_messages_stars=message.paid_message_stars,
            unread_media=message.media_unread,
            silent=message.silent,
            pinned=message.pinned,
            restriction_reason=types.List(
                types.RestrictionReason._parse(reason)
                for reason in getattr(message, "restriction_reason", None) or []
            )
            or None,
            fact_check=await types.FactCheck._parse(client, message.factcheck, users),
            suggested_post_info=types.SuggestedPostInfo._parse(message.suggested_post),
            channel_post=message.post,
            repeat_period=message.schedule_repeat_period,
            summary_language_code=message.summary_from_language,
            guest_bot_caller_user=types.User._parse(
                client, users.get(utils.get_raw_peer_id(message.guestchat_via_from))
            ),
            guest_bot_caller_chat=types.Chat._parse_chat(
                client, chats.get(utils.get_raw_peer_id(message.guestchat_via_from))
            ),
            raw=message,
            client=client,
        )

        if forward_header and forward_header.saved_from_peer and forward_header.saved_from_msg_id:
            saved_from_peer_id = utils.get_raw_peer_id(forward_header.saved_from_peer)
            saved_from_peer_chat = chats.get(saved_from_peer_id)
            if (
                isinstance(saved_from_peer_chat, raw.types.Channel)
                and not saved_from_peer_chat.megagroup
            ):
                parsed_message.automatic_forward = True

        if message.reply_to:
            parsed_message = await types.Message.__parse_reply(
                client=client,
                parsed_message=parsed_message,
                message=message,
                users=users,
                chats=chats,
                replies=replies,
                business_connection_id=business_connection_id,
                raw_reply_to_message=raw_reply_to_message,
            )

        if topics:
            parsed_message.topic = await types.ForumTopic._parse(
                client, topics.get(parsed_message.message_thread_id), users=users, chats=chats
            )

            if parsed_message.topic:
                await client.topic_cache.set(
                    (parsed_message.chat.id, parsed_message.topic.id), parsed_message.topic
                )

        if not parsed_message.topic and parsed_message.chat.is_forum:
            parsed_topic = await client.topic_cache.get((
                parsed_message.chat.id,
                parsed_message.message_thread_id,
            ))

            if parsed_topic:
                parsed_message.topic = parsed_topic
            elif client.fetch_topics and client.me and not client.me.is_bot:
                try:
                    parsed_message.topic = await client.get_forum_topics_by_id(
                        chat_id=parsed_message.chat.id,
                        topic_ids=parsed_message.message_thread_id or 1,
                    )

                    if parsed_message.topic:
                        await client.topic_cache.set(
                            (parsed_message.chat.id, parsed_message.topic.id), parsed_message.topic
                        )
                except (ChannelPrivate, ChannelForumMissing):
                    pass

        if chat.type == enums.ChatType.DIRECT and message.saved_peer_id:
            parsed_message.direct_messages_topic_id = message.saved_peer_id.user_id

            parsed_topic = await client.topic_cache.get((
                parsed_message.chat.id,
                parsed_message.direct_messages_topic_id,
            ))

            if parsed_topic:
                parsed_message.topic = parsed_topic
            elif client.fetch_topics and client.me and not client.me.is_bot:
                try:
                    parsed_message.topic = await client.get_direct_messages_topics_by_id(
                        chat_id=parsed_message.chat.id,
                        topic_ids=parsed_message.direct_messages_topic_id,
                    )

                    if parsed_message.topic:
                        await client.topic_cache.set(
                            (parsed_message.chat.id, parsed_message.topic.id), parsed_message.topic
                        )
                except (ChannelPrivate, ChatAdminRequired):
                    pass

        if not parsed_message.poll:  # Do not cache poll messages
            await client.message_cache.set(
                (parsed_message.chat.id, parsed_message.id), parsed_message
            )

        return parsed_message

    @staticmethod
    async def _parse_ephemeral_message(
        client: pyrogram.Client,
        message: raw.types.EphemeralMessage,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
        replies: int = 1,
    ) -> Message:
        from_id = utils.get_raw_peer_id(message.from_id)
        peer_id = utils.get_raw_peer_id(message.peer_id)

        if (
            isinstance(message.from_id, raw.types.PeerUser)
            and isinstance(message.peer_id, raw.types.PeerUser)
            and (from_id not in users or peer_id not in users)
        ):
            try:
                r = await client.invoke(
                    raw.functions.users.GetUsers(
                        id=[
                            await client.resolve_peer(from_id),
                            await client.resolve_peer(peer_id),
                        ]
                    )
                )
            except PeerIdInvalid:
                pass
            else:
                users.update({i.id: i for i in r})

        from_user = types.User._parse(client, users.get(from_id or peer_id))
        sender_chat = (
            types.Chat._parse(client, message, users, chats, is_chat=False)
            if not from_user
            else None
        )
        chat = types.Chat._parse(client, message, users, chats, is_chat=True)

        entities = types.List(
            filter(
                lambda x: x is not None,
                [
                    types.MessageEntity._parse(client, entity, users)
                    for entity in (message.entities or [])
                ],
            )
        )

        photo = None
        live_photo = None
        location = None
        contact = None
        venue = None
        game = None
        giveaway = None
        giveaway_winners = None
        invoice = None
        story = None
        audio = None
        voice = None
        animation = None
        video = None
        video_note = None
        sticker = None
        document = None
        web_page = None
        link_preview_options = None
        poll = None
        dice = None
        paid_media = None
        checklist = None

        media = message.media
        media_type = None
        has_media_spoiler = None

        if media:
            if isinstance(media, raw.types.MessageMediaPhoto):
                if media.live_photo:
                    doc = media.video

                    if isinstance(doc, raw.types.Document):
                        attributes = {type(i): i for i in doc.attributes}

                        if raw.types.DocumentAttributeVideo in attributes:
                            video_attributes = attributes[raw.types.DocumentAttributeVideo]

                            live_photo = types.LivePhoto._parse(client, doc, video_attributes)

                    media_type = enums.MessageMediaType.LIVE_PHOTO
                else:
                    media_type = enums.MessageMediaType.PHOTO

                photo = types.Photo._parse(client, media.photo, media.ttl_seconds)
                has_media_spoiler = media.spoiler
            elif isinstance(media, raw.types.MessageMediaGeo):
                location = types.Location._parse(media.geo)
                media_type = enums.MessageMediaType.LOCATION
            elif isinstance(media, raw.types.MessageMediaGeoLive):
                location = types.Location._parse_media(media)
                media_type = enums.MessageMediaType.LOCATION
            elif isinstance(media, raw.types.MessageMediaContact):
                contact = types.Contact._parse(client, media)
                media_type = enums.MessageMediaType.CONTACT
            elif isinstance(media, raw.types.MessageMediaVenue):
                venue = types.Venue._parse(client, media)
                media_type = enums.MessageMediaType.VENUE
            elif isinstance(media, raw.types.MessageMediaGame):
                game = types.Game._parse(client, media)
                media_type = enums.MessageMediaType.GAME
            elif isinstance(media, raw.types.MessageMediaGiveaway):
                giveaway = await types.Giveaway._parse(client, media, chats)
                media_type = enums.MessageMediaType.GIVEAWAY
            elif isinstance(media, raw.types.MessageMediaGiveawayResults):
                giveaway_winners = await types.GiveawayWinners._parse(client, media, users, chats)
                media_type = enums.MessageMediaType.GIVEAWAY_WINNERS
            elif isinstance(media, raw.types.MessageMediaInvoice):
                invoice = types.Invoice._parse(client, media)
                media_type = enums.MessageMediaType.INVOICE
            elif isinstance(media, raw.types.MessageMediaStory):
                story = await types.Story._parse(client, media, media.peer, users, chats)
                media_type = enums.MessageMediaType.STORY
            elif isinstance(media, raw.types.MessageMediaDocument):
                doc = media.document
                has_media_spoiler = media.spoiler

                if isinstance(doc, raw.types.Document):
                    attributes = {type(i): i for i in doc.attributes}

                    file_name = getattr(
                        attributes.get(raw.types.DocumentAttributeFilename), "file_name", None
                    )

                    if raw.types.DocumentAttributeAnimated in attributes:
                        video_attributes = attributes.get(raw.types.DocumentAttributeVideo)

                        if video_attributes and video_attributes.round_message:
                            video_note = types.VideoNote._parse(
                                client, doc, video_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VIDEO_NOTE
                        else:
                            animation = types.Animation._parse(
                                client, doc, video_attributes, file_name
                            )
                            media_type = enums.MessageMediaType.ANIMATION
                    elif raw.types.DocumentAttributeSticker in attributes:
                        sticker = await types.Sticker._parse(client, doc, attributes)
                        media_type = enums.MessageMediaType.STICKER
                    elif raw.types.DocumentAttributeVideo in attributes:
                        video_attributes = attributes[raw.types.DocumentAttributeVideo]

                        if video_attributes.round_message:
                            video_note = types.VideoNote._parse(
                                client, doc, video_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VIDEO_NOTE
                        else:
                            video = types.Video._parse(
                                client,
                                doc,
                                video_attributes,
                                file_name,
                                media.ttl_seconds,
                                media.video_cover,
                                media.video_timestamp,
                                media.alt_documents,
                            )
                            media_type = enums.MessageMediaType.VIDEO
                    elif raw.types.DocumentAttributeAudio in attributes:
                        audio_attributes = attributes[raw.types.DocumentAttributeAudio]

                        if audio_attributes.voice:
                            voice = types.Voice._parse(
                                client, doc, audio_attributes, media.ttl_seconds
                            )
                            media_type = enums.MessageMediaType.VOICE
                        else:
                            audio = types.Audio._parse(client, doc, audio_attributes, file_name)
                            media_type = enums.MessageMediaType.AUDIO
                    else:
                        document = types.Document._parse(client, doc, file_name)
                        media_type = enums.MessageMediaType.DOCUMENT
            elif isinstance(media, raw.types.MessageMediaWebPage):
                media_type = enums.MessageMediaType.WEB_PAGE
                web_page = types.WebPage._parse(client, media)
            elif isinstance(media, raw.types.MessageMediaPoll):
                poll = await types.Poll._parse(
                    client,
                    media,
                    description=await types.FormattedText._parse(
                        client,
                        raw.types.TextWithEntities(
                            text=message.message, entities=message.entities
                        ),
                    )
                    if message.message
                    else None,
                    users=users,
                    chats=chats,
                )
                media_type = enums.MessageMediaType.POLL
            elif isinstance(media, raw.types.MessageMediaDice):
                dice = types.Dice._parse(client, media)
                media_type = enums.MessageMediaType.DICE
            elif isinstance(media, raw.types.MessageMediaPaidMedia):
                paid_media = types.PaidMediaInfo._parse(client, media)
                media_type = enums.MessageMediaType.PAID_MEDIA
            elif isinstance(media, raw.types.MessageMediaToDo):
                media_type = enums.MessageMediaType.CHECKLIST
                checklist = await types.Checklist._parse(client, media, users, chats)
            else:
                media_type = enums.MessageMediaType.UNSUPPORTED
                media = None

        link_preview_options = types.LinkPreviewOptions._parse(
            media,
            getattr(getattr(media, "webpage", None), "url", utils.get_first_url(message.message)),
        )

        reply_markup = message.reply_markup

        if reply_markup:
            if isinstance(reply_markup, raw.types.ReplyKeyboardForceReply):
                reply_markup = types.ForceReply.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyKeyboardMarkup):
                reply_markup = types.ReplyKeyboardMarkup.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyInlineMarkup):
                reply_markup = types.InlineKeyboardMarkup.read(reply_markup)
            elif isinstance(reply_markup, raw.types.ReplyKeyboardHide):
                reply_markup = types.ReplyKeyboardRemove.read(reply_markup)
            else:
                reply_markup = None

        parsed_message = Message(
            id=0,
            ephemeral_message_id=message.id,
            date=utils.timestamp_to_datetime(message.date),
            chat=chat,
            from_user=from_user,
            sender_chat=sender_chat,
            receiver_user=types.User._parse(client, users.get(message.receiver_id)),
            text=(
                Str(message.message).init(entities) or None
                if media is None or web_page is not None
                else None
            ),
            caption=(
                Str(message.message).init(entities) or None
                if media is not None and web_page is None
                else None
            ),
            entities=(entities or None if media is None or web_page is not None else None),
            caption_entities=(
                entities or None if media is not None and web_page is None else None
            ),
            has_media_spoiler=has_media_spoiler,
            media=media_type,
            paid_media=paid_media,
            checklist=checklist,
            photo=photo,
            live_photo=live_photo,
            location=location,
            contact=contact,
            venue=venue,
            audio=audio,
            voice=voice,
            animation=animation,
            game=game,
            giveaway=giveaway,
            giveaway_winners=giveaway_winners,
            invoice=invoice,
            story=story,
            video=video,
            video_note=video_note,
            sticker=sticker,
            document=document,
            web_page=web_page,
            link_preview_options=link_preview_options,
            poll=poll,
            dice=dice,
            outgoing=message.out,
            reply_markup=reply_markup,
            raw=message,
            client=client,
        )

        if message.reply_to:
            parsed_message = await types.Message.__parse_reply(
                client=client,
                parsed_message=parsed_message,
                message=message,
                users=users,
                chats=chats,
                replies=replies,
            )

        if not parsed_message.topic and parsed_message.chat.is_forum:
            parsed_topic = await client.topic_cache.get((
                parsed_message.chat.id,
                parsed_message.message_thread_id,
            ))

            if parsed_topic:
                parsed_message.topic = parsed_topic
            elif client.fetch_topics and client.me and not client.me.is_bot:
                try:
                    parsed_message.topic = await client.get_forum_topics_by_id(
                        chat_id=parsed_message.chat.id,
                        topic_ids=parsed_message.message_thread_id or 1,
                    )

                    if parsed_message.topic:
                        await client.topic_cache.set(
                            (parsed_message.chat.id, parsed_message.topic.id), parsed_message.topic
                        )
                except (ChannelPrivate, ChannelForumMissing):
                    pass

        if not parsed_message.poll:  # Do not cache poll messages
            await client.message_cache.set(
                (parsed_message.chat.id, parsed_message.id), parsed_message
            )

        return parsed_message

    @staticmethod
    async def __parse_reply(
        client: pyrogram.Client,
        parsed_message: Message,
        message: raw.base.Message,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
        replies: int = 1,
        business_connection_id: str | None = None,
        raw_reply_to_message: raw.base.Message | None = None,
    ):
        if isinstance(message.reply_to, raw.types.MessageReplyHeader):
            parsed_message.reply_to_message_id = message.reply_to.reply_to_msg_id
            parsed_message.reply_to_top_message_id = message.reply_to.reply_to_top_id
            parsed_message.reply_to_checklist_task_id = message.reply_to.todo_item_id
            parsed_message.reply_to_poll_option_id = (
                message.reply_to.poll_option.decode()
                if message.reply_to.poll_option is not None
                else None
            )

            if replies:
                if message.reply_to.reply_to_peer_id:
                    key = (
                        utils.get_peer_id(message.reply_to.reply_to_peer_id),
                        message.reply_to.reply_to_msg_id,
                    )
                    reply_to_params = {"chat_id": key[0], "message_ids": key[1]}
                else:
                    key = (parsed_message.chat.id, parsed_message.reply_to_message_id)
                    # This tree spells "fetch what this message replies to" as
                    # reply_to_message_ids, where Kurigram uses message_ids + reply=True.
                    reply_to_params = {"chat_id": key[0], "reply_to_message_ids": message.id}

                parsed_message.reply_to_message = await client.message_cache.get(key)

                if raw_reply_to_message:  # For business bots only
                    parsed_message.reply_to_message = await types.Message._parse(
                        client,
                        raw_reply_to_message,
                        users,
                        chats,
                        business_connection_id=business_connection_id,
                        replies=0,
                    )
                elif client.fetch_replies and not parsed_message.reply_to_message:
                    with contextlib.suppress(ChannelPrivate, ChannelInvalid, MessageIdsEmpty):
                        parsed_message.reply_to_message = await client.get_messages(
                            replies=replies - 1, **reply_to_params
                        )

            if message.reply_to.forum_topic:
                parsed_message.topic_message = True

                if message.reply_to.reply_to_top_id:
                    parsed_message.message_thread_id = message.reply_to.reply_to_top_id
                elif message.reply_to.reply_to_msg_id:
                    parsed_message.message_thread_id = message.reply_to.reply_to_msg_id
                else:
                    parsed_message.message_thread_id = 1

            if message.reply_to.quote:
                parsed_message.quote = await types.TextQuote._parse(
                    client, users, message.reply_to
                )

            if message.reply_to.reply_from:
                parsed_message.external_reply = await types.ExternalReplyInfo._parse(
                    client, message.reply_to, users, chats
                )
        elif isinstance(message.reply_to, raw.types.MessageReplyStoryHeader):
            parsed_message.reply_to_story_id = message.reply_to.story_id
            parsed_message.reply_to_story_user_id = utils.get_peer_id(message.reply_to.peer)

            if client.fetch_stories and client.me and not client.me.is_bot:
                parsed_message.reply_to_story = await client.get_stories(
                    utils.get_peer_id(message.reply_to.peer), message.reply_to.story_id
                )

        return parsed_message

    @staticmethod
    async def _parse(
        client: pyrogram.Client,
        message: raw.base.Message,
        users: dict[int, raw.base.User],
        chats: dict[int, raw.base.Chat],
        topics: dict[int, raw.base.ForumTopic] | None = None,
        is_scheduled: bool = False,
        replies: int = 1,
        business_connection_id: str | None = None,
        guest_query_id: str | None = None,
        raw_reply_to_message: raw.base.Message | None = None,
    ) -> Message:
        if isinstance(message, raw.types.MessageEmpty):
            return Message(
                id=message.id,
                empty=True,
                business_connection_id=business_connection_id,
                raw=message,
                client=client,
            )

        if isinstance(message, raw.types.MessageService):
            return await types.Message._parse_service(
                client=client,
                message=message,
                users=users,
                chats=chats,
                replies=replies,
                business_connection_id=business_connection_id,
                raw_reply_to_message=raw_reply_to_message,
            )

        if isinstance(message, raw.types.Message):
            return await types.Message._parse_message(
                client=client,
                message=message,
                users=users,
                chats=chats,
                topics=topics,
                is_scheduled=is_scheduled,
                replies=replies,
                business_connection_id=business_connection_id,
                guest_query_id=guest_query_id,
                raw_reply_to_message=raw_reply_to_message,
            )

        if isinstance(message, raw.types.EphemeralMessage):
            return await types.Message._parse_ephemeral_message(
                client=client,
                message=message,
                users=users,
                chats=chats,
                replies=replies,
            )
        return None

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
            chat_id=self.chat.id if self.chat else None,
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
            chat_id=self.chat.id if self.chat else None,
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
            chat_id=self.chat.id if self.chat else None,
            listener_type=listener_type,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    @property
    def link(self) -> str:
        if (
            self.chat.type
            in {enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL}
            and self.chat.username
        ):
            return f"https://t.me/{self.chat.username}/{self.id}"
        return f"https://t.me/c/{utils.get_channel_id(self.chat.id)}/{self.id}"

    async def get_media_group(self) -> list[types.Message]:
        """Bound method *get_media_group* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.get_media_group(chat_id=message.chat.id, message_id=message.id)

        Example:
            .. code-block:: python

                await message.get_media_group()

        Returns:
            List of :obj:`~pyrogram.types.Message`: On success, a list of messages of the media group is returned.

        Raises:
            ValueError: In case the passed message id doesn't belong to a media group.
        """

        return await self._client.get_media_group(chat_id=self.chat.id, message_id=self.id)

    async def reply_text(
        self,
        text: str,
        quote: bool | None = None,
        parse_mode: enums.ParseMode | None = None,
        entities: list[types.MessageEntity] | None = None,
        link_preview_options: types.LinkPreviewOptions | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup=None,
    ) -> Message:
        """Bound method *reply_text* of :obj:`~pyrogram.types.Message`.

        An alias exists as *reply*.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_message(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                text="hello",
                reply_parameters=ReplyParameters(message_id=message.id),
            )

        Example:
            .. code-block:: python

                await message.reply_text("hello", quote=True)

        Parameters:
            text (``str``):
                Text of the message to be sent.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            link_preview_options (:obj:`~pyrogram.types.LinkPreviewOptions`, *optional*):
                Options for how the link preview is generated.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent Message is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_message(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            schedule_date=schedule_date,
            protect_content=protect_content,
            reply_markup=reply_markup,
        )

    reply = reply_text

    async def reply_animation(
        self,
        animation: str | BinaryIO,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        has_spoiler: bool | None = None,
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        thumb: str | BinaryIO | None = None,
        disable_notification: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        reply_parameters: types.ReplyParameters | None = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_animation* :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_animation(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                animation=animation,
            )

        Example:
            .. code-block:: python

                await message.reply_animation(animation)

        Parameters:
            animation (``str``):
                Animation to send.
                Pass a file_id as string to send an animation that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get an animation from the Internet, or
                pass a file path as string to upload a new animation that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``str``, *optional*):
                Animation caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            has_spoiler (``bool``, *optional*):
                Pass True if the animation needs to be covered with a spoiler animation.

            duration (``int``, *optional*):
                Duration of sent animation in seconds.

            width (``int``, *optional*):
                Animation width.

            height (``int``, *optional*):
                Animation height.

            thumb (``str | BinaryIO``, *optional*):
                Thumbnail of the animation file sent.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_animation(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            animation=animation,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_audio(
        self,
        audio: str | BinaryIO,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        duration: int = 0,
        performer: str | None = None,
        title: str | None = None,
        thumb: str | BinaryIO | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_audio* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_audio(
                chat_id=message.chat.id, message_thread_id=message.message_thread_id, audio=audio
            )

        Example:
            .. code-block:: python

                await message.reply_audio(audio)

        Parameters:
            audio (``str``):
                Audio file to send.
                Pass a file_id as string to send an audio file that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get an audio file from the Internet, or
                pass a file path as string to upload a new audio file that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``str``, *optional*):
                Audio caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            duration (``int``, *optional*):
                Duration of the audio in seconds.

            performer (``str``, *optional*):
                Performer.

            title (``str``, *optional*):
                Track name.

            thumb (``str | BinaryIO``, *optional*):
                Thumbnail of the music file album cover.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_audio(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_cached_media(
        self,
        file_id: str,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_cached_media* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_cached_media(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                file_id=file_id,
            )

        Example:
            .. code-block:: python

                await message.reply_cached_media(file_id)

        Parameters:
            file_id (``str``):
                Media to send.
                Pass a file_id as string to send a media that exists on the Telegram servers.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``bool``, *optional*):
                Media caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_cached_media(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            file_id=file_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    async def reply_chat_action(self, action: enums.ChatAction) -> bool:
        """Bound method *reply_chat_action* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            from pyrogram import enums

            await client.send_chat_action(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                action=enums.ChatAction.TYPING,
            )

        Example:
            .. code-block:: python

                from pyrogram import enums

                await message.reply_chat_action(enums.ChatAction.TYPING)

        Parameters:
            action (:obj:`~pyrogram.enums.ChatAction`):
                Type of action to broadcast.

        Returns:
            ``bool``: On success, True is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
            ValueError: In case the provided string is not a valid chat action.
        """
        return await self._client.send_chat_action(
            chat_id=self.chat.id, message_thread_id=self.message_thread_id, action=action
        )

    async def reply_contact(
        self,
        phone_number: str,
        first_name: str,
        quote: bool | None = None,
        last_name: str = "",
        vcard: str = "",
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_contact* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_contact(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                phone_number=phone_number,
                first_name=first_name,
            )

        Example:
            .. code-block:: python

                await message.reply_contact("+1-123-456-7890", "Name")

        Parameters:
            phone_number (``str``):
                Contact's phone number.

            first_name (``str``):
                Contact's first name.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            last_name (``str``, *optional*):
                Contact's last name.

            vcard (``str``, *optional*):
                Additional data about the contact in the form of a vCard, 0-2048 bytes

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_contact(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    async def reply_document(
        self,
        document: str | BinaryIO,
        quote: bool | None = None,
        thumb: str | BinaryIO | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        file_name: str | None = None,
        force_document: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_document* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_document(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                document=document,
            )

        Example:
            .. code-block:: python

                await message.reply_document(document)

        Parameters:
            document (``str``):
                File to send.
                Pass a file_id as string to send a file that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get a file from the Internet, or
                pass a file path as string to upload a new file that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            thumb (``str | BinaryIO``, *optional*):
                Thumbnail of the file sent.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            caption (``str``, *optional*):
                Document caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            file_name (``str``, *optional*):
                File name of the document sent.
                Defaults to file's path basename.

            force_document (``bool``, *optional*):
                Pass True to force sending files as document. Useful for video files that need to be sent as
                document messages instead of video messages.
                Defaults to False.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_document(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            file_name=file_name,
            force_document=force_document,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            schedule_date=schedule_date,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_game(
        self,
        game_short_name: str,
        quote: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_game* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_game(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                game_short_name="lumberjack",
            )

        Example:
            .. code-block:: python

                await message.reply_game("lumberjack")

        Parameters:
            game_short_name (``str``):
                Short name of the game, serves as the unique identifier for the game. Set up your games via Botfather.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An object for an inline keyboard. If empty, one ‘Play game_title’ button will be shown automatically.
                If not empty, the first button must launch the game.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_game(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    async def reply_inline_bot_result(
        self,
        query_id: int,
        result_id: str,
        quote: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
    ) -> Message:
        """Bound method *reply_inline_bot_result* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_inline_bot_result(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                query_id=query_id,
                result_id=result_id,
            )

        Example:
            .. code-block:: python

                await message.reply_inline_bot_result(query_id, result_id)

        Parameters:
            query_id (``int``):
                Unique identifier for the answered query.

            result_id (``str``):
                Unique identifier for the result that was chosen.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

        Returns:
            On success, the sent Message is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_inline_bot_result(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            query_id=query_id,
            result_id=result_id,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
        )

    async def reply_location(
        self,
        latitude: float,
        longitude: float,
        quote: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_location* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_location(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                latitude=latitude,
                longitude=longitude,
            )

        Example:
            .. code-block:: python

                await message.reply_location(latitude, longitude)

        Parameters:
            latitude (``float``):
                Latitude of the location.

            longitude (``float``):
                Longitude of the location.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_location(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            latitude=latitude,
            longitude=longitude,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    async def reply_media_group(
        self,
        media: list[types.InputMediaPhoto | types.InputMediaVideo],
        quote: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
    ) -> list[types.Message]:
        """Bound method *reply_media_group* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_media_group(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                media=list_of_media,
            )

        Example:
            .. code-block:: python

                await message.reply_media_group(list_of_media)

        Parameters:
            media (``list``):
                A list containing either :obj:`~pyrogram.types.InputMediaPhoto` or
                :obj:`~pyrogram.types.InputMediaVideo` objects
                describing photos and videos to be sent, must include 2–10 items.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

        Returns:
            On success, a :obj:`~pyrogram.types.List` object is returned containing all the
            single messages sent.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_media_group(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            media=media,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
        )

    async def reply_photo(
        self,
        photo: str | BinaryIO,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        has_spoiler: bool | None = None,
        ttl_seconds: int | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_photo* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_photo(
                chat_id=message.chat.id, message_thread_id=message.message_thread_id, photo=photo
            )

        Example:
            .. code-block:: python

                await message.reply_photo(photo)

        Parameters:
            photo (``str``):
                Photo to send.
                Pass a file_id as string to send a photo that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get a photo from the Internet, or
                pass a file path as string to upload a new photo that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``str``, *optional*):
                Photo caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            has_spoiler (``bool``, *optional*):
                Pass True if the photo needs to be covered with a spoiler animation.

            ttl_seconds (``int``, *optional*):
                Self-Destruct Timer.
                If you set a timer, the photo will self-destruct in *ttl_seconds*
                seconds after it was viewed.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_photo(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            ttl_seconds=ttl_seconds,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_poll(
        self,
        question: str,
        options: list[types.InputPollOption],
        question_parse_mode: enums.ParseMode = None,
        question_entities: list[types.MessageEntity] | None = None,
        is_anonymous: bool = True,
        type: enums.PollType = enums.PollType.REGULAR,
        allows_multiple_answers: bool | None = None,
        correct_option_id: int | None = None,
        explanation: str | None = None,
        explanation_parse_mode: enums.ParseMode = None,
        explanation_entities: list[types.MessageEntity] | None = None,
        open_period: int | None = None,
        close_date: datetime | None = None,
        is_closed: bool | None = None,
        quote: bool | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_poll* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_poll(
                chat_id=message.chat.id,
                question="This is a poll",
                options=[
                    InputPollOption(text="A"),
                    InputPollOption(text="B"),
                    InputPollOption(text="C"),
                ],
            )

        Example:
            .. code-block:: python

                await message.reply_poll(
                    question="This is a poll",
                    options=[
                        InputPollOption(text="A"),
                        InputPollOption(text="B"),
                        InputPollOption(text="C"),
                    ],
                )

        Parameters:
            question (``str``):
                Poll question, 1-255 characters.

            options (List of :obj:`~pyrogram.types.InputPollOption`):
                List of answer options, 2-10 answer options,  1-100 characters for each option.

            question_parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            question_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the poll question, which can be specified instead of *question_parse_mode*.

            is_anonymous (``bool``, *optional*):
                True, if the poll needs to be anonymous.
                Defaults to True.

            type (:obj`~pyrogram.enums.PollType`, *optional*):
                Poll type, :obj:`~pyrogram.enums.PollType.QUIZ` or :obj:`~pyrogram.enums.PollType.REGULAR`.
                Defaults to :obj:`~pyrogram.enums.PollType.REGULAR`.

            allows_multiple_answers (``bool``, *optional*):
                True, if the poll allows multiple answers, ignored for polls in quiz mode.
                Defaults to False.

            correct_option_id (``int``, *optional*):
                0-based identifier of the correct answer option, required for polls in quiz mode.

            explanation (``str``, *optional*):
                Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style
                poll, 0-200 characters with at most 2 line feeds after entities parsing.

            explanation_parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            explanation_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the poll explanation, which can be specified instead of
                *parse_mode*.

            open_period (``int``, *optional*):
                Amount of time in seconds the poll will be active after creation, 5-600.
                Can't be used together with *close_date*.

            close_date (:py:obj:`~datetime.datetime`, *optional*):
                Point in time when the poll will be automatically closed.
                Must be at least 5 and no more than 600 seconds in the future.
                Can't be used together with *open_period*.

            is_closed (``bool``, *optional*):
                Pass True, if the poll needs to be immediately closed.
                This can be useful for poll preview.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_poll(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            question=question,
            options=options,
            question_parse_mode=question_parse_mode,
            question_entities=question_entities,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            explanation_entities=explanation_entities,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_parameters=reply_parameters,
            schedule_date=schedule_date,
            reply_markup=reply_markup,
        )

    async def reply_sticker(
        self,
        sticker: str | BinaryIO,
        quote: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_sticker* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_sticker(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                sticker=sticker,
            )

        Example:
            .. code-block:: python

                await message.reply_sticker(sticker)

        Parameters:
            sticker (``str``):
                Sticker to send.
                Pass a file_id as string to send a sticker that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get a .webp sticker file from the Internet, or
                pass a file path as string to upload a new sticker that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_sticker(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_venue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        quote: bool | None = None,
        foursquare_id: str = "",
        foursquare_type: str = "",
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> Message:
        """Bound method *reply_venue* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_venue(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                latitude=latitude,
                longitude=longitude,
                title="Venue title",
                address="Venue address",
            )

        Example:
            .. code-block:: python

                await message.reply_venue(latitude, longitude, "Venue title", "Venue address")

        Parameters:
            latitude (``float``):
                Latitude of the venue.

            longitude (``float``):
                Longitude of the venue.

            title (``str``):
                Name of the venue.

            address (``str``):
                Address of the venue.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            foursquare_id (``str``, *optional*):
                Foursquare identifier of the venue.

            foursquare_type (``str``, *optional*):
                Foursquare type of the venue, if known.
                (For example, "arts_entertainment/default", "arts_entertainment/aquarium" or "food/icecream".)

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_venue(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    async def reply_video(
        self,
        video: str | BinaryIO,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        has_spoiler: bool | None = None,
        ttl_seconds: int | None = None,
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        thumb: str | BinaryIO | None = None,
        supports_streaming: bool = True,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        no_sound: bool | None = False,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_video* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_video(
                chat_id=message.chat.id, message_thread_id=message.message_thread_id, video=video
            )

        Example:
            .. code-block:: python

                await message.reply_video(video)

        Parameters:
            video (``str``):
                Video to send.
                Pass a file_id as string to send a video that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get a video from the Internet, or
                pass a file path as string to upload a new video that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``str``, *optional*):
                Video caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            has_spoiler (``bool``, *optional*):
                Pass True if the video needs to be covered with a spoiler animation.

            ttl_seconds (``int``, *optional*):
                Self-Destruct Timer.
                If you set a timer, the video will self-destruct in *ttl_seconds*
                seconds after it was viewed.

            duration (``int``, *optional*):
                Duration of sent video in seconds.

            width (``int``, *optional*):
                Video width.

            height (``int``, *optional*):
                Video height.

            thumb (``str | BinaryIO``, *optional*):
                Thumbnail of the video sent.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            supports_streaming (``bool``, *optional*):
                Pass True, if the uploaded video is suitable for streaming.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            no_sound (``bool``, *optional*):
                Pass True if the video you are uploading is a video message with no sound.
                Does not work for external links.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_video(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            video=video,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            has_spoiler=has_spoiler,
            ttl_seconds=ttl_seconds,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            no_sound=no_sound,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_video_note(
        self,
        video_note: str | BinaryIO,
        quote: bool | None = None,
        duration: int = 0,
        length: int = 1,
        thumb: str | BinaryIO | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_video_note* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_video_note(
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                video_note=video_note,
            )

        Example:
            .. code-block:: python

                await message.reply_video_note(video_note)

        Parameters:
            video_note (``str``):
                Video note to send.
                Pass a file_id as string to send a video note that exists on the Telegram servers, or
                pass a file path as string to upload a new video note that exists on your local machine.
                Sending video notes by a URL is currently unsupported.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            duration (``int``, *optional*):
                Duration of sent video in seconds.

            length (``int``, *optional*):
                Video width and height.

            thumb (``str | BinaryIO``, *optional*):
                Thumbnail of the video sent.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_video_note(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def reply_voice(
        self,
        voice: str | BinaryIO,
        quote: bool | None = None,
        caption: str = "",
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        duration: int = 0,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> Message:
        """Bound method *reply_voice* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_voice(
                chat_id=message.chat.id, message_thread_id=message.message_thread_id, voice=voice
            )

        Example:
            .. code-block:: python

                await message.reply_voice(voice)

        Parameters:
            voice (``str``):
                Audio file to send.
                Pass a file_id as string to send an audio that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get an audio from the Internet, or
                pass a file path as string to upload a new audio that exists on your local machine.

            quote (``bool``, *optional*):
                If ``True``, the message will be sent as a reply to this message.
                If *reply_parameters* is passed, this parameter will be ignored.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            caption (``str``, *optional*):
                Voice message caption, 0-1024 characters.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            duration (``int``, *optional*):
                Duration of the voice message in seconds.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the sent :obj:`~pyrogram.types.Message` is returned.
            In case the upload is deliberately stopped with :meth:`~pyrogram.Client.stop_transmission`, None is returned
            instead.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if quote is None:
            quote = self.chat.type != enums.ChatType.PRIVATE

        if reply_parameters is None and quote:
            reply_parameters = types.ReplyParameters(message_id=self.id)

        return await self._client.send_voice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            progress=progress,
            progress_args=progress_args,
        )

    async def edit_text(
        self,
        text: str,
        parse_mode: enums.ParseMode | None = None,
        entities: list[types.MessageEntity] | None = None,
        link_preview_options: types.LinkPreviewOptions | None = None,
        reply_markup: types.InlineKeyboardMarkup = None,
    ) -> Message:
        """Bound method *edit_text* of :obj:`~pyrogram.types.Message`.

        An alias exists as *edit*.

        Use as a shortcut for:

        .. code-block:: python

            await client.edit_message_text(
                chat_id=message.chat.id, message_id=message.id, text="hello"
            )

        Example:
            .. code-block:: python

                await message.edit_text("hello")

        Parameters:
            text (``str``):
                New text of the message.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            link_preview_options (:obj:`~pyrogram.types.LinkPreviewOptions`, *optional*):
                Options for how the link preview is generated.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

        Returns:
            On success, the edited :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.edit_message_text(
            chat_id=self.chat.id,
            message_id=self.id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            reply_markup=reply_markup,
        )

    edit = edit_text

    async def edit_caption(
        self,
        caption: str,
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        reply_markup: types.InlineKeyboardMarkup = None,
    ) -> Message:
        """Bound method *edit_caption* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.edit_message_caption(
                chat_id=message.chat.id, message_id=message.id, caption="hello"
            )

        Example:
            .. code-block:: python

                await message.edit_caption("hello")

        Parameters:
            caption (``str``):
                New caption of the message.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

        Returns:
            On success, the edited :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.edit_message_caption(
            chat_id=self.chat.id,
            message_id=self.id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            reply_markup=reply_markup,
        )

    async def edit_media(
        self,
        media: types.InputMedia,
        reply_markup: types.InlineKeyboardMarkup = None,
    ) -> Message:
        """Bound method *edit_media* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.edit_message_media(
                chat_id=message.chat.id, message_id=message.id, media=media
            )

        Example:
            .. code-block:: python

                await message.edit_media(media)

        Parameters:
            media (:obj:`~pyrogram.types.InputMedia`):
                One of the InputMedia objects describing an animation, audio, document, photo or video.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

        Returns:
            On success, the edited :obj:`~pyrogram.types.Message` is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.edit_message_media(
            chat_id=self.chat.id,
            message_id=self.id,
            media=media,
            reply_markup=reply_markup,
        )

    async def edit_reply_markup(self, reply_markup: types.InlineKeyboardMarkup = None) -> Message:
        """Bound method *edit_reply_markup* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.edit_message_reply_markup(
                chat_id=message.chat.id, message_id=message.id, reply_markup=inline_reply_markup
            )

        Example:
            .. code-block:: python

                await message.edit_reply_markup(inline_reply_markup)

        Parameters:
            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`):
                An InlineKeyboardMarkup object.

        Returns:
            On success, if edited message is sent by the bot, the edited
            :obj:`~pyrogram.types.Message` is returned, otherwise True is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.edit_message_reply_markup(
            chat_id=self.chat.id, message_id=self.id, reply_markup=reply_markup
        )

    async def forward(
        self,
        chat_id: int | str,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        schedule_date: datetime | None = None,
    ) -> types.Message | list[types.Message]:
        """Bound method *forward* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.forward_messages(
                chat_id=chat_id, from_chat_id=message.chat.id, message_ids=message.id
            )

        Example:
            .. code-block:: python

                await message.forward(chat_id)

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_thread_id (``int``, *optional*):
                Unique identifier of a message thread to which the message belongs; for supergroups only

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

        Returns:
            On success, the forwarded Message is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.forward_messages(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            from_chat_id=self.chat.id,
            message_ids=self.id,
            disable_notification=disable_notification,
            schedule_date=schedule_date,
        )

    async def copy(
        self,
        chat_id: int | str,
        caption: str | None = None,
        message_thread_id: int | None = None,
        parse_mode: enums.ParseMode | None = None,
        caption_entities: list[types.MessageEntity] | None = None,
        show_caption_above_media: bool | None = None,
        disable_notification: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = object,
    ) -> types.Message | list[types.Message]:
        """Bound method *copy* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.copy_message(
                chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.id
            )

        Example:
            .. code-block:: python

                await message.copy(chat_id)

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            caption (``string``, *optional*):
                New caption for media, 0-1024 characters after entities parsing.
                If not specified, the original caption is kept.
                Pass "" (empty string) to remove the caption.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the new caption, which can be specified instead of *parse_mode*.

            show_caption_above_media (``bool``, *optional*):
                Pass True if the caption should be shown above the media.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.
                If not specified, the original reply markup is kept.
                Pass None to remove the reply markup.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the copied message is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if self.service:
            log.warning(
                "Service messages cannot be copied. chat_id: %s, message_id: %s",
                self.chat.id,
                self.id,
            )
            return None
        if self.game and not await self._client.storage.is_bot():
            log.warning(
                "Users cannot send messages with Game media type. chat_id: %s, message_id: %s",
                self.chat.id,
                self.id,
            )
            return None
        if self.empty:
            log.warning("Empty messages cannot be copied.")
            return None
        if self.text:
            return await self._client.send_message(
                chat_id,
                text=self.text,
                entities=self.entities,
                parse_mode=enums.ParseMode.DISABLED,
                link_preview_options=types.LinkPreviewOptions(is_disabled=not self.web_page),
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                reply_parameters=reply_parameters,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_markup=self.reply_markup if reply_markup is object else reply_markup,
            )
        if self.media:
            send_media = partial(
                self._client.send_cached_media,
                chat_id=chat_id,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                reply_parameters=reply_parameters,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_markup=self.reply_markup if reply_markup is object else reply_markup,
            )

            if self.photo:
                file_id = self.photo.file_id
            elif self.audio:
                file_id = self.audio.file_id
            elif self.document:
                file_id = self.document.file_id
            elif self.video:
                file_id = self.video.file_id
            elif self.animation:
                file_id = self.animation.file_id
            elif self.voice:
                file_id = self.voice.file_id
            elif self.sticker:
                file_id = self.sticker.file_id
            elif self.video_note:
                file_id = self.video_note.file_id
            elif self.contact:
                return await self._client.send_contact(
                    chat_id,
                    phone_number=self.contact.phone_number,
                    first_name=self.contact.first_name,
                    last_name=self.contact.last_name,
                    vcard=self.contact.vcard,
                    disable_notification=disable_notification,
                    message_thread_id=message_thread_id,
                    schedule_date=schedule_date,
                )
            elif self.location:
                return await self._client.send_location(
                    chat_id,
                    latitude=self.location.latitude,
                    longitude=self.location.longitude,
                    disable_notification=disable_notification,
                    message_thread_id=message_thread_id,
                    schedule_date=schedule_date,
                )
            elif self.venue:
                return await self._client.send_venue(
                    chat_id,
                    latitude=self.venue.location.latitude,
                    longitude=self.venue.location.longitude,
                    title=self.venue.title,
                    address=self.venue.address,
                    foursquare_id=self.venue.foursquare_id,
                    foursquare_type=self.venue.foursquare_type,
                    disable_notification=disable_notification,
                    message_thread_id=message_thread_id,
                    schedule_date=schedule_date,
                )
            elif self.poll:
                return await self._client.send_poll(
                    chat_id,
                    question=self.poll.question,
                    options=[opt.text for opt in self.poll.options],
                    disable_notification=disable_notification,
                    message_thread_id=message_thread_id,
                    schedule_date=schedule_date,
                )
            elif self.game:
                return await self._client.send_game(
                    chat_id,
                    game_short_name=self.game.short_name,
                    disable_notification=disable_notification,
                    message_thread_id=message_thread_id,
                )
            else:
                raise ValueError("Unknown media type")

            if self.sticker or self.video_note:
                return await send_media(file_id=file_id, message_thread_id=message_thread_id)

            if caption is None:
                caption = self.caption or ""
                caption_entities = self.caption_entities

            return await send_media(
                file_id=file_id,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                message_thread_id=message_thread_id,
            )
        raise ValueError("Can't copy this message")

    async def delete(self, revoke: bool = True):
        """Bound method *delete* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.delete_messages(chat_id=chat_id, message_ids=message.id)

        Example:
            .. code-block:: python

                await message.delete()

        Parameters:
            revoke (``bool``, *optional*):
                Deletes messages on both parts.
                This is only for private cloud chats and normal groups, messages on
                channels and supergroups are always revoked (i.e.: deleted for everyone).
                Defaults to True.

        Returns:
            True on success, False otherwise.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.delete_messages(
            chat_id=self.chat.id, message_ids=self.id, revoke=revoke
        )

    async def click(
        self,
        x: int | str = 0,
        y: int | None = None,
        quote: bool | None = None,
        timeout: int = 10,
    ):
        """Bound method *click* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for clicking a button attached to the message instead of:

        - Clicking inline buttons:

        .. code-block:: python

            await client.request_callback_answer(
                chat_id=message.chat.id,
                message_id=message.id,
                callback_data=message.reply_markup[i][j].callback_data,
            )

        - Clicking normal buttons:

        .. code-block:: python

            await client.send_message(
                chat_id=message.chat.id, text=message.reply_markup[i][j].text
            )

        Example:
            This method can be used in three different ways:

            1.  Pass one integer argument only (e.g.: ``.click(2)``, to click a button at index 2).
                Buttons are counted left to right, starting from the top.

            2.  Pass two integer arguments (e.g.: ``.click(1, 0)``, to click a button at position (1, 0)).
                The origin (0, 0) is top-left.

            3.  Pass one string argument only (e.g.: ``.click("Settings")``, to click a button by using its label).
                Only the first matching button will be pressed.

        Parameters:
            x (``int`` | ``str``):
                Used as integer index, integer abscissa (in pair with y) or as string label.
                Defaults to 0 (first button).

            y (``int``, *optional*):
                Used as ordinate only (in pair with x).

            quote (``bool``, *optional*):
                Useful for normal buttons only, where pressing it will result in a new message sent.
                If ``True``, the message will be sent as a reply to this message.
                Defaults to ``True`` in group chats and ``False`` in private chats.

            timeout (``int``, *optional*):
                Timeout in seconds.

        Returns:
            -   The result of :meth:`~pyrogram.Client.request_callback_answer` in case of inline callback button clicks.
            -   The result of :meth:`~Message.reply()` in case of normal button clicks.
            -   A string in case the inline button is a URL, a *switch_inline_query* or a
                *switch_inline_query_current_chat* button.

        Raises:
            RPCError: In case of a Telegram RPC error.
            ValueError: In case the provided index or position is out of range or the button label was not found.
            TimeoutError: In case, after clicking an inline button, the bot fails to answer within the timeout.
        """

        if isinstance(self.reply_markup, types.ReplyKeyboardMarkup):
            keyboard = self.reply_markup.keyboard
            is_inline = False
        elif isinstance(self.reply_markup, types.InlineKeyboardMarkup):
            keyboard = self.reply_markup.inline_keyboard
            is_inline = True
        else:
            raise ValueError("The message doesn't contain any keyboard")

        if isinstance(x, int) and y is None:
            try:
                button = [button for row in keyboard for button in row][x]
            except IndexError as e:
                raise ValueError(f"The button at index {x} doesn't exist") from e
        elif isinstance(x, int) and isinstance(y, int):
            try:
                button = keyboard[y][x]
            except IndexError as e:
                raise ValueError(f"The button at position ({x}, {y}) doesn't exist") from e
        elif isinstance(x, str) and y is None:
            label = x.encode("utf-16", "surrogatepass").decode("utf-16")

            try:
                button = next(button for row in keyboard for button in row if label == button.text)
            except IndexError as e:
                raise ValueError(f"The button with label '{x}' doesn't exists") from e
        else:
            raise ValueError("Invalid arguments")

        if is_inline:
            if button.callback_data:
                return await self._client.request_callback_answer(
                    chat_id=self.chat.id,
                    message_id=self.id,
                    callback_data=button.callback_data,
                    timeout=timeout,
                )
            if button.url:
                return button.url
            if button.switch_inline_query:
                return button.switch_inline_query
            if button.switch_inline_query_current_chat:
                return button.switch_inline_query_current_chat
            raise ValueError("This button is not supported yet")
        await self.reply(button, quote=quote)
        return None

    async def react(self, emoji: str = "", big: bool = False) -> bool:
        """Bound method *react* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.send_reaction(chat_id=chat_id, message_id=message.id, emoji="🔥")

        Example:
            .. code-block:: python

                await message.react(emoji="🔥")

        Parameters:
            emoji (``str``, *optional*):
                Reaction emoji.
                Pass "" as emoji (default) to retract the reaction.

            big (``bool``, *optional*):
                Pass True to show a bigger and longer reaction.
                Defaults to False.

        Returns:
            ``bool``: On success, True is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.send_reaction(
            chat_id=self.chat.id, message_id=self.id, emoji=emoji, big=big
        )

    async def retract_vote(
        self,
    ) -> types.Poll:
        """Bound method *retract_vote* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            client.retract_vote(
                chat_id=message.chat.id,
                message_id=message_id,
            )

        Example:
            .. code-block:: python

                message.retract_vote()

        Returns:
            :obj:`~pyrogram.types.Poll`: On success, the poll with the retracted vote is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.retract_vote(chat_id=self.chat.id, message_id=self.id)

    async def download(
        self,
        file_name: str = "",
        in_memory: bool = False,
        block: bool = True,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> str:
        """Bound method *download* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.download_media(message)

        Example:
            .. code-block:: python

                await message.download()

        Parameters:
            file_name (``str``, *optional*):
                A custom *file_name* to be used instead of the one provided by Telegram.
                By default, all files are downloaded in the *downloads* folder in your working directory.
                You can also specify a path for downloading files in a custom location: paths that end with "/"
                are considered directories. All non-existent folders will be created automatically.

            in_memory (``bool``, *optional*):
                Pass True to download the media in-memory.
                A binary file-like object with its attribute ".name" set will be returned.
                Defaults to False.

            block (``bool``, *optional*):
                Blocks the code execution until the file has been downloaded.
                Defaults to True.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            On success, the absolute path of the downloaded file as string is returned, None otherwise.

        Raises:
            RPCError: In case of a Telegram RPC error.
            ``ValueError``: If the message doesn't contain any downloadable media
        """
        return await self._client.download_media(
            message=self,
            file_name=file_name,
            in_memory=in_memory,
            block=block,
            progress=progress,
            progress_args=progress_args,
        )

    async def vote(
        self,
        option: int,
    ) -> types.Poll:
        """Bound method *vote* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            client.vote_poll(chat_id=message.chat.id, message_id=message.id, option=1)

        Example:
            .. code-block:: python

                message.vote(6)

        Parameters:
            option (``int``):
                Index of the poll option you want to vote for (0 to 9).

        Returns:
            :obj:`~pyrogram.types.Poll`: On success, the poll with the chosen option is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.vote_poll(
            chat_id=self.chat.id, message_id=self.id, options=option
        )

    async def pin(
        self, disable_notification: bool = False, both_sides: bool = False
    ) -> types.Message:
        """Bound method *pin* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.pin_chat_message(chat_id=message.chat.id, message_id=message_id)

        Example:
            .. code-block:: python

                await message.pin()

        Parameters:
            disable_notification (``bool``):
                Pass True, if it is not necessary to send a notification to all chat members about the new pinned
                message. Notifications are always disabled in channels.

            both_sides (``bool``, *optional*):
                Pass True to pin the message for both sides (you and recipient).
                Applicable to private chats only. Defaults to False.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the service message is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.pin_chat_message(
            chat_id=self.chat.id,
            message_id=self.id,
            disable_notification=disable_notification,
            both_sides=both_sides,
        )

    async def unpin(self) -> bool:
        """Bound method *unpin* of :obj:`~pyrogram.types.Message`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unpin_chat_message(chat_id=message.chat.id, message_id=message_id)

        Example:
            .. code-block:: python

                await message.unpin()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.unpin_chat_message(chat_id=self.chat.id, message_id=self.id)
