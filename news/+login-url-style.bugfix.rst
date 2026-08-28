Fixed :obj:`~pyrogram.types.InlineKeyboardButton` silently dropping ``style`` and
``icon_custom_emoji_id`` on buttons that use ``login_url``. ``LoginUrl.write()`` accepted no style
argument, so the value computed by the caller was discarded for that branch alone.
