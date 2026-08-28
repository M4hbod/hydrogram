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

from .on_business_connection import OnBusinessConnection as OnBusinessConnection
from .on_business_message import OnBusinessMessage as OnBusinessMessage
from .on_callback_query import OnCallbackQuery
from .on_chat_boost import OnChatBoost as OnChatBoost
from .on_chat_join_request import OnChatJoinRequest
from .on_chat_member_updated import OnChatMemberUpdated
from .on_chosen_inline_result import OnChosenInlineResult
from .on_connect import OnConnect as OnConnect
from .on_deleted_business_messages import OnDeletedBusinessMessages as OnDeletedBusinessMessages
from .on_deleted_messages import OnDeletedMessages
from .on_disconnect import OnDisconnect
from .on_edited_business_message import OnEditedBusinessMessage as OnEditedBusinessMessage
from .on_edited_message import OnEditedMessage
from .on_error import OnError
from .on_guest_message import OnGuestMessage as OnGuestMessage
from .on_inline_query import OnInlineQuery
from .on_managed_bot import OnManagedBot as OnManagedBot
from .on_message import OnMessage
from .on_message_reaction import OnMessageReaction as OnMessageReaction
from .on_message_reaction_count import OnMessageReactionCount as OnMessageReactionCount
from .on_poll import OnPoll
from .on_pre_checkout_query import OnPreCheckoutQuery as OnPreCheckoutQuery
from .on_purchased_paid_media import OnPurchasedPaidMedia as OnPurchasedPaidMedia
from .on_raw_update import OnRawUpdate
from .on_shipping_query import OnShippingQuery as OnShippingQuery
from .on_start import OnStart as OnStart
from .on_stop import OnStop as OnStop
from .on_story import OnStory as OnStory
from .on_user_status import OnUserStatus


class Decorators(  # noqa: N818 false-positive
    OnMessage,
    OnEditedMessage,
    OnDeletedMessages,
    OnCallbackQuery,
    OnRawUpdate,
    OnDisconnect,
    OnUserStatus,
    OnInlineQuery,
    OnPoll,
    OnChosenInlineResult,
    OnChatMemberUpdated,
    OnChatJoinRequest,
    OnError,
    OnBusinessConnection,
    OnBusinessMessage,
    OnChatBoost,
    OnConnect,
    OnDeletedBusinessMessages,
    OnEditedBusinessMessage,
    OnGuestMessage,
    OnManagedBot,
    OnMessageReaction,
    OnMessageReactionCount,
    OnPreCheckoutQuery,
    OnPurchasedPaidMedia,
    OnShippingQuery,
    OnStart,
    OnStop,
    OnStory,
):
    pass
