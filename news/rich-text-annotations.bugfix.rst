The ``text``, ``summary`` and ``credit`` parameters of the
:obj:`~pyrogram.types.RichText` and :obj:`~pyrogram.types.RichBlock` classes
were annotated ``RichText``, but ``RichText`` is a union that includes ``str``
and a list of spans, which is what the parser has always passed them. The
annotations now say so.
