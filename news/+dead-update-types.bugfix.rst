Eight update types never reached their handlers. The dispatcher routed them to
``pyrogram.types.PreCheckoutQuery``, ``ShippingQuery``, ``MessageReactionUpdated``,
``MessageReactionCountUpdated``, ``ChatBoostUpdated``, ``BusinessConnection``,
``ManagedBotUpdated`` and ``PurchasedPaidMedia`` -- none of which existed, so the
``AttributeError`` was logged and swallowed by the handler worker and
``@on_pre_checkout_query`` and friends simply never fired. All eight types are
ported, and ``tests/contract/test_type_references.py`` now fails on any
``types.X`` that hand-written code names but the package does not define.
