Corrected the documentation for :obj:`~pyrogram.types.InlineKeyboardButton`'s ``style`` and
``icon_custom_emoji_id``. Both were documented as requiring the bot owner to have Telegram Premium.
Verified against production Telegram from a non-Premium bot owner: ``style`` works and has no such
requirement, while ``icon_custom_emoji_id`` is accepted and then **silently dropped** by the server
-- the message sends without error and the button reads back with no icon.
