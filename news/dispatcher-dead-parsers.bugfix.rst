Fixed five dispatcher update parsers that raised on every update they were
routed. ``callback_query_parser`` passed four arguments to a three-argument
``CallbackQuery._parse``, killing every inline-keyboard button press;
``CallbackQuery._parse`` read ``game_short_name`` off business callback queries,
which do not carry it; ``parse_deleted_messages`` read ``messages`` off
``UpdateDeleteEphemeralMessages``, which names the field ``ids``;
``deleted_business_messages_parser`` awaited a synchronous parser; and the
``Poll`` and ``Story`` parsers iterated raw fields that are optional in the
schema and arrive as ``None``. Every one of these was swallowed by the handler
worker, so the symptom was an update type that silently never fired.
