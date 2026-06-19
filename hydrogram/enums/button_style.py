#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from enum import auto

from .auto_name import AutoName


class ButtonStyle(AutoName):
    """Background style of a :obj:`~hydrogram.types.KeyboardButton` or
    :obj:`~hydrogram.types.InlineKeyboardButton` (Bot API 9.4 / layer 223+)."""

    DEFAULT = auto()
    "The button uses the default style."

    PRIMARY = auto()
    "The button has a dark-blue background."

    DANGER = auto()
    "The button has a red background."

    SUCCESS = auto()
    "The button has a green background."
