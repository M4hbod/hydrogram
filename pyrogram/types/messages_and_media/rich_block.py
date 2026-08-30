#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import Literal

import pyrogram
from pyrogram import raw, types
from pyrogram.file_id import FileId
from pyrogram.types.object import Object


def _get_ordered_list_label(num: int, list_type: Literal["a", "A", "i", "I", "1"]) -> str:
    if list_type in {"a", "A"} and num > 0:
        result = ""
        temp_num = num

        while temp_num > 0:
            temp_num -= 1
            result = chr(ord("A" if list_type == "A" else "a") + temp_num % 26) + result
            temp_num //= 26

        return result + "."

    if list_type in {"i", "I"} and num > 0 and num < 4000:
        val = [
            (1000, "M"),
            (900, "CM"),
            (500, "D"),
            (400, "CD"),
            (100, "C"),
            (90, "XC"),
            (50, "L"),
            (40, "XL"),
            (10, "X"),
            (9, "IX"),
            (5, "V"),
            (4, "IV"),
            (1, "I"),
        ]

        result = ""

        for value, numeral in val:
            count = int(num / value)
            result += numeral * count
            num -= value * count

        if list_type == "i":
            result = result.lower()

        return result + "."

    return f"{num}."


class RichBlock(Object):
    """This object represents a block in a rich formatted message.

    It can be one of:

    - :obj:`~pyrogram.types.RichBlockCaption`
    - :obj:`~pyrogram.types.RichBlockTableCell`
    - :obj:`~pyrogram.types.RichBlockListItem`
    - :obj:`~pyrogram.types.RichBlockParagraph`
    - :obj:`~pyrogram.types.RichBlockSectionHeading`
    - :obj:`~pyrogram.types.RichBlockPreformatted`
    - :obj:`~pyrogram.types.RichBlockFooter`
    - :obj:`~pyrogram.types.RichBlockDivider`
    - :obj:`~pyrogram.types.RichBlockMathematicalExpression`
    - :obj:`~pyrogram.types.RichBlockAnchor`
    - :obj:`~pyrogram.types.RichBlockList`
    - :obj:`~pyrogram.types.RichBlockBlockQuotation`
    - :obj:`~pyrogram.types.RichBlockPullQuotation`
    - :obj:`~pyrogram.types.RichBlockCollage`
    - :obj:`~pyrogram.types.RichBlockSlideshow`
    - :obj:`~pyrogram.types.RichBlockTable`
    - :obj:`~pyrogram.types.RichBlockDetails`
    - :obj:`~pyrogram.types.RichBlockMap`
    - :obj:`~pyrogram.types.RichBlockAnimation`
    - :obj:`~pyrogram.types.RichBlockAudio`
    - :obj:`~pyrogram.types.RichBlockPhoto`
    - :obj:`~pyrogram.types.RichBlockVideo`
    - :obj:`~pyrogram.types.RichBlockVoiceNote`
    - :obj:`~pyrogram.types.RichBlockThinking`
    - :obj:`~pyrogram.types.RichBlockUnsupported`
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    async def _parse(
        client: pyrogram.Client,
        rich_block: raw.base.PageBlock,
        photos: dict[int, raw.base.Photo] | None = None,
        documents: dict[int, raw.base.Document] | None = None,
        part: bool | None = None,
        users: dict[int, raw.base.User] | None = None,
        chats: dict[int, raw.base.Chat] | None = None,
    ) -> RichBlock:
        # A mutable default argument is shared between calls; normalise here instead.
        photos = photos or {}
        documents = documents or {}
        users = users or {}
        chats = chats or {}

        if isinstance(rich_block, raw.types.PageBlockParagraph):
            return RichBlockParagraph(
                text=await types.RichText._parse(client, rich_block.text),
            )
        if isinstance(rich_block, raw.types.PageBlockHeading1):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=1
            )
        if isinstance(rich_block, raw.types.PageBlockHeading2):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=2
            )
        if isinstance(rich_block, raw.types.PageBlockHeading3):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=3
            )
        if isinstance(rich_block, raw.types.PageBlockHeading4):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=4
            )
        if isinstance(rich_block, raw.types.PageBlockHeading5):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=5
            )
        if isinstance(rich_block, raw.types.PageBlockHeading6):
            return RichBlockSectionHeading(
                text=await types.RichText._parse(client, rich_block.text), size=6
            )
        if isinstance(rich_block, raw.types.PageBlockPreformatted):
            return RichBlockPreformatted(
                text=await types.RichText._parse(client, rich_block.text),
                language=rich_block.language,
            )
        if isinstance(rich_block, raw.types.PageBlockFooter):
            return RichBlockFooter(
                text=await types.RichText._parse(client, rich_block.text),
            )
        if isinstance(rich_block, raw.types.PageBlockDivider):
            return RichBlockDivider()
        if isinstance(rich_block, raw.types.PageBlockMath):
            return RichBlockMathematicalExpression(expression=rich_block.source)
        if isinstance(rich_block, raw.types.PageBlockAnchor):
            return RichBlockAnchor(name=rich_block.name)
        if isinstance(rich_block, raw.types.PageBlockList):
            return RichBlockList(
                items=types.List([
                    await types.RichBlockListItem._parse(client, i) for i in rich_block.items
                ])
            )
        if isinstance(rich_block, raw.types.PageBlockOrderedList):
            return RichBlockList(
                items=types.List([
                    await types.RichBlockListItem._parse(client, i) for i in rich_block.items
                ])
            )
        if isinstance(rich_block, raw.types.PageBlockBlockquoteBlocks):
            return RichBlockBlockQuotation(
                blocks=types.List([
                    await types.RichBlock._parse(client, i, photos, documents, part, users, chats)
                    for i in rich_block.blocks
                ]),
                credit=await types.RichText._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockBlockquote):
            return RichBlockBlockQuotation(
                blocks=types.List([
                    RichBlockParagraph(text=await types.RichText._parse(client, rich_block.text))
                ]),
                credit=await types.RichText._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockPullquote):
            return RichBlockPullQuotation(
                text=await types.RichText._parse(client, rich_block.text),
                credit=await types.RichText._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockCollage):
            return RichBlockCollage(
                blocks=types.List([
                    await types.RichBlock._parse(client, i, photos, documents, part, users, chats)
                    for i in rich_block.items
                ]),
                caption=await types.RichBlockCaption._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockSlideshow):
            return RichBlockSlideshow(
                blocks=types.List([
                    await types.RichBlock._parse(client, i, photos, documents, part, users, chats)
                    for i in rich_block.items
                ]),
                caption=await types.RichBlockCaption._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockTable):
            return await RichBlockTable._parse(client, rich_block)
        if isinstance(rich_block, raw.types.PageBlockDetails):
            return RichBlockDetails(
                summary=await types.RichText._parse(client, rich_block.title),
                blocks=types.List([
                    await types.RichBlock._parse(client, i, photos, documents, part, users, chats)
                    for i in rich_block.blocks
                ]),
                is_open=rich_block.open,
            )
        if isinstance(rich_block, raw.types.PageBlockMap):
            return RichBlockMap(
                location=types.Location._parse(rich_block.geo),
                zoom=rich_block.zoom,
                width=rich_block.w,
                height=rich_block.h,
                caption=await types.RichBlockCaption._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockVideo):
            doc = documents.get(rich_block.video_id)
            attributes = {type(i): i for i in doc.attributes}

            file_name = getattr(
                attributes.get(raw.types.DocumentAttributeFilename), "file_name", None
            )

            if raw.types.DocumentAttributeAnimated in attributes:
                video_attributes = attributes.get(raw.types.DocumentAttributeVideo)

                return RichBlockAnimation(
                    animation=types.Animation._parse(client, doc, video_attributes, file_name),
                    has_spoiler=rich_block.spoiler,
                    caption=await types.RichBlockCaption._parse(client, rich_block.caption),
                )
            if raw.types.DocumentAttributeVideo in attributes:
                video_attributes = attributes[raw.types.DocumentAttributeVideo]

                return RichBlockVideo(
                    video=types.Video._parse(client, doc, video_attributes, file_name),
                    has_spoiler=rich_block.spoiler,
                    caption=await types.RichBlockCaption._parse(client, rich_block.caption),
                )
            if raw.types.DocumentAttributeAudio in attributes:
                audio_attributes = attributes[raw.types.DocumentAttributeAudio]

                if audio_attributes.voice:
                    return RichBlockVoiceNote(
                        voice_note=types.Voice._parse(client, doc, audio_attributes),
                        caption=await types.RichBlockCaption._parse(client, rich_block.caption),
                    )
                return RichBlockAudio(
                    audio=types.Audio._parse(client, doc, audio_attributes, file_name),
                    caption=await types.RichBlockCaption._parse(client, rich_block.caption),
                )
        if isinstance(rich_block, raw.types.PageBlockAudio):
            doc = documents.get(rich_block.audio_id)
            attributes = {type(i): i for i in doc.attributes}

            file_name = getattr(
                attributes.get(raw.types.DocumentAttributeFilename), "file_name", None
            )

            audio_attributes = attributes[raw.types.DocumentAttributeAudio]

            return RichBlockAudio(
                audio=types.Audio._parse(client, doc, audio_attributes, file_name),
                caption=await types.RichBlockCaption._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockPhoto):
            return RichBlockPhoto(
                photo=types.Photo._parse(client, photos.get(rich_block.photo_id)),
                has_spoiler=rich_block.spoiler,
                caption=await types.RichBlockCaption._parse(client, rich_block.caption),
            )
        if isinstance(rich_block, raw.types.PageBlockThinking):
            return RichBlockThinking(text=await types.RichText._parse(client, rich_block.text))

        # if isinstance(rich_block, raw.types.PageBlockAuthorDate):
        # if isinstance(rich_block, raw.types.PageBlockChannel):
        # if isinstance(rich_block, raw.types.PageBlockCover):
        # if isinstance(rich_block, raw.types.PageBlockEmbed):
        # if isinstance(rich_block, raw.types.PageBlockEmbedPost):
        # if isinstance(rich_block, raw.types.PageBlockHeader):
        # if isinstance(rich_block, raw.types.PageBlockKicker):
        # if isinstance(rich_block, raw.types.PageBlockRelatedArticles):
        # if isinstance(rich_block, raw.types.PageBlockSubheader):
        # if isinstance(rich_block, raw.types.PageBlockSubtitle):
        # if isinstance(rich_block, raw.types.PageBlockTitle):
        # if isinstance(rich_block, raw.types.PageBlockUnsupported):

        return RichBlockUnsupported()

    @staticmethod
    def _write(block: RichBlock, media: RichMessageMedia):
        """Serialise one block back to a ``PageBlock``.

        The inverse of :meth:`_parse`, and the same shape: a single dispatcher.
        ``media`` collects the photo and document vectors, because a block
        references its media by id and the ids live on the message.

        The return is unannotated for the same reason as
        :meth:`RichText._write`: ``raw.base.PageBlock`` is a marker class, not
        the union of the constructors it documents.
        """
        write_text = types.RichText._write

        if isinstance(block, RichBlockParagraph):
            return raw.types.PageBlockParagraph(text=write_text(block.text))

        if isinstance(block, RichBlockSectionHeading):
            headings = (
                raw.types.PageBlockHeading1,
                raw.types.PageBlockHeading2,
                raw.types.PageBlockHeading3,
                raw.types.PageBlockHeading4,
                raw.types.PageBlockHeading5,
                raw.types.PageBlockHeading6,
            )
            size = block.size or 1
            if not 1 <= size <= len(headings):
                raise ValueError(f"Heading size must be between 1 and {len(headings)}, got {size}")
            return headings[size - 1](text=write_text(block.text))

        if isinstance(block, RichBlockPreformatted):
            return raw.types.PageBlockPreformatted(
                text=write_text(block.text), language=block.language or ""
            )

        if isinstance(block, RichBlockFooter):
            return raw.types.PageBlockFooter(text=write_text(block.text))

        if isinstance(block, RichBlockDivider):
            return raw.types.PageBlockDivider()

        if isinstance(block, RichBlockAnchor):
            return raw.types.PageBlockAnchor(name=block.name)

        if isinstance(block, RichBlockMathematicalExpression):
            return raw.types.PageBlockMath(source=block.expression)

        if isinstance(block, RichBlockThinking):
            return raw.types.PageBlockThinking(text=write_text(block.text))

        if isinstance(block, RichBlockList):
            items = block.items or []
            # One RichBlockList covers both raw list kinds; an item that carries
            # a number or a label type is what makes the list an ordered one.
            ordered = any(i.value is not None or i.type is not None for i in items)
            if ordered:
                return raw.types.PageBlockOrderedList(
                    items=[RichBlock._write_ordered_list_item(i, media) for i in items]
                )
            return raw.types.PageBlockList(
                items=[RichBlock._write_list_item(i, media) for i in items]
            )

        if isinstance(block, RichBlockBlockQuotation):
            return raw.types.PageBlockBlockquoteBlocks(
                blocks=[RichBlock._write(b, media) for b in block.blocks or []],
                caption=write_text(block.credit),
            )

        if isinstance(block, RichBlockPullQuotation):
            return raw.types.PageBlockPullquote(
                text=write_text(block.text), caption=write_text(block.credit)
            )

        if isinstance(block, RichBlockCollage):
            return raw.types.PageBlockCollage(
                items=[RichBlock._write(b, media) for b in block.blocks or []],
                caption=RichBlockCaption._write_caption(block.caption),
            )

        if isinstance(block, RichBlockSlideshow):
            return raw.types.PageBlockSlideshow(
                items=[RichBlock._write(b, media) for b in block.blocks or []],
                caption=RichBlockCaption._write_caption(block.caption),
            )

        if isinstance(block, RichBlockTable):
            return raw.types.PageBlockTable(
                # _parse wraps the raw `title` in a caption; unwrap it again.
                title=write_text(block.caption.text if block.caption else None),
                rows=[
                    raw.types.PageTableRow(
                        cells=[RichBlockTableCell._write_cell(cell) for cell in row or []]
                    )
                    for row in block.cells or []
                ],
                bordered=block.is_bordered or None,
                striped=block.is_striped or None,
            )

        if isinstance(block, RichBlockDetails):
            return raw.types.PageBlockDetails(
                blocks=[RichBlock._write(b, media) for b in block.blocks or []],
                title=write_text(block.summary),
                open=block.is_open or None,
            )

        if isinstance(block, RichBlockPhoto):
            return raw.types.PageBlockPhoto(
                photo_id=media.photo(block.photo),
                caption=RichBlockCaption._write_caption(block.caption),
                spoiler=block.has_spoiler or None,
            )

        if isinstance(block, (RichBlockVideo, RichBlockAnimation)):
            source = block.video if isinstance(block, RichBlockVideo) else block.animation
            return raw.types.PageBlockVideo(
                video_id=media.document(source),
                caption=RichBlockCaption._write_caption(block.caption),
                spoiler=block.has_spoiler or None,
            )

        if isinstance(block, (RichBlockAudio, RichBlockVoiceNote)):
            source = block.audio if isinstance(block, RichBlockAudio) else block.voice_note
            return raw.types.PageBlockAudio(
                audio_id=media.document(source),
                caption=RichBlockCaption._write_caption(block.caption),
            )

        raise ValueError(f"Cannot send {type(block).__name__} as a rich message block")

    @staticmethod
    def _write_list_item(item: RichBlockListItem, media: RichMessageMedia):
        return raw.types.PageListItemBlocks(
            blocks=[RichBlock._write(b, media) for b in item.blocks or []],
            checkbox=item.has_checkbox or None,
            checked=item.is_checked or None,
        )

    @staticmethod
    def _write_ordered_list_item(item: RichBlockListItem, media: RichMessageMedia):
        return raw.types.PageListOrderedItemBlocks(
            blocks=[RichBlock._write(b, media) for b in item.blocks or []],
            num=item.label,
            value=item.value,
            type=item.type,
            checkbox=item.has_checkbox or None,
            checked=item.is_checked or None,
        )


class RichMessageMedia:
    """The photo and document vectors a rich message carries.

    A ``PageBlock`` names its media by id, and the ids are only resolvable
    through the ``photos`` and ``documents`` vectors on the message itself, so
    the blocks and the message have to be built together.
    """

    def __init__(self) -> None:
        self.photos: list[raw.types.InputPhoto] = []
        self.documents: list[raw.types.InputDocument] = []

    @staticmethod
    def _decode(value: str | Object) -> FileId:
        file_id = value if isinstance(value, str) else getattr(value, "file_id", None)
        if not file_id:
            raise ValueError(
                f"Expected a file id or an object carrying one, got {type(value).__name__}"
            )
        return FileId.decode(file_id)

    def photo(self, value: str | Object) -> int:
        decoded = self._decode(value)
        self.photos.append(
            raw.types.InputPhoto(
                id=decoded.media_id,
                access_hash=decoded.access_hash,
                file_reference=decoded.file_reference,
            )
        )
        return decoded.media_id

    def document(self, value: str | Object) -> int:
        decoded = self._decode(value)
        self.documents.append(
            raw.types.InputDocument(
                id=decoded.media_id,
                access_hash=decoded.access_hash,
                file_reference=decoded.file_reference,
            )
        )
        return decoded.media_id


class RichBlockUnsupported(RichBlock):
    """A rich block unsupported yet."""

    def __init__(
        self,
    ):
        super().__init__()


class RichBlockCaption(RichBlock):
    """Caption of a rich formatted block.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Block caption.

        credit (:obj:`~pyrogram.types.RichText`, *optional*):
            Block credit which corresponds to the HTML tag <cite>.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
        credit: str | list[types.RichText] | types.RichText | None = None,
    ):
        super().__init__()

        self.text = text
        self.credit = credit

    @staticmethod
    async def _parse(client, caption: raw.base.PageCaption) -> RichBlockCaption | None:
        if caption is not None:
            return RichBlockCaption(
                text=await types.RichText._parse(client, caption.text),
                credit=await types.RichText._parse(client, caption.credit),
            )
        return None

    @staticmethod
    def _write_caption(caption: RichBlockCaption | None) -> raw.types.PageCaption:
        # Both halves are required by the schema, so an absent caption is still
        # a PageCaption, just an empty one.
        if caption is None:
            return raw.types.PageCaption(text=raw.types.TextEmpty(), credit=raw.types.TextEmpty())
        return raw.types.PageCaption(
            text=types.RichText._write(caption.text),
            credit=types.RichText._write(caption.credit),
        )
        return None


