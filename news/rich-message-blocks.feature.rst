:obj:`~pyrogram.types.InputRichMessage` now takes ``blocks``, so rich messages
can be sent in their structured form instead of only as HTML or Markdown. This
is what carries tables, lists with checkboxes, collapsible sections, headings,
anchors, nested quotations, collages and media. The blocks are the same
:obj:`~pyrogram.types.RichBlock` and :obj:`~pyrogram.types.RichText` classes
that reading a rich message already returns, so a message can be parsed, edited
and sent again rather than needing a parallel set of input types.
