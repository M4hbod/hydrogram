``ForumTopicCreated._parse`` read ``action`` off the raw message directly, which
raises ``AttributeError`` for anything but a service message. Two ``_parse``
annotations were also wrong in a way that hid the same class of defect:
``Chat._parse_full`` declared the un-namespaced full types while its body
handles ``raw.types.users.UserFull`` and ``raw.types.messages.ChatFull``, and
``GiftAuctionState._parse`` declared ``raw.base.StarGiftAuctionState`` where the
RPC returns ``raw.types.payments.StarGiftAuctionState``. A second check in
``test_optional_raw_fields_are_guarded`` now fails on any read of a field no
constructor the annotated input can hold declares.
