**Breaking.** ``reply_to_message_id`` and ``disable_web_page_preview`` are removed from every send
and edit method, replaced by :obj:`~pyrogram.types.ReplyParameters` and
:obj:`~pyrogram.types.LinkPreviewOptions`. There are no deprecation shims: passing the old names
raises ``TypeError``.

The exhaustive list, so the downstream sweep is a grep:

* ``reply_to_message_id=N`` becomes ``reply_parameters=ReplyParameters(message_id=N)``. Affects
  ``send_message``, ``send_photo``, ``send_audio``, ``send_document``, ``send_sticker``,
  ``send_video``, ``send_animation``, ``send_voice``, ``send_video_note``, ``send_location``,
  ``send_venue``, ``send_contact``, ``send_dice``, ``send_poll``, ``send_media_group``,
  ``send_cached_media``, ``send_game``, ``send_inline_bot_result``, ``copy_message``,
  ``copy_media_group``, and the 18 ``Message.reply_*`` bound methods.
* ``disable_web_page_preview=True`` becomes
  ``link_preview_options=LinkPreviewOptions(is_disabled=True)``. Affects ``send_message``,
  ``edit_message_text``, ``edit_inline_text``, :obj:`~pyrogram.types.InputTextMessageContent` and
  ``CallbackQuery.edit_message_text``.

Two things that keep the old spelling and are **not** affected: the ``Message.reply_to_message_id``
attribute, which describes an incoming message, and ``get_messages(reply_to_message_ids=...)``,
which fetches replies.

The replacements do more than the parameters they retire. ``ReplyParameters`` can quote a substring
at a given UTF-16 position, and can reply to a story, an ephemeral message, a checklist task or a
poll option. ``LinkPreviewOptions`` can choose which URL is previewed, prefer a larger or smaller
image, and place the preview above the text -- a message with an explicit preview URL is now sent
through ``messages.sendMedia`` with an ``InputMediaWebPage``, which is the only way to express it.
