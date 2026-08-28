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

from .animation import Animation
from .auction_bid import AuctionBid
from .auction_round import AuctionRound
from .auction_state import AuctionState, AuctionStateActive, AuctionStateFinished
from .audio import Audio
from .chat_has_protected_content_disable_requested import ChatHasProtectedContentDisableRequested
from .chat_has_protected_content_toggled import ChatHasProtectedContentToggled
from .chat_owner_changed import ChatOwnerChanged
from .chat_owner_left import ChatOwnerLeft
from .chat_theme import ChatTheme
from .checklist import Checklist
from .checklist_task import ChecklistTask
from .checklist_tasks_added import ChecklistTasksAdded
from .checklist_tasks_done import ChecklistTasksDone
from .community_chat_added import CommunityChatAdded
from .community_chat_removed import CommunityChatRemoved
from .contact import Contact
from .contact_registered import ContactRegistered
from .dice import Dice
from .direct_message_price_changed import DirectMessagePriceChanged
from .document import Document
from .external_reply_info import ExternalReplyInfo
from .fact_check import FactCheck
from .formatted_text import FormattedText
from .game import Game
from .general_forum_topic_hidden import GeneralForumTopicHidden
from .general_forum_topic_unhidden import GeneralForumTopicUnhidden
from .gift import Gift
from .gift_attribute import GiftAttribute
from .gift_auction import GiftAuction
from .gift_auction_state import GiftAuctionState
from .gift_purchase_limit import GiftPurchaseLimit
from .gift_resale_parameters import GiftResaleParameters
from .gift_resale_price import GiftResalePrice, GiftResalePriceStar, GiftResalePriceTon
from .gifted_premium import GiftedPremium
from .gifted_stars import GiftedStars
from .gifted_ton import GiftedTon
from .giveaway import Giveaway
from .giveaway_completed import GiveawayCompleted
from .giveaway_created import GiveawayCreated
from .giveaway_prize_stars import GiveawayPrizeStars
from .giveaway_winners import GiveawayWinners
from .input_checklist_task import InputChecklistTask
from .invoice import Invoice
from .link_preview_options import LinkPreviewOptions
from .live_photo import LivePhoto
from .location import Location
from .managed_bot_created import ManagedBotCreated
from .media_area import MediaArea
from .message import Message
from .message_entity import MessageEntity
from .message_origin import MessageOrigin
from .message_origin_channel import MessageOriginChannel
from .message_origin_chat import MessageOriginChat
from .message_origin_hidden_user import MessageOriginHiddenUser
from .message_origin_import import MessageOriginImport
from .message_origin_user import MessageOriginUser
from .message_reactions import MessageReactions
from .paid_media_info import PaidMediaInfo
from .paid_media_preview import PaidMediaPreview
from .paid_messages_price_changed import PaidMessagesPriceChanged
from .paid_messages_refunded import PaidMessagesRefunded
from .payment_result import PaymentResult
from .photo import Photo
from .poll import Poll
from .poll_option import PollOption
from .poll_option_added import PollOptionAdded
from .poll_option_deleted import PollOptionDeleted
from .premium_gift_code import PremiumGiftCode
from .proximity_alert_triggered import ProximityAlertTriggered
from .reaction import Reaction
from .refunded_payment import RefundedPayment
from .reply_parameters import ReplyParameters
from .restriction_reason import RestrictionReason
from .rich_block import (
    RichBlock,
    RichBlockAnchor,
    RichBlockAnimation,
    RichBlockAudio,
    RichBlockBlockQuotation,
    RichBlockCaption,
    RichBlockCollage,
    RichBlockDetails,
    RichBlockDivider,
    RichBlockFooter,
    RichBlockList,
    RichBlockListItem,
    RichBlockMap,
    RichBlockMathematicalExpression,
    RichBlockParagraph,
    RichBlockPhoto,
    RichBlockPreformatted,
    RichBlockPullQuotation,
    RichBlockSectionHeading,
    RichBlockSlideshow,
    RichBlockTable,
    RichBlockTableCell,
    RichBlockThinking,
    RichBlockUnsupported,
    RichBlockVideo,
    RichBlockVoiceNote,
)
from .rich_message import RichMessage
from .rich_text import (
    RichText,
    RichTextAnchor,
    RichTextAnchorLink,
    RichTextBankCardNumber,
    RichTextBold,
    RichTextBotCommand,
    RichTextCashtag,
    RichTextCode,
    RichTextCustomEmoji,
    RichTextDateTime,
    RichTextEmailAddress,
    RichTextHashtag,
    RichTextItalic,
    RichTextMarked,
    RichTextMathematicalExpression,
    RichTextMention,
    RichTextPhoneNumber,
    RichTextReference,
    RichTextReferenceLink,
    RichTextSpoiler,
    RichTextStrikethrough,
    RichTextSubscript,
    RichTextSuperscript,
    RichTextTextMention,
    RichTextUnderline,
    RichTextUrl,
)
from .screenshot_taken import ScreenshotTaken
from .star_amount import StarAmount
from .sticker import Sticker
from .story import Story
from .stripped_thumbnail import StrippedThumbnail
from .successful_payment import SuccessfulPayment
from .suggested_post_approval_failed import SuggestedPostApprovalFailed
from .suggested_post_approved import SuggestedPostApproved
from .suggested_post_declined import SuggestedPostDeclined
from .suggested_post_info import SuggestedPostInfo
from .suggested_post_paid import SuggestedPostPaid
from .suggested_post_parameters import SuggestedPostParameters
from .suggested_post_price import SuggestedPostPrice, SuggestedPostPriceStar, SuggestedPostPriceTon
from .suggested_post_refunded import SuggestedPostRefunded
from .text_quote import TextQuote
from .thumbnail import Thumbnail
from .upgraded_gift_attribute_rarity import (
    UpgradedGiftAttributeRarity,
    UpgradedGiftAttributeRarityEpic,
    UpgradedGiftAttributeRarityLegendary,
    UpgradedGiftAttributeRarityPerMille,
    UpgradedGiftAttributeRarityRare,
    UpgradedGiftAttributeRarityUncommon,
)
from .upgraded_gift_original_details import UpgradedGiftOriginalDetails
from .upgraded_gift_purchase_offer import (
    UpgradedGiftPurchaseOffer,
    UpgradedGiftPurchaseOfferRejected,
)
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from .web_app_data import WebAppData
from .web_page import WebPage
from .write_access_allowed import WriteAccessAllowed

