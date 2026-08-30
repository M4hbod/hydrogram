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

        copy_text (``str``, *optional*):
            Text to copy to the clipboard when the button is pressed. Limited to 256 characters.

        pay (``bool``, *optional*):
            Pass True to send a Pay button. Substrings ``⭐`` and ``XTR`` in the button's text are
            replaced with a Telegram Star icon.

            **NOTE**: This type of button **must** always be the first button in the first row and
            can only be used in invoice messages.

        disabled (``bool``, *optional*):
            Pass True to render the button as disabled. Pressing it does nothing.

        requires_password (``bool``, *optional*):
            Pass True to ask for the user's 2-step verification password before the callback query
            is sent to the bot.

        style (:obj:`~pyrogram.enums.ButtonStyle`, *optional*):
            Background style of the button (default, primary, danger, success).
            Verified working against production Telegram from a bot whose owner does **not** have
            Premium, so it carries no such requirement.

        icon_custom_emoji_id (``str``, *optional*):
            Unique identifier of a custom emoji shown as an icon before the button text.

            **The server drops this silently when it will not honour it.** Sending a button with an
            icon from a bot whose owner lacks Telegram Premium succeeds, and the button comes back
            with ``icon_custom_emoji_id`` set to ``None`` -- no error, no warning. Confirmed against
            production with a genuine custom emoji document id, so read the value back if you need
            to know whether it took.
    """

    def __init__(
        self,
        text: str,
        icon_custom_emoji_id: str | None = None,
        style: enums.ButtonStyle = enums.ButtonStyle.DEFAULT,
        url: str | None = None,
        callback_data: str | bytes | None = None,
        requires_password: bool | None = None,
        web_app: types.WebAppInfo | None = None,
        login_url: types.LoginUrl | None = None,
        user_id: int | None = None,
        switch_inline_query: str | None = None,
        switch_inline_query_current_chat: str | None = None,
        switch_inline_query_chosen_chat: types.SwitchInlineQueryChosenChat | None = None,
        copy_text: types.CopyTextButton | None = None,
        callback_game: types.CallbackGame | None = None,
        pay: bool | None = None,
        disabled: bool | None = None,
    ):
        super().__init__()

        self.text = str(text)
        self.icon_custom_emoji_id = icon_custom_emoji_id
        self.style = style
        self.url = url
        self.callback_data = callback_data
        self.requires_password = requires_password
        self.web_app = web_app
        self.login_url = login_url
        self.user_id = user_id
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.switch_inline_query_chosen_chat = switch_inline_query_chosen_chat
        self.copy_text = copy_text
        self.callback_game = callback_game
        self.pay = pay
        self.disabled = disabled

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
    def read(b: raw.types.KeyboardInlineButton):
        """Parse a layer-229 ``keyboardInlineButton``.

        Layer 229 split inline buttons off from reply buttons: they are their own base type
        (``KeyboardInlineButton``) and the kind is carried in ``type:InlineButtonType`` rather than
        in the constructor. Every variant is handled here, because an unhandled one is a button
        that silently disappears from the parsed markup.
        """
        style, icon = InlineKeyboardButton._read_style(b)
        button_type = b.type
        common = {"text": b.text, "style": style, "icon_custom_emoji_id": icon}

        if isinstance(button_type, raw.types.InlineButtonTypeCallback):
            # Keep the data as a string when it decodes, but fall back to bytes rather than
            # losing information to errors="ignore".
            try:
                data = button_type.data.decode()
            except UnicodeDecodeError:
                data = button_type.data

            return InlineKeyboardButton(
                callback_data=data,
                requires_password=button_type.requires_password or None,
                **common,
            )

        if isinstance(button_type, raw.types.InlineButtonTypeUrl):
            return InlineKeyboardButton(url=button_type.url, **common)

        if isinstance(
            button_type,
            (raw.types.InlineButtonTypeUrlAuth, raw.types.InputInlineButtonTypeUrlAuth),
        ):
            return InlineKeyboardButton(login_url=types.LoginUrl.read(button_type), **common)

        if isinstance(
            button_type,
            (
                raw.types.InlineButtonTypeUserProfile,
                raw.types.InputInlineButtonTypeUserProfile,
            ),
        ):
            return InlineKeyboardButton(user_id=button_type.user_id, **common)

        if isinstance(button_type, raw.types.InlineButtonTypeSwitchInline):
            if button_type.same_peer:
                return InlineKeyboardButton(
                    switch_inline_query_current_chat=button_type.query, **common
                )
            return InlineKeyboardButton(switch_inline_query=button_type.query, **common)

        if isinstance(button_type, raw.types.InlineButtonTypeGame):
            return InlineKeyboardButton(callback_game=types.CallbackGame(), **common)

        if isinstance(button_type, raw.types.InlineButtonTypeWebView):
            return InlineKeyboardButton(web_app=types.WebAppInfo(url=button_type.url), **common)

        if isinstance(button_type, raw.types.InlineButtonTypeCopy):
            return InlineKeyboardButton(copy_text=button_type.copy_text, **common)

        if isinstance(button_type, raw.types.InlineButtonTypeBuy):
            return InlineKeyboardButton(pay=True, **common)

        if isinstance(button_type, raw.types.InlineButtonTypeDisabled):
            return InlineKeyboardButton(disabled=True, **common)

        return None

    async def write(self, client: pyrogram.Client):
        button_type = await self._write_type(client)

        return raw.types.KeyboardInlineButton(
            text=self.text, type=button_type, style=self._raw_style()
        )

    async def _write_type(self, client: pyrogram.Client) -> raw.base.InlineButtonType:
        """Pick the ``InlineButtonType`` this button describes.

        The order mirrors the historical write(): the first field that is set wins, which is what
        the "you must use exactly one of the optional fields" contract in the docstring means.
        """
        if self.callback_data is not None:
            # Telegram wants bytes; strings are accepted here for convenience.
            data = (
                bytes(self.callback_data, "utf-8")
                if isinstance(self.callback_data, str)
                else self.callback_data
            )
            return raw.types.InlineButtonTypeCallback(
                data=data, requires_password=self.requires_password
            )

        if self.url is not None:
            return raw.types.InlineButtonTypeUrl(url=self.url)

        if self.login_url is not None:
            return self.login_url.write(
                bot=await client.resolve_peer(self.login_url.bot_username or "self")
            )

        if self.user_id is not None:
            return raw.types.InputInlineButtonTypeUserProfile(
                user_id=await client.resolve_peer(self.user_id)
            )

        if self.switch_inline_query is not None:
            return raw.types.InlineButtonTypeSwitchInline(query=self.switch_inline_query)

        if self.switch_inline_query_current_chat is not None:
            return raw.types.InlineButtonTypeSwitchInline(
                query=self.switch_inline_query_current_chat, same_peer=True
            )

        if self.callback_game is not None:
            return raw.types.InlineButtonTypeGame()

        if self.web_app is not None:
            return raw.types.InlineButtonTypeWebView(url=self.web_app.url)

        if self.copy_text is not None:
            return raw.types.InlineButtonTypeCopy(copy_text=self.copy_text)

        if self.pay:
            return raw.types.InlineButtonTypeBuy()

        if self.disabled:
            return raw.types.InlineButtonTypeDisabled()

        raise ValueError(
            "InlineKeyboardButton requires exactly one of: callback_data, url, login_url, "
            "user_id, switch_inline_query, switch_inline_query_current_chat, callback_game, "
            "web_app, copy_text, pay, disabled"
        )
