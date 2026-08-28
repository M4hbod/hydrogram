:meth:`str` on a type that keeps its source MTProto object no longer dumps it. Several types
(:obj:`~pyrogram.types.Gift`, :obj:`~pyrogram.types.Invoice`, :obj:`~pyrogram.types.Folder`) hold
the raw constructor they were parsed from as an escape hatch; it is enormous, it is an
implementation detail, and it can carry fields the wrapper deliberately masks. ``Object.default``
now hides it, as it already masked ``phone_number``.
