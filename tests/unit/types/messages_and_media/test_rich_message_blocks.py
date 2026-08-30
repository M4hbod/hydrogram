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

"""Sending rich messages as structured blocks.

``InputRichMessage`` could only carry HTML or Markdown, which is the thin
text-only form. The structured form is ``raw.types.InputRichMessage``, whose
``blocks`` vector is the same ``PageBlock`` union the read side already parses,
so the send side reuses the ``RichBlock`` classes rather than mirroring them.

Every test here round-trips: build blocks, write them to raw, parse them back.
A constructor that is merely well named still fails serialisation, and a block
that writes to something the parser does not recognise comes back as
``RichBlockUnsupported`` rather than raising, so both are asserted.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import pyrogram
from pyrogram import raw, types
from pyrogram.file_id import FileId, FileType, ThumbnailSource


@pytest.fixture
async def client():
    # Built inside the running loop: on Python 3.9 the client's own primitives
    # bind to a loop at construction, and a sync fixture has none.
    return pyrogram.Client("test", api_id=1, api_hash="x", in_memory=True)


@pytest.fixture
def photo_file_id():
    return FileId(
        file_type=FileType.PHOTO,
        dc_id=2,
        media_id=123456789,
        access_hash=987654321,
        file_reference=b"\x01\x02",
        volume_id=0,
        local_id=0,
        thumbnail_source=ThumbnailSource.THUMBNAIL,
        thumbnail_file_type=FileType.PHOTO,
        thumbnail_size="m",
    ).encode()


@pytest.fixture
def video_file_id():
    return FileId(
        file_type=FileType.VIDEO,
        dc_id=2,
        media_id=555,
        access_hash=666,
        file_reference=b"\x03",
    ).encode()


def write(blocks, **kwargs):
    return types.InputRichMessage(blocks=blocks, **kwargs).write()


# --- the message itself -------------------------------------------------------


def test_blocks_build_the_structured_constructor():
    written = write([types.RichBlockParagraph(text="hi")])

    assert isinstance(written, raw.types.InputRichMessage)
    assert len(written.blocks) == 1
    assert written.write(), "the constructor did not serialise"


def test_html_and_markdown_still_take_the_thin_path():
    assert isinstance(
        types.InputRichMessage(html="<b>hi</b>").write(), raw.types.InputRichMessageHTML
    )
    assert isinstance(
        types.InputRichMessage(markdown="**hi**").write(), raw.types.InputRichMessageMarkdown
    )


def test_blocks_win_over_html_when_both_are_given():
    written = types.InputRichMessage(blocks=[types.RichBlockDivider()], html="<b>x</b>").write()
    assert isinstance(written, raw.types.InputRichMessage)


def test_an_empty_rich_message_is_refused():
    with pytest.raises(ValueError, match="blocks, html or markdown"):
        types.InputRichMessage().write()


def test_the_message_flags_are_carried():
    written = write([types.RichBlockDivider()], is_rtl=True, skip_entity_detection=True)
    assert written.rtl is True
    assert written.noautolink is True


# --- block round trips --------------------------------------------------------


@pytest.mark.parametrize(
    ("block", "expected"),
    [
        (types.RichBlockParagraph(text="p"), raw.types.PageBlockParagraph),
        (types.RichBlockDivider(), raw.types.PageBlockDivider),
        (types.RichBlockAnchor(name="top"), raw.types.PageBlockAnchor),
        (types.RichBlockFooter(text="f"), raw.types.PageBlockFooter),
        (types.RichBlockThinking(text="t"), raw.types.PageBlockThinking),
        (
            types.RichBlockMathematicalExpression(expression="x^2"),
            raw.types.PageBlockMath,
        ),
        (
            types.RichBlockPreformatted(text="code", language="python"),
            raw.types.PageBlockPreformatted,
        ),
        (
            types.RichBlockPullQuotation(text="q", credit="c"),
            raw.types.PageBlockPullquote,
        ),
        (
            types.RichBlockCollage(blocks=[types.RichBlockParagraph(text="a")]),
            raw.types.PageBlockCollage,
        ),
        (
            types.RichBlockSlideshow(blocks=[types.RichBlockParagraph(text="a")]),
            raw.types.PageBlockSlideshow,
        ),
    ],
)
def test_the_block_writes_to_its_raw_constructor(block, expected):
    written = write([block])
    assert isinstance(written.blocks[0], expected)
    assert written.write()


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [1, 2, 3, 4, 5, 6])
async def test_every_heading_size_round_trips(client, size):
    written = write([types.RichBlockSectionHeading(text="h", size=size)])

    parsed = await types.RichBlock._parse(client, written.blocks[0])
    assert isinstance(parsed, types.RichBlockSectionHeading)
    assert parsed.size == size


def test_a_heading_size_outside_the_schema_is_refused():
    with pytest.raises(ValueError, match="between 1 and 6"):
        write([types.RichBlockSectionHeading(text="h", size=7)])


@pytest.mark.asyncio
async def test_a_table_round_trips_with_its_cell_geometry(client):
    table = types.RichBlockTable(
        cells=[
            [
                types.RichBlockTableCell(text="Track", is_header=True),
                types.RichBlockTableCell(text="Length", is_header=True, align="right"),
            ],
            [
                types.RichBlockTableCell(text="Intro", rowspan=2),
                types.RichBlockTableCell(text="1:02", align="center", valign="bottom"),
            ],
        ],
        is_bordered=True,
        is_striped=True,
        caption=types.RichBlockCaption(text="Tracklist"),
    )

    written = write([table]).blocks[0]
    assert isinstance(written, raw.types.PageBlockTable)
    assert written.bordered and written.striped
    assert written.rows[0].cells[0].header is True
    assert written.rows[0].cells[1].align_right is True
    assert written.rows[1].cells[0].rowspan == 2
    assert written.rows[1].cells[1].align_center is True
    assert written.rows[1].cells[1].valign_bottom is True

    parsed = await types.RichBlock._parse(client, written)
    assert isinstance(parsed, types.RichBlockTable)
    assert len(parsed.cells) == 2
    assert parsed.cells[0][0].is_header is True
    assert parsed.cells[1][0].rowspan == 2
    assert parsed.is_bordered is True


def test_a_default_aligned_cell_carries_no_flags():
    """ "left" and "top" are the schema's defaults, spelled as absent flags."""
    cell = types.RichBlockTableCell(text="x", align="left", valign="top")
    written = types.RichBlockTableCell._write_cell(cell)

    assert written.align_center is None
    assert written.align_right is None
    assert written.valign_middle is None
    assert written.valign_bottom is None
    assert written.colspan is None
    assert written.rowspan is None


