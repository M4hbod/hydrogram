Fixed two parsers that crashed on ordinary traffic by iterating a raw field the
schema marks optional. ``Thumbnail._parse`` iterated ``Document.thumbs``, so
every document without a thumbnail raised ``TypeError``, and
``ChatPreview._parse`` iterated ``ChatInvite.participants``, so every invite
without a member preview did the same. A new contract test,
``test_optional_raw_fields_are_guarded``, resolves raw attribute chains against
the generated schema across the whole package and fails on any unguarded
iteration of an optional field.
