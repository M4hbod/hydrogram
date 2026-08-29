Filters that read a field off the update no longer assume it is a ``Message``.
``filters.private``/``group``/``channel`` raised ``ValueError`` on any update
that was not a ``Message`` or a ``CallbackQuery``, and ``incoming``/``outgoing``
raised ``AttributeError``; both die inside the handler worker, where they are
logged and swallowed, so the handler just never runs. Each field is now taken
only from the update types that carry it -- ``me``, ``bot``, ``incoming``,
``outgoing`` and the chat-type filters work across the whole update surface and
simply do not match where the field is absent.