class RichBlockTableCell(RichBlock):
    """Cell in a table.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`, *optional*):
            Text in the cell.
            If omitted, then the cell is invisible.

        is_header (``bool``, *optional*):
            True, if the cell is a header cell.

        colspan (``int``, *optional*):
            The number of columns the cell spans if it is bigger than 1.

        rowspan (``int``, *optional*):
            The number of rows the cell spans if it is bigger than 1.

        align (``str``, *optional*):
            Horizontal cell content alignment.
            Currently, must be one of "left", "center", or "right".

        valign (``str``, *optional*):
            Vertical cell content alignment.
            Currently, must be one of "top", "middle", or "bottom".
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None = None,
        is_header: bool | None = None,
        colspan: int | None = None,
        rowspan: int | None = None,
        align: str | None = None,
        valign: str | None = None,
    ):
        super().__init__()

        self.text = text
        self.is_header = is_header
        self.colspan = colspan
        self.rowspan = rowspan
        self.align = align
        self.valign = valign

    @staticmethod
    async def _parse(client, table_cell: raw.base.PageTableCell):
        align = "left"
        if table_cell.align_center:
            align = "center"
        elif table_cell.align_right:
            align = "right"

        valign = "top"
        if table_cell.valign_middle:
            valign = "middle"
        elif table_cell.valign_bottom:
            valign = "bottom"

        return RichBlockTableCell(
            text=await types.RichText._parse(client, table_cell.text),
            is_header=table_cell.header,
            colspan=max(table_cell.colspan or 1, 1),
            rowspan=max(table_cell.rowspan or 1, 1),
            align=align,
            valign=valign,
        )

    @staticmethod
    def _write_cell(cell: RichBlockTableCell) -> raw.types.PageTableCell:
        # "left" and "top" are the defaults, carried by the absence of a flag.
        return raw.types.PageTableCell(
            text=types.RichText._write(cell.text) if cell.text is not None else None,
            header=cell.is_header or None,
            align_center=cell.align == "center" or None,
            align_right=cell.align == "right" or None,
            valign_middle=cell.valign == "middle" or None,
            valign_bottom=cell.valign == "bottom" or None,
            colspan=cell.colspan if (cell.colspan or 1) > 1 else None,
            rowspan=cell.rowspan if (cell.rowspan or 1) > 1 else None,
        )


class RichBlockListItem(RichBlock):
    """An item of a list.

    Parameters:
        label (``str``):
            Label of the item.

        blocks (List of :obj:`pyrogram.types.RichBlock`):
            The content of the item.

        has_checkbox (``bool``, *optional*):
            True, if the item has a checkbox.

        is_checked (``bool``, *optional*):
            True, if the item has a checked checkbox.

        value (``int``, *optional*):
            For ordered lists, the numeric value of the item label.

        type (``str``, *optional*):
            For ordered lists, the type of the item label.
            Must be one of "a" for lowercase letters, "A" for uppercase letters,
            "i" for lowercase Roman numerals, "I" for uppercase Roman numerals,
            or "1" for decimal numbers.
    """

    def __init__(
        self,
        label: str,
        blocks: list[types.RichBlock],
        has_checkbox: bool | None = None,
        is_checked: bool | None = None,
        value: int | None = None,
        type: str | None = None,
    ):
        super().__init__()

        self.label = label
        self.blocks = blocks
        self.has_checkbox = has_checkbox
        self.is_checked = is_checked
        self.value = value
        self.type = type

    @staticmethod
    async def _parse(client, list_item: raw.base.PageListItem | raw.base.PageListOrderedItem):
        if isinstance(list_item, raw.types.PageListItemBlocks):
            blocks = types.List([
                await types.RichBlock._parse(client, block) for block in list_item.blocks
            ])
            label = "•"
            has_checkbox = list_item.checkbox
            is_checked = list_item.checked
            value = None
            item_type = None

        elif isinstance(list_item, raw.types.PageListItemText):
            blocks = types.List([
                types.RichBlockParagraph(text=await types.RichText._parse(client, list_item.text))
            ])
            label = "•"
            has_checkbox = list_item.checkbox
            is_checked = list_item.checked
            value = None
            item_type = None

        elif isinstance(list_item, raw.types.PageListOrderedItemBlocks):
            blocks = types.List([
                await types.RichBlock._parse(client, block) for block in list_item.blocks
            ])
            has_checkbox = list_item.checkbox
            is_checked = list_item.checked
            value = list_item.value
            item_type = list_item.type or "1"

            if value is not None:
                label = _get_ordered_list_label(value, item_type)
            else:
                label = list_item.num

        elif isinstance(list_item, raw.types.PageListOrderedItemText):
            blocks = types.List([
                types.RichBlockParagraph(text=await types.RichText._parse(client, list_item.text))
            ])
            has_checkbox = list_item.checkbox
            is_checked = list_item.checked
            value = list_item.value
            item_type = list_item.type or "1"

            if value is not None:
                label = _get_ordered_list_label(value, item_type)
            else:
                label = list_item.num
        else:
            return None

        return RichBlockListItem(
            label=label,
            blocks=blocks,
            has_checkbox=has_checkbox,
            is_checked=is_checked,
            value=value,
            type=item_type,
        )


class RichBlockParagraph(RichBlock):
    """A text paragraph, corresponding to the HTML tag ``<p>``.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
    ):
        super().__init__()

        self.text = text


