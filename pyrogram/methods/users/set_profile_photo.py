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

from typing import BinaryIO

import pyrogram
from pyrogram import raw, types


class SetProfilePhoto:
    async def set_profile_photo(
        self: pyrogram.Client,
        photo: str | BinaryIO | None = None,
        video: str | BinaryIO | None = None,
        is_public: bool | None = None,
    ) -> bool:
        """Set a new profile photo or video (H.264/MPEG-4 AVC video, max 5 seconds).

        The ``photo`` and ``video`` arguments are mutually exclusive.
        Pass either one as named argument (see examples below).

        .. note::

            This method only works for Users.
            Bots profile photos must be set using BotFather.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            photo (``str`` | ``BinaryIO``, *optional*):
                Profile photo to set.
                Pass a file path as string to upload a new photo that exists on your local machine or
                pass a binary file-like object with its attribute ".name" set for in-memory uploads.

            video (``str`` | ``BinaryIO``, *optional*):
                Profile video to set.
                Pass a file path as string to upload a new video that exists on your local machine or
                pass a binary file-like object with its attribute ".name" set for in-memory uploads.

            is_public (``bool``, *optional*):
                Pass True to set the photo that people who cannot see your profile photo will get.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                # Set a new profile photo
                await app.set_profile_photo(photo="new_photo.jpg")

                # Set a new profile video
                await app.set_profile_photo(video="new_video.mp4")
        """

        return bool(
            await self.invoke(
                raw.functions.photos.UploadProfilePhoto(
                    file=await self.save_file(photo),
                    video=await self.save_file(video),
                    fallback=is_public,
                )
            )
        )


class SetBotProfilePhoto:
    async def set_bot_profile_photo(
        self: pyrogram.Client,
        bot_user_id: int | str,
        photo: types.InputChatPhoto | None = None,
    ) -> bool:
        """Set the profile photo of a bot you own.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            bot_user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target bot.

            photo (:obj:`~pyrogram.types.InputChatPhoto`, *optional*):
                Profile photo to set. Pass None to remove the current one.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                # Set a new bot profile photo
                await app.set_bot_profile_photo(
                    "@mybot", photo=types.InputChatPhotoStatic("new_photo.jpg")
                )

                # Set a new bot profile video
                await app.set_bot_profile_photo(
                    "@mybot", photo=types.InputChatPhotoAnimation("new_video.mp4")
                )

                # Remove the bot's profile photo
                await app.set_bot_profile_photo("@mybot")
        """
        bot = await self.resolve_peer(bot_user_id)

        # Promoting a photo the bot already has is a different request from
        # uploading a new one, and the empty id is how a photo is removed.
        if photo is None or isinstance(photo, types.InputChatPhotoPrevious):
            return bool(
                await self.invoke(
                    raw.functions.photos.UpdateProfilePhoto(
                        id=await photo.write(self) if photo else raw.types.InputPhotoEmpty(),
                        bot=bot,
                    )
                )
            )

        return bool(
            await self.invoke(
                raw.functions.photos.UploadProfilePhoto(
                    bot=bot,
                    file=await photo.write(self)
                    if isinstance(photo, types.InputChatPhotoStatic)
                    else None,
                    video=await photo.write(self)
                    if isinstance(photo, types.InputChatPhotoAnimation)
                    else None,
                    video_start_ts=getattr(photo, "main_frame_timestamp", None),
                )
            )
        )
