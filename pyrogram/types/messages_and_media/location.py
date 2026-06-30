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
from pyrogram import raw
from pyrogram.types.object import Object


class Location(Object):
    """A point on the map.

    Parameters:
        longitude (``float``):
            Longitude as defined by sender.

        latitude (``float``):
            Latitude as defined by sender.

        horizontal_accuracy (``int``, *optional*):
            The estimated horizontal accuracy of the location, in meters, as defined by sender.
    """

    def __init__(
        self,
        *,
        client: pyrogram.Client = None,
        longitude: float,
        latitude: float,
        horizontal_accuracy: int | None,
    ):
        super().__init__(client)

        self.longitude = longitude
        self.latitude = latitude
        self.horizontal_accuracy = horizontal_accuracy

    @staticmethod
    def _parse(client, geo_point: raw.types.GeoPoint) -> Location:
        if isinstance(geo_point, raw.types.GeoPoint):
            return Location(
                longitude=geo_point.long,
                latitude=geo_point.lat,
                horizontal_accuracy=geo_point.accuracy_radius,
                client=client,
            )
        return None
