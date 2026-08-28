Added the ``skip_updates`` client option. It defaults to ``True``, dropping updates that queued
while the client was offline; pass ``False`` to receive them on connect. The ported dispatcher
requires it.
