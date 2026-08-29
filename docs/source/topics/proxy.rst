Proxy Settings
==============

Pyrogram reaches Telegram through a proxy in either of two ways.

A **SOCKS 4/5 or HTTP (CONNECT)** proxy is a plain tunnel: Pyrogram dials the proxy, the proxy dials
Telegram, and the MTProto stream inside is exactly what it would be on a direct connection.

An **MTProxy** is Telegram's own thing. There is no tunnelling protocol: Pyrogram speaks Telegram's
obfuscated transport directly to the proxy, mixing the proxy's secret into the keys, and the proxy
relays it to the data centre named in the handshake. This is the kind shared as a
``https://t.me/proxy?...`` link.

-----

SOCKS and HTTP
--------------

Pass the proxy settings as the *proxy* parameter of :obj:`~pyrogram.Client`. Omit ``username`` and
``password`` when the proxy needs no authorization.

.. code-block:: python

    from pyrogram import Client

    proxy = {
        "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
        "hostname": "11.22.33.44",
        "port": 1234,
        "username": "username",
        "password": "password",
    }

    app = Client("my_account", proxy=proxy)

    app.run()

-----

MTProxy
-------

An MTProxy takes a ``secret`` instead of credentials, and no username or password.

.. code-block:: python

    from pyrogram import Client

    proxy = {
        "scheme": "mtproxy",
        "hostname": "11.22.33.44",
        "port": 443,
        "secret": "dd00112233445566778899aabbccddeeff",
    }

    app = Client("my_account", proxy=proxy)

    app.run()

A shared proxy link can be passed in place of the dict, which is usually what you have to hand.
``tg://proxy?...`` and ``https://t.me/proxy?...`` both work, and so do the ``socks`` equivalents:

.. code-block:: python

    app = Client(
        "my_account",
        proxy="https://t.me/proxy?server=11.22.33.44&port=443&secret=dd00112233445566778899aabbccddeeff",
    )

Secret flavours
^^^^^^^^^^^^^^^

The secret is accepted as hex or base64, and its length decides how the connection is framed. You
do not choose the framing; the secret does.

.. list-table::
    :header-rows: 1

    * - Secret
      - What it means
    * - 16 bytes
      - Plain obfuscated transport.
    * - ``dd`` + 16 bytes
      - Random padding on every packet, so packet lengths carry no signature.
    * - ``ee`` + 16 bytes + a domain
      - Fake-TLS. The connection opens with a TLS ClientHello for that domain and the stream is cut
        into TLS records, so it looks like ordinary HTTPS traffic to that host.

With an ``ee`` secret the proxy's reply to the greeting is authenticated against the secret: a
server that answers without knowing it is rejected rather than trusted.

.. note::

    A proxy sees every byte you exchange with Telegram, obfuscated but not end-to-end encrypted from
    it, along with which data centre you connect to and when. Use one you have a reason to trust.

Validation
----------

The proxy settings are checked when the :obj:`~pyrogram.Client` is constructed, not on the first
connection attempt, so an unknown scheme, a missing field or a secret that does not decode raises
``ValueError`` right away.
