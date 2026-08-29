``Client`` speaks Telegram's own MTProxy transport. Pass
``proxy=dict(scheme="mtproxy", hostname=..., port=..., secret=...)`` -- or the
``tg://proxy?...`` / ``https://t.me/proxy?...`` link itself, which is parsed
into one. Plain 16-byte, ``dd`` (random padding) and ``ee`` (fake-TLS) secrets
are all accepted, in hex or base64, and the secret picks the framing:
``TCPIntermediatePadded`` for a padded secret, ``TCPAbridgedO`` for a plain one.
A ``tg://socks?...`` link is accepted for SOCKS5 the same way.
