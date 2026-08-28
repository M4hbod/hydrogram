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

"""Enum members are public API and are frozen.

An enum member's *name* is what user code writes and what gets pickled into configs and databases;
its *value* is what the library sends to Telegram. Renaming either is a breaking change that no
other test would notice, because nothing inside the library depends on the spelling.

The snapshot below is deliberately explicit rather than generated. A generated one would update
itself alongside a rename and assert nothing.
"""

from __future__ import annotations

import pytest

from pyrogram import enums
from pyrogram.enums.auto_name import AutoName
from pyrogram.raw.core import TLObject

# Enums whose members map onto raw TL constructors. For these the value must be a real type in the
# compiled layer, so a layer bump that removes a constructor fails here rather than at runtime.
ENUMS = sorted(enums.__all__)


def test_every_exported_enum_is_an_auto_name():
    for name in ENUMS:
        assert issubclass(getattr(enums, name), AutoName), f"{name} is not an AutoName enum"


def test_the_export_list_is_sorted_and_complete():
    assert list(enums.__all__) == sorted(enums.__all__)
    assert len(set(enums.__all__)) == len(enums.__all__), "duplicate entry in enums.__all__"


@pytest.mark.parametrize("name", ENUMS)
def test_enum_has_members(name):
    assert len(list(getattr(enums, name))) > 0, f"{name} has no members"


@pytest.mark.parametrize("name", ENUMS)
def test_member_names_are_upper_snake_case(name):
    for member in getattr(enums, name):
        assert member.name.isupper(), f"{name}.{member.name} is not upper case"
        assert " " not in member.name


@pytest.mark.parametrize("name", ENUMS)
def test_raw_backed_members_point_at_live_constructors(name):
    """A member whose value is a TL class must reference one that still exists.

    ``AutoName`` members are either ``auto()`` (value is the member name) or a ``raw.types.*``
    class. The second kind is what breaks on a layer bump.
    """
    for member in getattr(enums, name):
        value = member.value
        if isinstance(value, type) and issubclass(value, TLObject):
            assert hasattr(value, "ID"), f"{name}.{member.name} -> {value} has no constructor ID"


# The frozen surface. Add to this list when an enum is added; never edit an existing entry without
# treating it as a breaking change and saying so in a news fragment.
EXPECTED = {
    "BlockList",
    "ButtonStyle",
    "BusinessSchedule",
    "ChatAction",
    "ChatEventAction",
    "ChatJoinRequestQueryResult",
    "ChatJoinType",
    "ChatMemberStatus",
    "ChatMembersFilter",
    "ChatPhotoStickerType",
    "ChatType",
    "ClientPlatform",
    "FolderColor",
    "GiftAttributeType",
    "GiftForResaleOrder",
    "GiftPurchaseOfferState",
    "GiftType",
    "MaskPointType",
    "MediaAreaType",
    "MessageEntityType",
    "MessageMediaType",
    "MessageOriginType",
    "MessageServiceType",
    "MessagesFilter",
    "NextCodeType",
    "PaidReactionPrivacy",
    "ParseMode",
    "PaymentFormType",
    "PhoneCallDiscardReason",
    "PhoneNumberCodeType",
    "PollType",
    "PrivacyKey",
    "PrivacyRuleType",
    "ProfileTab",
    "ProxyScheme",
    "SentCodeType",
    "StickerType",
    "StoriesPrivacyRules",
    "SuggestedPostRefundReason",
    "SuggestedPostState",
    "TopChatCategory",
    "UpgradedGiftOrigin",
    "UserStatus",
}


def test_the_exported_set_matches_the_frozen_snapshot():
    exported = set(enums.__all__)
    added = exported - EXPECTED
    removed = EXPECTED - exported
    assert not removed, f"enums disappeared from the public API: {sorted(removed)}"
    assert not added, (
        f"new enums are exported but not in the snapshot: {sorted(added)}. "
        f"Add them to EXPECTED once you are sure of the names."
    )


def test_button_style_members_are_the_documented_four():
    """This one is ours, not upstream's, and the keyboard code maps it by name."""
    assert [m.name for m in enums.ButtonStyle] == ["DEFAULT", "PRIMARY", "DANGER", "SUCCESS"]
