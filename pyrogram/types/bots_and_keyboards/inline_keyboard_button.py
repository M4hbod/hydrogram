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

import pyrogram
from pyrogram import enums, raw, types
from pyrogram.types.object import Object


class InlineKeyboardButton(Object):
    """One button of an inline keyboard.

    You must use exactly one of the optional fields.

    Parameters:
        text (``str``):
            Label text on the button.

        callback_data (``str`` | ``bytes``, *optional*):
            Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes.

        url (``str``, *optional*):
            HTTP url to be opened when button is pressed.

        web_app (:obj:`~pyrogram.types.WebAppInfo`, *optional*):
            Description of the `Web App <https://core.telegram.org/bots/webapps>`_ that will be launched when the user
            presses the button. The Web App will be able to send an arbitrary message on behalf of the user using the
            method :meth:`~pyrogram.Client.answer_web_app_query`. Available only in private chats between a user and the
            bot.

        login_url (:obj:`~pyrogram.types.LoginUrl`, *optional*):
             An HTTP URL used to automatically authorize the user. Can be used as a replacement for
             the `Telegram Login Widget <https://core.telegram.org/widgets/login>`_.

        user_id (``int``, *optional*):
            User id, for links to the user profile.

        switch_inline_query (``str``, *optional*):
            If set, pressing the button will prompt the user to select one of their chats, open that chat and insert
            the bot's username and the specified inline query in the input field. Can be empty, in which case just
            the bot's username will be inserted.Note: This offers an easy way for users to start using your bot in
            inline mode when they are currently in a private chat with it. Especially useful when combined with
            switch_pm… actions – in this case the user will be automatically returned to the chat they switched from,
            skipping the chat selection screen.

        switch_inline_query_current_chat (``str``, *optional*):
            If set, pressing the button will insert the bot's username and the specified inline query in the current
            chat's input field. Can be empty, in which case only the bot's username will be inserted.This offers a
            quick way for the user to open your bot in inline mode in the same chat – good for selecting something
            from multiple options.

        callback_game (:obj:`~pyrogram.types.CallbackGame`, *optional*):
            Description of the game that will be launched when the user presses the button.
            **NOTE**: This type of button **must** always be the first button in the first row.

        style (:obj:`~pyrogram.enums.ButtonStyle`, *optional*):
            Background style of the button (default, primary, danger, success). Requires the bot
            owner to have Telegram Premium.

        icon_custom_emoji_id (``str``, *optional*):
            Unique identifier of a custom emoji shown as an icon before the button text. Requires the
            bot owner to have Telegram Premium.
    """

    def __init__(
        self,
        text: str | Any,
        callback_data: str | bytes | None = None,
        url: str | None = None,
        web_app: types.WebAppInfo = None,
        login_url: types.LoginUrl = None,
        user_id: int | None = None,
        switch_inline_query: str | None = None,
        switch_inline_query_current_chat: str | None = None,
        callback_game: types.CallbackGame = None,
        style: enums.ButtonStyle = enums.ButtonStyle.DEFAULT,
        icon_custom_emoji_id: str | None = None,
    ):
        super().__init__()

        self.text = text if isinstance(text, str) else str(text)
        self.callback_data = callback_data
        self.url = url
        self.web_app = web_app
        self.login_url = login_url
        self.user_id = user_id
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.callback_game = callback_game
        self.style = style or enums.ButtonStyle.DEFAULT
        self.icon_custom_emoji_id = icon_custom_emoji_id
        # self.pay = pay

    def _raw_style(self):
        """Build the raw KeyboardButtonStyle, or None when nothing is set (default + no icon)."""
        if self.style == enums.ButtonStyle.DEFAULT and self.icon_custom_emoji_id is None:
            return None
        return raw.types.KeyboardButtonStyle(
            bg_primary=self.style == enums.ButtonStyle.PRIMARY,
            bg_danger=self.style == enums.ButtonStyle.DANGER,
            bg_success=self.style == enums.ButtonStyle.SUCCESS,
            icon=int(self.icon_custom_emoji_id) if self.icon_custom_emoji_id is not None else None,
        )

    @staticmethod
    def _read_style(b):
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

    @staticmethod
    def read(b: raw.base.KeyboardButton):
        style, icon = InlineKeyboardButton._read_style(b)
        if isinstance(b, raw.types.KeyboardButtonCallback):
            # Try decode data to keep it as string, but if fails, fallback to bytes so we don't lose any information,
            # instead of decoding by ignoring/replacing errors.
            try:
                data = b.data.decode()
            except UnicodeDecodeError:
                data = b.data

            return InlineKeyboardButton(
                text=b.text, callback_data=data, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(b, raw.types.KeyboardButtonUrl):
            return InlineKeyboardButton(
                text=b.text, url=b.url, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(b, raw.types.KeyboardButtonUrlAuth):
            return InlineKeyboardButton(
                text=b.text,
                login_url=types.LoginUrl.read(b),
                style=style,
                icon_custom_emoji_id=icon,
            )

        if isinstance(b, raw.types.KeyboardButtonUserProfile):
            return InlineKeyboardButton(
                text=b.text, user_id=b.user_id, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(b, raw.types.KeyboardButtonSwitchInline):
            if b.same_peer:
                return InlineKeyboardButton(
                    text=b.text,
                    switch_inline_query_current_chat=b.query,
                    style=style,
                    icon_custom_emoji_id=icon,
                )
            return InlineKeyboardButton(
                text=b.text, switch_inline_query=b.query, style=style, icon_custom_emoji_id=icon
            )

        if isinstance(b, raw.types.KeyboardButtonGame):
            return InlineKeyboardButton(
                text=b.text,
                callback_game=types.CallbackGame(),
                style=style,
                icon_custom_emoji_id=icon,
            )

        if isinstance(b, raw.types.KeyboardButtonWebView):
            return InlineKeyboardButton(
                text=b.text,
                web_app=types.WebAppInfo(url=b.url),
                style=style,
                icon_custom_emoji_id=icon,
            )
        return None

    async def write(self, client: pyrogram.Client):
        style = self._raw_style()
        if self.callback_data is not None:
            # Telegram only wants bytes, but we are allowed to pass strings too, for convenience.
            data = (
                bytes(self.callback_data, "utf-8")
                if isinstance(self.callback_data, str)
                else self.callback_data
            )

            return raw.types.KeyboardButtonCallback(text=self.text, data=data, style=style)

        if self.url is not None:
            return raw.types.KeyboardButtonUrl(text=self.text, url=self.url, style=style)

        if self.login_url is not None:
            return self.login_url.write(
                text=self.text,
                bot=await client.resolve_peer(self.login_url.bot_username or "self"),
                style=style,
            )

        if self.user_id is not None:
            return raw.types.InputKeyboardButtonUserProfile(
                text=self.text, user_id=await client.resolve_peer(self.user_id), style=style
            )

        if self.switch_inline_query is not None:
            return raw.types.KeyboardButtonSwitchInline(
                text=self.text, query=self.switch_inline_query, style=style
            )

        if self.switch_inline_query_current_chat is not None:
            return raw.types.KeyboardButtonSwitchInline(
                text=self.text,
                query=self.switch_inline_query_current_chat,
                same_peer=True,
                style=style,
            )

        if self.callback_game is not None:
            return raw.types.KeyboardButtonGame(text=self.text, style=style)

        if self.web_app is not None:
            return raw.types.KeyboardButtonWebView(
                text=self.text, url=self.web_app.url, style=style
            )
        return None
