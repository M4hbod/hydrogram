What this fork changes
======================

This is a private hard fork of `Hydrogram <https://github.com/hydrogram/hydrogram>`_, which is
itself a fork of the archived `Pyrogram <https://github.com/pyrogram/pyrogram>`_. The package
directory and the import name are both ``pyrogram``, deliberately: ``py-tgcalls``, ``pykeyboard``
and other Pyrogram-only packages import it by that name.

It is not published to PyPI. Install it from git.

Breaking changes
----------------

Breaking changes are adopted outright rather than shimmed, and announced in the changelog. These
are the ones that will bite an existing Pyrogram or Hydrogram bot.

**Reply and link-preview parameters** were replaced by the Bot API 7 objects. ``reply_to_message_id``,
``reply_to_chat_id``, ``reply_to_story_id``, ``quote_text``, ``quote_entities`` and ``quote_offset``
are gone; pass a :obj:`~pyrogram.types.ReplyParameters`. ``disable_web_page_preview`` is gone; pass
a :obj:`~pyrogram.types.LinkPreviewOptions`.

.. code-block:: python

    # before
    await app.send_message(chat_id, "hi", reply_to_message_id=123, disable_web_page_preview=True)

    # now
    await app.send_message(
        chat_id,
        "hi",
        reply_parameters=ReplyParameters(message_id=123),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

Passing an old name raises ``TypeError`` rather than being silently ignored, which is the point:
nothing here pretends to accept an option it will not honour.

**Dates are timezone-aware.** Every ``datetime`` a message or type carries is UTC-aware. Comparing
one against a naive ``datetime.now()`` raises ``TypeError``; use ``datetime.now(timezone.utc)``.

**Keyboard buttons were rebuilt for layer 229.** Telegram split inline buttons off from reply
buttons into their own base type. The Python API of
:obj:`~pyrogram.types.InlineKeyboardButton` is unchanged, but it gained ``style`` and
``icon_custom_emoji_id``, and it is a different wire format underneath.

What this fork adds
-------------------

- **TL layer 229**, against Hydrogram's 223.
- **MTProxy** as a native transport -- plain, ``dd`` and ``ee`` (fake-TLS) secrets. ``Client``
  takes a ``tg://proxy`` or ``t.me/proxy`` link directly. See :doc:`topics/proxy`.
- **Update-gap recovery.** :meth:`~pyrogram.Client.recover_gaps` fetches what arrived while the
  client was offline and replays it through the normal handlers; ``skip_updates=False`` calls it
  for you.
- 443 client methods, 397 types, 121 filters and 30 handlers, matching Kurigram's surface.
- ``python-socks[asyncio]`` for SOCKS and HTTP proxies, replacing ``pysocks``, whose handshake ran
  on the event loop and blocked it.

Inherited from Hydrogram
------------------------

- Modern packaging: ``pyproject.toml``, hatchling, ``uv``.
- ``aiosqlite`` rather than ``sqlite3`` for session storage.
- ``full_name`` on :obj:`~pyrogram.types.User` and :obj:`~pyrogram.types.Chat`.
- Custom storage engines, by subclassing :obj:`~pyrogram.storage.BaseStorage`.
- Optional parameters are keyword-only, so adding one later cannot shift an existing call.
- ``towncrier`` changelogs and a Ruff-formatted tree.
