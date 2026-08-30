``RichBlockTable._parse`` put a bare :obj:`~pyrogram.types.RichText` in
``caption``, which its own docstring types as a
:obj:`~pyrogram.types.RichBlockCaption` like every other block's. It now wraps
the raw ``title`` in a ``RichBlockCaption``. Code reading ``table.caption``
directly as text must now read ``table.caption.text``.
