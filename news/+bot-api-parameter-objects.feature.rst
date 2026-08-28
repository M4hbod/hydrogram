Added :obj:`~pyrogram.types.ReplyParameters` and :obj:`~pyrogram.types.LinkPreviewOptions`, the
parameter objects that replace the flat ``reply_to_message_id`` and ``disable_web_page_preview``
arguments in the Bot API 7 model.

They are the prerequisite for that migration rather than the migration itself: the send and edit
methods still take the flat parameters for now. ``ReplyParameters`` expresses the combinations the
flat argument could not -- quoting a substring with a position, replying to a story, an ephemeral
message, a checklist task or a poll option -- and ``LinkPreviewOptions`` can choose a preview's URL
and size instead of only switching it off.
