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

from __future__ import annotations

import hydrogram
from hydrogram import raw
from hydrogram.errors import UnknownError


class GetInlineBotResults:
    async def get_inline_bot_results(
        self: hydrogram.Client,
        bot: int | str,
        query: str = "",
        offset: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
    ):
        """Get bot results via inline queries.
        You can then send a result using :meth:`~hydrogram.Client.send_inline_bot_result`

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            bot (``int`` | ``str``):
                Unique identifier of the inline bot you want to get results from. You can specify
                a @username (str) or a bot ID (int).

            query (``str``, *optional*):
                Text of the query (up to 512 characters).
                Defaults to "" (empty string).

            offset (``str``, *optional*):
                Offset of the results to be returned.

            latitude (``float``, *optional*):
                Latitude of the location.
                Useful for location-based results only.

            longitude (``float``, *optional*):
                Longitude of the location.
                Useful for location-based results only.

        Returns:
            :obj:`BotResults <hydrogram.api.types.messages.BotResults>`: On Success.

        Raises:
            TimeoutError: In case the bot fails to answer within 10 seconds.

        Example:
            .. code-block:: python

                results = await app.get_inline_bot_results("hydrogrambot")
                print(results)
        """
        # TODO: Don't return the raw type

        try:
            return await self.invoke(
                raw.functions.messages.GetInlineBotResults(
                    bot=await self.resolve_peer(bot),
                    peer=raw.types.InputPeerSelf(),
                    query=query,
                    offset=offset,
                    geo_point=raw.types.InputGeoPoint(lat=latitude, long=longitude)
                    if (latitude is not None and longitude is not None)
                    else None,
                )
            )
        except UnknownError as e:
            # TODO: Add this -503 Timeout error into the Error DB
            if e.value.error_code == -503 and e.value.error_message == "Timeout":
                raise TimeoutError("The inline bot didn't answer in time") from None
            raise e
