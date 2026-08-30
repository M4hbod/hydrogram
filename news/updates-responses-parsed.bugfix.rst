Fifteen methods raised ``AttributeError: 'Updates' object has no attribute
'messages'`` on every call, ``send_rich_message`` among them. They passed the
result of an RPC that returns ``Updates`` straight to ``parse_messages``, which
reads a ``messages`` vector that ``Updates`` does not have. A user sending to
their own private chat gets the ``UpdateShortSentMessage`` shortcut, which the
methods did handle, so the broken branch was only ever reached by bots and in
groups. The new ``utils.parse_messages_from_updates`` reads the new messages out
of an ``Updates``, and a contract test resolves every ``parse_messages``
argument back to its RPC's declared return type.