class RichBlockSectionHeading(RichBlock):
    """A section heading, corresponding to the HTML tags ``<h1>``, ``<h2>``, ``<h3>``, ``<h4>``, ``<h5>``, or ``<h6>``.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.

        size (``int``):
            Relative size of the text font, 1-6.
            1 is the largest, 6 is the smallest.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
        size: int,
    ):
        super().__init__()

        self.text = text
        self.size = size


class RichBlockPreformatted(RichBlock):
    """A preformatted text block, corresponding to the nested HTML tags ``<pre>`` and ``<code>``.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.

        language (``str``, *optional*):
            The programming language of the text.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
        language: str | None = None,
    ):
        super().__init__()

        self.text = text
        self.language = language


class RichBlockFooter(RichBlock):
    """A footer, corresponding to the HTML tag ``<footer>``.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.
    """

    def __init__(self, text: str | list[types.RichText] | types.RichText | None):
        super().__init__()

        self.text = text


class RichBlockDivider(RichBlock):
    """A divider, corresponding to the HTML tag ``<hr/>``."""

    def __init__(self):
        super().__init__()


class RichBlockMathematicalExpression(RichBlock):
    """A block with a mathematical expression in LaTeX format, corresponding to the custom HTML tag ``<tg-math-block>``.

    Parameters:
        expression (``str``):
            The mathematical expression in LaTeX format.
    """

    def __init__(self, expression: str):
        super().__init__()

        self.expression = expression


