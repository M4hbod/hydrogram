The ``proxy`` dict is validated when the ``Client`` is built rather than on the
first connection attempt: an unknown scheme, a missing ``hostname``/``port``, or
a secret that does not decode now raises ``ValueError`` immediately.
