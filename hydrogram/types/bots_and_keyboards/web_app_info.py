#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Amano LLC <https://amanoteam.com>
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

from hydrogram.types.object import Object


class WebAppInfo(Object):
    """Contains information about a `Web App <https://core.telegram.org/bots/webapps>`_.

    Parameters:
        url (``str``):
            An HTTPS URL of a Web App to be opened with additional data as specified in
            `Initializing Web Apps <https://core.telegram.org/bots/webapps#initializing-web-apps>`_.
    """

    def __init__(
        self,
        *,
        url: str,
    ):
        super().__init__()

        self.url = url