``Client.message_cache`` is now a proper LRU guarded by a lock. It was an unlocked dict that, once
full, discarded *half* its contents at once - so a burst of traffic threw away entries that were
still in use. Access is now ``await client.message_cache.get(key)`` / ``.set(key, value)`` rather
than subscripting.
