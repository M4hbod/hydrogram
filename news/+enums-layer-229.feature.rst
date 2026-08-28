Added 28 enums, taking the public set from 15 to 43: ``BlockList``, ``BusinessSchedule``,
``ChatJoinRequestQueryResult``, ``ChatJoinType``, ``ChatPhotoStickerType``, ``ClientPlatform``,
``FolderColor``, ``GiftAttributeType``, ``GiftForResaleOrder``, ``GiftPurchaseOfferState``,
``GiftType``, ``MaskPointType``, ``MediaAreaType``, ``MessageOriginType``, ``PaidReactionPrivacy``,
``PaymentFormType``, ``PhoneCallDiscardReason``, ``PhoneNumberCodeType``, ``PrivacyKey``,
``PrivacyRuleType``, ``ProfileTab``, ``ProxyScheme``, ``StickerType``, ``StoriesPrivacyRules``,
``SuggestedPostRefundReason``, ``SuggestedPostState``, ``TopChatCategory`` and
``UpgradedGiftOrigin``.

These are the value types the remaining API-surface work depends on. Enum member names and values
are now frozen by a snapshot test, since renaming either is a breaking change nothing else would
catch.
