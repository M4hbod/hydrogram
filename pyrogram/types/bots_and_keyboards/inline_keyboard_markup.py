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


import pyrogram
from pyrogram import raw, types
from pyrogram.types.object import Object


class InlineKeyboardMarkup(Object):
    """An inline keyboard that appears right next to the message it belongs to.

    Parameters:
        inline_keyboard (List of List of :obj:`~pyrogram.types.InlineKeyboardButton`):
            List of button rows, each represented by a List of InlineKeyboardButton objects.
    """

    def __init__(self, inline_keyboard: list[list["types.InlineKeyboardButton"]]):
        super().__init__()

        self.inline_keyboard = inline_keyboard

    @staticmethod
    def read(o):
        inline_keyboard = []

        for i in o.rows:
            row = [types.InlineKeyboardButton.read(j) for j in i.buttons]
            inline_keyboard.append(row)

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    async def write(self, client: "pyrogram.Client"):
        rows = []

        for r in self.inline_keyboard:
            buttons = [await b.write(client) for b in r]

            # Inline rows are KeyboardInlineButtonRow since layer 229; reply keyboards keep
            # KeyboardButtonRow.
            rows.append(raw.types.KeyboardInlineButtonRow(buttons=buttons))

        return raw.types.ReplyInlineMarkup(rows=rows)