@pytest.mark.asyncio
async def test_a_checklist_round_trips_its_checkboxes(client):
    checklist = types.RichBlockList(
        items=[
            types.RichBlockListItem(
                label="•",
                blocks=[types.RichBlockParagraph(text="Downloaded")],
                has_checkbox=True,
                is_checked=True,
            ),
            types.RichBlockListItem(
                label="•",
                blocks=[types.RichBlockParagraph(text="Tagged")],
                has_checkbox=True,
            ),
        ]
    )

    written = write([checklist]).blocks[0]
    assert isinstance(written, raw.types.PageBlockList)
    assert written.items[0].checkbox is True
    assert written.items[0].checked is True
    assert written.items[1].checkbox is True
    assert written.items[1].checked is None

    parsed = await types.RichBlock._parse(client, written)
    assert [(i.has_checkbox, i.is_checked) for i in parsed.items] == [(True, True), (True, None)]


def test_a_numbered_item_makes_the_list_an_ordered_one():
    ordered = types.RichBlockList(
        items=[
            types.RichBlockListItem(
                label="1.", blocks=[types.RichBlockParagraph(text="a")], value=1, type="1"
            )
        ]
    )
    plain = types.RichBlockList(
        items=[types.RichBlockListItem(label="•", blocks=[types.RichBlockParagraph(text="a")])]
    )

    assert isinstance(write([ordered]).blocks[0], raw.types.PageBlockOrderedList)
    assert isinstance(write([plain]).blocks[0], raw.types.PageBlockList)


@pytest.mark.asyncio
async def test_a_collapsible_section_round_trips(client):
    details = types.RichBlockDetails(
        summary="Details",
        blocks=[types.RichBlockParagraph(text="hidden")],
        is_open=False,
    )

    written = write([details]).blocks[0]
    assert isinstance(written, raw.types.PageBlockDetails)
    assert written.open is None

    parsed = await types.RichBlock._parse(client, written)
    assert isinstance(parsed, types.RichBlockDetails)
    assert len(parsed.blocks) == 1


