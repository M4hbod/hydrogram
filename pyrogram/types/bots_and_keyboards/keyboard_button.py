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

from typing import Any

from pyrogram import enums, raw, types
from pyrogram.types.object import Object


class KeyboardButton(Object):
    """One button of the reply keyboard.
    For simple text buttons String can be used instead of this object to specify text of the button.
    Optional fields are mutually exclusive.

    Parameters:
        text (``str``):
            Text of the button. If none of the optional fields are used, it will be sent as a message when
            the button is pressed.

        request_contact (``bool``, *optional*):
            If True, the user's phone number will be sent as a contact when the button is pressed.
            Available in private chats only.

        request_location (``bool``, *optional*):
            If True, the user's current location will be sent when the button is pressed.
            Available in private chats only.

        web_app (:obj:`~pyrogram.types.WebAppInfo`, *optional*):
            If specified, the described `Web App <https://core.telegram.org/bots/webapps>`_ will be launched when the
            button is pressed. The Web App will be able to send a “web_app_data” service message. Available in private
            chats only.

    """

    def __init__(
        self,
        text: str | Any,
        request_contact: bool | None = None,
        request_location: bool | None = None,
        web_app: types.WebAppInfo = None,
        style: enums.ButtonStyle = enums.ButtonStyle.DEFAULT,
        icon_custom_emoji_id: str | None = None,
    ):
        super().__init__()

        self.text = text if isinstance(text, str) else str(text)
        self.request_contact = request_contact
        self.request_location = request_location
        self.web_app = web_app
        self.style = style or enums.ButtonStyle.DEFAULT
        self.icon_custom_emoji_id = icon_custom_emoji_id

    def _raw_style(self):
        if self.style == enums.ButtonStyle.DEFAULT and self.icon_custom_emoji_id is None:
            return None
        return raw.types.KeyboardButtonStyle(
            bg_primary=self.style == enums.ButtonStyle.PRIMARY,
            bg_danger=self.style == enums.ButtonStyle.DANGER,
            bg_success=self.style == enums.ButtonStyle.SUCCESS,
            icon=int(self.icon_custom_emoji_id) if self.icon_custom_emoji_id is not None else None,
        )

    @staticmethod
    def read(b: raw.types.KeyboardButton):
        """Parse a layer-229 ``keyboardButton``.

        Layer 229 replaced the flat per-kind constructors with a single ``keyboardButton``
        carrying a ``type:ButtonType`` discriminator, so the dispatch is on ``b.type`` rather than
        on the class of ``b``.
        """
        style, icon = KeyboardButton._read_style(b)
        button_type = b.type

        if isinstance(button_type, raw.types.ButtonTypeRequestPhone):
            return KeyboardButton(
                text=b.text, request_contact=True, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(button_type, raw.types.ButtonTypeRequestGeoLocation):
            return KeyboardButton(
                text=b.text, request_location=True, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(button_type, raw.types.ButtonTypeSimpleWebView):
            return KeyboardButton(
                text=b.text,
                web_app=types.WebAppInfo(url=button_type.url),
                style=style,
                icon_custom_emoji_id=icon,
            )

        # buttonTypeDefault, and anything this version does not model yet: a plain text button.
        # Returning the bare string keeps the historical behaviour, where a keyboard of plain
        # buttons round-trips as a list of strings.
        if style is enums.ButtonStyle.DEFAULT and icon is None:
            return b.text

        return KeyboardButton(text=b.text, style=style, icon_custom_emoji_id=icon)

    @staticmethod
    def _read_style(b) -> tuple[enums.ButtonStyle, str | None]:
        """Map a raw button's optional ``style`` to (ButtonStyle, icon_custom_emoji_id)."""
        raw_style = getattr(b, "style", None)
        style = enums.ButtonStyle.DEFAULT
        icon = None

        if raw_style is not None:
            if raw_style.bg_primary:
                style = enums.ButtonStyle.PRIMARY
            elif raw_style.bg_danger:
                style = enums.ButtonStyle.DANGER
            elif raw_style.bg_success:
                style = enums.ButtonStyle.SUCCESS

            if raw_style.icon is not None:
                icon = str(raw_style.icon)

        return style, icon

    def write(self):
        if self.request_contact:
            button_type = raw.types.ButtonTypeRequestPhone()
        elif self.request_location:
            button_type = raw.types.ButtonTypeRequestGeoLocation()
        elif self.web_app:
            button_type = raw.types.ButtonTypeSimpleWebView(url=self.web_app.url)
        else:
            button_type = raw.types.ButtonTypeDefault()

        return raw.types.KeyboardButton(text=self.text, type=button_type, style=self._raw_style())
