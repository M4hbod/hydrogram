13 bound methods raised ``TypeError`` on every call. Each passed keywords its
client method does not accept -- all eleven ``Story.reply_*`` shortcuts, plus
``Story.react`` and two new ``Message`` ones -- because the bound methods were
ported with Kurigram's signatures while the client methods stayed behind. The
parameters that could not work are gone from both the call and the signature,
and ``tests/contract/test_bound_method_delegation.py`` now walks every
``self._client.X(...)`` in the type tree and fails when a keyword is not in
``Client.X``'s signature.