@pytest.mark.asyncio
async def test_quotations_nest(client):
    quote = types.RichBlockBlockQuotation(
        blocks=[
            types.RichBlockParagraph(text="outer"),
            types.RichBlockBlockQuotation(
                blocks=[types.RichBlockParagraph(text="inner")], credit="who"
            ),
        ],
        credit="source",
    )

    written = write([quote]).blocks[0]
    assert isinstance(written, raw.types.PageBlockBlockquoteBlocks)
    assert isinstance(written.blocks[1], raw.types.PageBlockBlockquoteBlocks)

    parsed = await types.RichBlock._parse(client, written)
    assert isinstance(parsed.blocks[1], types.RichBlockBlockQuotation)


# --- media --------------------------------------------------------------------


def test_a_photo_block_lands_in_the_message_photo_vector(photo_file_id):
    written = write([
        types.RichBlockPhoto(photo=photo_file_id, caption=types.RichBlockCaption(text="cover"))
    ])

    assert written.blocks[0].photo_id == 123456789
    assert [p.id for p in written.photos] == [123456789]
    assert written.photos[0].access_hash == 987654321
    assert written.documents is None
    assert written.write()


def test_a_video_block_lands_in_the_document_vector(video_file_id):
    written = write([types.RichBlockVideo(video=video_file_id, has_spoiler=True)])

    assert written.blocks[0].video_id == 555
    assert written.blocks[0].spoiler is True
    assert [d.id for d in written.documents] == [555]
    assert written.photos is None


def test_media_may_be_given_as_an_object_carrying_a_file_id(photo_file_id):
    photo = types.Photo(
        file_id=photo_file_id,
        file_unique_id="u",
        width=1,
        height=1,
        file_size=1,
        date=None,
    )
    written = write([types.RichBlockPhoto(photo=photo)])
    assert written.blocks[0].photo_id == 123456789


def test_media_that_carries_no_file_id_is_refused():
    with pytest.raises(ValueError, match="file id"):
        write([types.RichBlockPhoto(photo=object())])


# --- rich text ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_plain_string_is_the_simplest_rich_text(client):
    written = write([types.RichBlockParagraph(text="hello")]).blocks[0]
    assert isinstance(written.text, raw.types.TextPlain)

    parsed = await types.RichBlock._parse(client, written)
    assert parsed.text == "hello"


def test_an_empty_string_writes_the_empty_constructor():
    assert isinstance(types.RichText._write(""), raw.types.TextEmpty)
    assert isinstance(types.RichText._write(None), raw.types.TextEmpty)


@pytest.mark.asyncio
async def test_a_list_of_spans_round_trips(client):
    paragraph = types.RichBlockParagraph(
        text=[
            "by ",
            types.RichTextBold(text="Artemis"),
            types.RichTextCode(text="320k"),
        ]
    )

    written = write([paragraph]).blocks[0]
    assert isinstance(written.text, raw.types.TextConcat)
    assert isinstance(written.text.texts[1], raw.types.TextBold)
    assert isinstance(written.text.texts[2], raw.types.TextFixed)

    parsed = await types.RichBlock._parse(client, written)
    assert parsed.text[0] == "by "
    assert isinstance(parsed.text[1], types.RichTextBold)
    assert isinstance(parsed.text[2], types.RichTextCode)


