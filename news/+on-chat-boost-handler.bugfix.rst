``@on_chat_boost`` registered a ``ShippingQueryHandler`` rather than a ``ChatBoostHandler``, so the
decorated callback would never have fired for a boost and would have fired for shipping queries
instead. The bug came in with the ported decorator and was caught by a test asserting every
decorator registers its own handler.
