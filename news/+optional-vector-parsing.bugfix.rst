Fixed crashes parsing users, chats and messages that omit a flags-gated vector.
``User._parse`` and ``Chat._parse_*`` iterated ``usernames`` and ``restriction_reason``
unconditionally, and ``Message`` did the same with ``entities`` - all of which are absent rather
than empty for the many peers and messages that have none. ``getattr(obj, "field", [])`` was also
used in nine places where it cannot work: the attribute exists and holds ``None``, so the default
never applies.
