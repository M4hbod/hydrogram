**Breaking.** Dates returned by the library are now timezone-aware UTC.

:func:`~pyrogram.utils.timestamp_to_datetime` -- and therefore every date on a parsed object, such
as ``Message.date`` and ``Message.edit_date`` -- previously returned a *naive local* datetime while
:func:`~pyrogram.utils.zero_datetime` returned an aware UTC one. The two could not be compared:
checking a message date against the library's own default for ``until_date`` or ``offset_date``
raised ``TypeError: can't compare offset-naive and offset-aware datetimes``.

Telegram sends dates as Unix timestamps, which are instants rather than wall-clock readings, so the
aware form is the accurate one. Code that compares a message date against a naive datetime now
raises ``TypeError`` instead of silently working; use ``datetime.now(timezone.utc)`` in place of
``datetime.now()``, or call ``.astimezone()`` on the message date to render it locally.

Datetimes *passed to* the library are unchanged: an aware one converts exactly, and a naive one is
still read as local time, matching ``datetime.now()``.