class RichBlockAnchor(RichBlock):
    """A block with an anchor, corresponding to the HTML tag ``<a>`` with the attribute ``name``.

    Parameters:
        name (``str``):
            The name of the anchor.
    """

    def __init__(self, name: str):
        super().__init__()

        self.name = name


class RichBlockList(RichBlock):
    """A list of blocks, corresponding to the HTML tag ``<ul>`` or ``<ol>`` with multiple nested tags ``<li>``.

    Parameters:
        items (List of :obj:`pyrogram.types.RichBlockListItem`):
            Items of the list.
    """

    def __init__(self, items: list[types.RichBlockListItem]):
        super().__init__()

        self.items = items


class RichBlockBlockQuotation(RichBlock):
    """A block quotation, corresponding to the HTML tag ``<blockquote>``.

    Parameters:
        blocks (List of :obj:`pyrogram.types.RichBlock`):
            Content of the block.

        credit (:obj:`~pyrogram.types.RichText`, *optional*):
            Credit of the block.
    """

    def __init__(self, blocks: list[types.RichBlock], credit: types.RichText | None = None):
        super().__init__()

        self.blocks = blocks
        self.credit = credit


class RichBlockPullQuotation(RichBlock):
    """A quotation with centered text, loosely corresponding to the HTML tag ``<aside>``.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.

        credit (:obj:`~pyrogram.types.RichText`, *optional*):
            Credit of the block.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
        credit: str | list[types.RichText] | types.RichText | None = None,
    ):
        super().__init__()

        self.text = text
        self.credit = credit


class RichBlockCollage(RichBlock):
    """A collage, corresponding to the custom HTML tag ``<tg-collage>``.

    Parameters:
        blocks (List of :obj:`~pyrogram.types.RichBlock`):
            Elements of the collage.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self, blocks: list[types.RichBlock], caption: types.RichBlockCaption | None = None
    ):
        super().__init__()

        self.blocks = blocks
        self.caption = caption


