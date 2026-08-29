``pysocks`` is replaced by ``python-socks[asyncio]``. The SOCKS and HTTP proxy
handshake was synchronous and ran on the event loop, blocking every other task
for its duration -- long enough to deadlock outright against a proxy served
from the same loop. Proxy failures now raise ``python_socks.ProxyError`` with
the reason rather than a bare ``TimeoutError``. The ``proxy`` dict is unchanged.
