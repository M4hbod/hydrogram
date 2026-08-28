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
from .contact import Contact
from .dice import Dice
from .document import Document
from .formatted_text import FormattedText
from .game import Game
from .gift import Gift
from .gift_attribute import GiftAttribute
from .gift_auction import GiftAuction
from .gift_auction_state import GiftAuctionState
from .gift_purchase_limit import GiftPurchaseLimit
from .gift_resale_parameters import GiftResaleParameters
from .gift_resale_price import GiftResalePrice, GiftResalePriceStar, GiftResalePriceTon
from .invoice import Invoice
from .link_preview_options import LinkPreviewOptions
from .location import Location
from .message import Message
from .message_entity import MessageEntity
from .message_reactions import MessageReactions
from .photo import Photo
from .poll import Poll
from .poll_option import PollOption
from .reaction import Reaction
from .reply_parameters import ReplyParameters
from .sticker import Sticker
from .stripped_thumbnail import StrippedThumbnail
from .suggested_post_parameters import SuggestedPostParameters
from .suggested_post_price import SuggestedPostPrice, SuggestedPostPriceStar, SuggestedPostPriceTon
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
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from .web_app_data import WebAppData
from .web_page import WebPage

__all__ = [
    "Animation",
    "AuctionBid",
    "AuctionRound",
    "AuctionState",
    "AuctionStateActive",
    "AuctionStateFinished",
    "Audio",
    "Contact",
    "Dice",
    "Document",
    "FormattedText",
    "Game",
    "Gift",
    "GiftAttribute",
    "GiftAuction",
    "GiftAuctionState",
    "GiftPurchaseLimit",
    "GiftResaleParameters",
    "GiftResalePrice",
    "GiftResalePriceStar",
    "GiftResalePriceTon",
    "Invoice",
    "LinkPreviewOptions",
    "Location",
    "Message",
    "MessageEntity",
    "MessageReactions",
    "Photo",
    "Poll",
    "PollOption",
    "Reaction",
    "ReplyParameters",
    "Sticker",
    "StrippedThumbnail",
    "SuggestedPostParameters",
    "SuggestedPostPrice",
    "SuggestedPostPriceStar",
    "SuggestedPostPriceTon",
    "Thumbnail",
    "UpgradedGiftAttributeRarity",
    "UpgradedGiftAttributeRarityEpic",
    "UpgradedGiftAttributeRarityLegendary",
    "UpgradedGiftAttributeRarityPerMille",
    "UpgradedGiftAttributeRarityRare",
    "UpgradedGiftAttributeRarityUncommon",
    "UpgradedGiftOriginalDetails",
    "Venue",
    "Video",
    "VideoNote",
    "Voice",
    "WebAppData",
    "WebPage",
]