class RichBlockSlideshow(RichBlock):
    """A slideshow, corresponding to the custom HTML tag ``<tg-slideshow>``.

    Parameters:
        blocks (List of :obj:`~pyrogram.types.RichBlock`):
            Elements of the slideshow.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self, blocks: list[types.RichBlock], caption: types.RichBlockCaption | None = None
    ):
        super().__init__()

        self.blocks = blocks
        self.caption = caption


class RichBlockTable(RichBlock):
    """A table, corresponding to the HTML tag ``<table>``.

    Parameters:
        cells (List of List of :obj:`~pyrogram.types.RichBlockTableCell`):
            Cells of the table.

        is_bordered (``bool``, *optional*):
            True, if the table has borders.

        is_striped (``bool``, *optional*):
            True, if the table is striped.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self,
        cells: list[list[types.RichBlockTableCell]],
        is_bordered: bool | None = None,
        is_striped: bool | None = None,
        caption: types.RichBlockCaption | None = None,
    ):
        super().__init__()

        self.cells = cells
        self.is_bordered = is_bordered
        self.is_striped = is_striped
        self.caption = caption

    @staticmethod
    async def _parse(client, page_block: raw.types.PageBlockTable):
        cells = []

        if page_block.rows:
            for row in page_block.rows:
                row_cells = []
                if row.cells:
                    for table_cell in row.cells:
                        cell = await RichBlockTableCell._parse(client, table_cell)
                        row_cells.append(cell)

                if row_cells:
                    cells.append(row_cells)

        # The raw field is `title`, a bare RichText, but `caption` is typed as a
        # RichBlockCaption like every other block's, so wrap it rather than
        # handing back a shape the annotation does not describe.
        title = await types.RichText._parse(client, page_block.title)

        return RichBlockTable(
            cells=cells,
            is_bordered=page_block.bordered,
            is_striped=page_block.striped,
            caption=types.RichBlockCaption(text=title) if title is not None else None,
        )