__all__ = [
    "Animation",
    "AuctionBid",
    "AuctionRound",
    "AuctionState",
    "AuctionStateActive",
    "AuctionStateFinished",
    "Audio",
    "ChatHasProtectedContentDisableRequested",
    "ChatHasProtectedContentToggled",
    "ChatOwnerChanged",
    "ChatOwnerLeft",
    "ChatTheme",
    "Checklist",
    "ChecklistTask",
    "ChecklistTasksAdded",
    "ChecklistTasksDone",
    "CommunityChatAdded",
    "CommunityChatRemoved",
    "Contact",
    "ContactRegistered",
    "Dice",
    "DirectMessagePriceChanged",
    "Document",
    "ExternalReplyInfo",
    "FactCheck",
    "FormattedText",
    "Game",
    "GeneralForumTopicHidden",
    "GeneralForumTopicUnhidden",
    "Gift",
    "GiftAttribute",
    "GiftAuction",
    "GiftAuctionState",
    "GiftPurchaseLimit",
    "GiftResaleParameters",
    "GiftResalePrice",
    "GiftResalePriceStar",
    "GiftResalePriceTon",
    "GiftedPremium",
    "GiftedStars",
    "GiftedTon",
    "Giveaway",
    "GiveawayCompleted",
    "GiveawayCreated",
    "GiveawayPrizeStars",
    "GiveawayWinners",
    "InputChecklistTask",
    "Invoice",
    "LinkPreviewOptions",
    "LivePhoto",
    "Location",
    "ManagedBotCreated",
    "MediaArea",
    "Message",
    "MessageEntity",
    "MessageOrigin",
    "MessageOriginChannel",
    "MessageOriginChat",
    "MessageOriginHiddenUser",
    "MessageOriginImport",
    "MessageOriginUser",
    "MessageReactions",
    "PaidMediaInfo",
    "PaidMediaPreview",
    "PaidMessagesPriceChanged",
    "PaidMessagesRefunded",
    "PaymentResult",
    "Photo",
    "Poll",
    "PollOption",
    "PollOptionAdded",
    "PollOptionDeleted",
    "PremiumGiftCode",
    "ProximityAlertTriggered",
    "Reaction",
    "RefundedPayment",
    "ReplyParameters",
    "RestrictionReason",
    "RichBlock",
    "RichBlockAnchor",
    "RichBlockAnimation",
    "RichBlockAudio",
    "RichBlockBlockQuotation",
    "RichBlockCaption",
    "RichBlockCollage",
    "RichBlockDetails",
    "RichBlockDivider",
    "RichBlockFooter",
    "RichBlockList",
    "RichBlockListItem",
    "RichBlockMap",
    "RichBlockMathematicalExpression",
    "RichBlockParagraph",
    "RichBlockPhoto",
    "RichBlockPreformatted",
    "RichBlockPullQuotation",
    "RichBlockSectionHeading",
    "RichBlockSlideshow",
    "RichBlockTable",
    "RichBlockTableCell",
    "RichBlockThinking",
    "RichBlockUnsupported",
    "RichBlockVideo",
    "RichBlockVoiceNote",
    "RichMessage",
    "RichText",
    "RichTextAnchor",
    "RichTextAnchorLink",
    "RichTextBankCardNumber",
    "RichTextBold",
    "RichTextBotCommand",
    "RichTextCashtag",
    "RichTextCode",
    "RichTextCustomEmoji",
    "RichTextDateTime",
    "RichTextEmailAddress",
    "RichTextHashtag",
    "RichTextItalic",
    "RichTextMarked",
    "RichTextMathematicalExpression",
    "RichTextMention",
    "RichTextPhoneNumber",
    "RichTextReference",
    "RichTextReferenceLink",
    "RichTextSpoiler",
    "RichTextStrikethrough",
    "RichTextSubscript",
    "RichTextSuperscript",
    "RichTextTextMention",
    "RichTextUnderline",
    "RichTextUrl",
    "ScreenshotTaken",
    "StarAmount",
    "Sticker",
    "Story",
    "StrippedThumbnail",
    "SuccessfulPayment",
    "SuggestedPostApprovalFailed",
    "SuggestedPostApproved",
    "SuggestedPostDeclined",
    "SuggestedPostInfo",
    "SuggestedPostPaid",
    "SuggestedPostParameters",
    "SuggestedPostPrice",
    "SuggestedPostPriceStar",
    "SuggestedPostPriceTon",
    "SuggestedPostRefunded",
    "TextQuote",
    "Thumbnail",
    "UpgradedGiftAttributeRarity",
    "UpgradedGiftAttributeRarityEpic",
    "UpgradedGiftAttributeRarityLegendary",
    "UpgradedGiftAttributeRarityPerMille",
    "UpgradedGiftAttributeRarityRare",
    "UpgradedGiftAttributeRarityUncommon",
    "UpgradedGiftOriginalDetails",
    "UpgradedGiftPurchaseOffer",
    "UpgradedGiftPurchaseOfferRejected",
    "Venue",
    "Video",
    "VideoNote",
    "Voice",
    "WebAppData",
    "WebPage",
    "WriteAccessAllowed",
]
