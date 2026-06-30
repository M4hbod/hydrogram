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

from typing import TYPE_CHECKING

from pyrogram.methods.utilities.idle import idle

if TYPE_CHECKING:
    import pyrogram


class Run:
    def run(self: "pyrogram.Client", coroutine=None):
        """Start the client, idle the main script and finally stop the client.

        When calling this method without any argument it acts as a convenience method that calls
        :meth:`~pyrogram.Client.start`, :meth:`~pyrogram.idle` and :meth:`~pyrogram.Client.stop`
        in sequence. It makes running a single client less verbose.

        In case a coroutine is passed as argument, runs the coroutine until it's completed and
        doesn't do any client operation. This is almost the same as :py:obj:`asyncio.run` except
        for the fact that Pyrogram's ``run`` uses the current event loop instead of a new one.

        If you want to run multiple clients at once, see :meth:`pyrogram.compose`.

        Parameters:
            coroutine (``Coroutine``, *optional*):
                Pass a coroutine to run it until it completes.

        Raises:
            ConnectionError: In case you try to run an already started client.

        Example:
            .. code-block:: python

                from pyrogram import Client

                app = Client("my_account")
                ...  # Set handlers up
                app.run()

            .. code-block:: python

                from pyrogram import Client

                app = Client("my_account")


                async def main():
                    async with app:
                        print(await app.get_me())


                app.run(main())
        """
        run = self.loop.run_until_complete

        if coroutine is not None:
            run(coroutine)
        else:
            if self.loop.is_running():
                raise RuntimeError(
                    "You must call client.run() method outside of an asyncio event loop. "
                    "Otherwise, you can use client.start(), client.idle(), and client.stop() "
                    "methods. Refer to https://docs.pyrogram.org/en/latest/api/methods/run.html"
                )

            run(self.start())
            run(idle())
            run(self.stop())