class RichBlockDetails(RichBlock):
    """An expandable block for details disclosure, corresponding to the HTML tag ``<details>``.

    Parameters:
        summary (:obj:`~pyrogram.types.RichText`):
            Always shown summary of the block.

        blocks (List of :obj:`~pyrogram.types.RichBlock`):
            Content of the block.

        is_open (``bool``, *optional*):
            True, if the content of the block is visible by default.
    """

    def __init__(
        self,
        summary: str | list[types.RichText] | types.RichText | None,
        blocks: list[types.RichBlock],
        is_open: bool | None = None,
    ):
        super().__init__()

        self.summary = summary
        self.blocks = blocks
        self.is_open = is_open


class RichBlockMap(RichBlock):
    """A block with a map, corresponding to the custom HTML tag ``<tg-map>``.

    Parameters:
        location (:obj:`~pyrogram.types.Location`):
            Location of the center of the map.

        zoom (``int``):
            Map zoom level, 13-20.

        width (``int``):
            Expected width of the map.

        height (``int``):
            Expected height of the map.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self,
        location: types.Location,
        zoom: int,
        width: int,
        height: int,
        caption: types.RichBlockCaption | None = None,
    ):
        super().__init__()

        self.location = location
        self.zoom = zoom
        self.width = width
        self.height = height
        self.caption = caption


class RichBlockAnimation(RichBlock):
    """A block with an animation, corresponding to the HTML tag ``<video>``.

    Parameters:
        animation (:obj:`~pyrogram.types.Animation`):
            The animation.

        has_spoiler (``bool``, *optional*):
            True, if the media preview is covered by a spoiler animation.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self,
        animation: types.Animation,
        has_spoiler: bool | None = None,
        caption: types.RichBlockCaption | None = None,
    ):
        super().__init__()

        self.animation = animation
        self.has_spoiler = has_spoiler
        self.caption = caption


