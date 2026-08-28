Added the 31 shared value types that the remaining API-surface work depends on: the gift cluster
(:obj:`~pyrogram.types.Gift`, :obj:`~pyrogram.types.GiftAttribute`,
:obj:`~pyrogram.types.GiftAuction`, the auction states, resale prices, purchase limits and upgraded
gift rarities), :obj:`~pyrogram.types.Folder` and :obj:`~pyrogram.types.FolderInviteLink`,
:obj:`~pyrogram.types.Invoice` and :obj:`~pyrogram.types.LabeledPrice`,
:obj:`~pyrogram.types.SuggestedPostParameters` with its price variants,
:obj:`~pyrogram.types.FormattedText` and :obj:`~pyrogram.types.Birthday`.

``utils.parse_text_with_entities`` was added alongside them - the read-side counterpart to
``parse_text_entities``, turning a received ``TextWithEntities`` into text plus high-level entities.
