:meth:`Chat._parse_chat` now returns ``None`` for a missing peer instead of raising
``AttributeError``. Callers routinely look a peer up in the ``users``/``chats`` maps that arrive
with an update and pass the result straight in; a miss yields ``None``, which fell through to the
channel parser. :meth:`User._parse` already behaved this way.
