#  Pyrogram - Telegram MTProto API Client Library for Python
#  Compatibility shim: upstream pyrogram ships a `pyrogram.emoji` module of emoji-name
#  constants. This fork (rebranded from hydrogram) doesn't, but third-party libs such as
#  pykeyboard do `from pyrogram.emoji import *` at import time. They don't actually use any
#  constant, so an empty module is enough to keep that import working.

__all__: list[str] = []