@pytest.mark.parametrize(
    ("span", "expected"),
    [
        (types.RichTextBold(text="x"), raw.types.TextBold),
        (types.RichTextItalic(text="x"), raw.types.TextItalic),
        (types.RichTextUnderline(text="x"), raw.types.TextUnderline),
        (types.RichTextStrikethrough(text="x"), raw.types.TextStrike),
        (types.RichTextSpoiler(text="x"), raw.types.TextSpoiler),
        (types.RichTextCode(text="x"), raw.types.TextFixed),
        (types.RichTextMarked(text="x"), raw.types.TextMarked),
        (types.RichTextSubscript(text="x"), raw.types.TextSubscript),
        (types.RichTextSuperscript(text="x"), raw.types.TextSuperscript),
        (types.RichTextHashtag(text="#x", hashtag="x"), raw.types.TextHashtag),
        (types.RichTextCashtag(text="$X", cashtag="X"), raw.types.TextCashtag),
        (types.RichTextBotCommand(text="/x", bot_command="x"), raw.types.TextBotCommand),
        (types.RichTextMention(text="@x", username="x"), raw.types.TextMention),
        (
            types.RichTextBankCardNumber(text="4111", bank_card_number="4111"),
            raw.types.TextBankCard,
        ),
        (types.RichTextUrl(text="x", url="https://t.me"), raw.types.TextUrl),
        (types.RichTextEmailAddress(text="x", email_address="a@b.c"), raw.types.TextEmail),
        (types.RichTextPhoneNumber(text="x", phone_number="+1"), raw.types.TextPhone),
        (types.RichTextMathematicalExpression(expression="x^2"), raw.types.TextMath),
        (types.RichTextAnchor(text="", name="top"), raw.types.TextAnchor),
        (types.RichTextReference(text="see", name="top"), raw.types.TextAnchor),
        (types.RichTextReferenceLink(text="see", reference_name="top"), raw.types.TextUrl),
        (types.RichTextAnchorLink(text="see", anchor_name="top"), raw.types.TextUrl),
    ],
)
def test_the_span_writes_to_its_raw_constructor(span, expected):
    written = types.RichText._write(span)
    assert isinstance(written, expected)
    # A well-named constructor still fails to serialise if a field is wrong.
    assert raw.types.PageBlockParagraph(text=written).write()


@pytest.mark.asyncio
async def test_an_anchor_target_and_a_reference_to_it_stay_distinct(client):
    """``_parse`` tells them apart by whether the anchor has text; so must ``_write``."""
    target = types.RichText._write(types.RichTextAnchor(text="", name="top"))
    reference = types.RichText._write(types.RichTextReference(text="see", name="top"))

    assert isinstance(target.text, raw.types.TextEmpty)
    assert not isinstance(reference.text, raw.types.TextEmpty)

    assert isinstance(await types.RichText._parse(client, target), types.RichTextAnchor)
    assert isinstance(await types.RichText._parse(client, reference), types.RichTextReference)


@pytest.mark.asyncio
async def test_a_reference_link_round_trips_through_its_fragment(client):
    written = types.RichText._write(
        types.RichTextReferenceLink(text="see", reference_name="tracks")
    )
    assert written.url == "#tracks"

    parsed = await types.RichText._parse(client, written)
    assert isinstance(parsed, types.RichTextReferenceLink)
    assert parsed.reference_name == "tracks"


def test_a_custom_emoji_writes_its_document_id():
    written = types.RichText._write(
        types.RichTextCustomEmoji(custom_emoji_id=5, alternative_text="x")
    )
    assert written.document_id == 5
    assert written.alt == "x"


def test_a_text_mention_writes_the_user_id():
    user = types.User(id=777)
    written = types.RichText._write(types.RichTextTextMention(text="me", user=user))
    assert written.user_id == 777


@pytest.mark.asyncio
async def test_a_date_round_trips_its_format_flags(client):
    written = types.RichText._write(
        types.RichTextDateTime(
            text="then", date=datetime(2026, 8, 31, tzinfo=timezone.utc), date_time_format="wDT"
        )
    )
    assert written.day_of_week is True
    assert written.long_date is True
    assert written.long_time is True
    assert written.short_date is None
    assert written.relative is None

    parsed = await types.RichText._parse(client, written)
    assert isinstance(parsed, types.RichTextDateTime)
    assert set(parsed.date_time_format) == {"w", "D", "T"}


def test_a_relative_date_writes_only_the_relative_flag():
    written = types.RichText._write(
        types.RichTextDateTime(
            text="then", date=datetime(2026, 8, 31, tzinfo=timezone.utc), date_time_format="r"
        )
    )
    assert written.relative is True
    assert written.long_date is None


def test_a_type_that_cannot_be_sent_says_so():
    with pytest.raises(ValueError, match="Cannot send"):
        types.RichText._write(object())

    with pytest.raises(ValueError, match="Cannot send"):
        write([types.RichBlockUnsupported()])
