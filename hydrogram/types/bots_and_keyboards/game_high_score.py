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
from hydrogram import raw, types, utils
from hydrogram.types.object import Object


class GameHighScore(Object):
    """One row of the high scores table for a game.

    Parameters:
        user (:obj:`~hydrogram.types.User`):
            User.

        score (``int``):
            Score.

        position (``int``, *optional*):
            Position in high score table for the game.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        user: types.User,
        score: int,
        position: int | None = None,
    ):
        super().__init__(client)

        self.user = user
        self.score = score
        self.position = position

    @staticmethod
    def _parse(client, game_high_score: raw.types.HighScore, users: dict) -> GameHighScore:
        users = {i.id: i for i in users}

        return GameHighScore(
            user=types.User._parse(client, users[game_high_score.user_id]),
            score=game_high_score.score,
            position=game_high_score.pos,
            client=client,
        )

    @staticmethod
    def _parse_action(client, service: raw.types.MessageService, users: dict):
        return GameHighScore(
            user=types.User._parse(
                client, users[utils.get_raw_peer_id(service.from_id or service.peer_id)]
            ),
            score=service.action.score,
            client=client,
        )