class RichBlockAudio(RichBlock):
    """A block with a music file, corresponding to the HTML tag ``<audio>``.

    Parameters:
        audio (:obj:`~pyrogram.types.Audio`):
            The audio.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(self, audio: types.Audio, caption: types.RichBlockCaption | None = None):
        super().__init__()

        self.audio = audio
        self.caption = caption


class RichBlockPhoto(RichBlock):
    """A block with a photo, corresponding to the HTML tag ``<photo>``.

    Parameters:
        photo (:obj:`~pyrogram.types.Photo`):
            The photo.

        has_spoiler (``bool``, *optional*):
            True, if the media preview is covered by a spoiler animation.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self,
        photo: types.Photo,
        has_spoiler: bool | None = None,
        caption: types.RichBlockCaption | None = None,
    ):
        super().__init__()

        self.photo = photo
        self.has_spoiler = has_spoiler
        self.caption = caption


class RichBlockVideo(RichBlock):
    """A block with a video, corresponding to the HTML tag ``<video>``.

    Parameters:
        video (:obj:`~pyrogram.types.Video`):
            The video.

        has_spoiler (``bool``, *optional*):
            True, if the media preview is covered by a spoiler animation.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(
        self,
        video: types.Video,
        has_spoiler: bool | None = None,
        caption: types.RichBlockCaption | None = None,
    ):
        super().__init__()

        self.video = video
        self.has_spoiler = has_spoiler
        self.caption = caption


class RichBlockVoiceNote(RichBlock):
    """A block with a voice note, corresponding to the HTML tag ``<audio>``.

    Parameters:
        voice_note (:obj:`~pyrogram.types.Voice`):
            The voice note.

        has_spoiler (``bool``, *optional*):
            True, if the media preview is covered by a spoiler animation.

        caption (:obj:`~pyrogram.types.RichBlockCaption`, *optional*):
            Caption of the block.
    """

    def __init__(self, voice_note: types.Voice, caption: types.RichBlockCaption | None = None):
        super().__init__()

        self.voice_note = voice_note
        self.caption = caption


class RichBlockThinking(RichBlock):
    """A block with a "Thinking..." placeholder, corresponding to the custom HTML tag ``<tg-thinking>``.
    The block may be used only in :meth:`~pyrogram.Client.send_rich_message_draft`, therefore it can't be received in messages.
    See https://t.me/addemoji/AIActions for examples of custom emoji, which are recommended for usage in the block.

    Parameters:
        text (:obj:`~pyrogram.types.RichText`):
            Text of the block.
            See https://t.me/addemoji/AIActions for examples of custom emoji, which are recommended for usage in the block.
    """

    def __init__(
        self,
        text: str | list[types.RichText] | types.RichText | None,
    ):
        super().__init__()

        self.text = text
