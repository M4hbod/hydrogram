``set_update_state`` and ``delete_update_state`` now commit. They did not, and
sqlite holds the WAL write lock from the first statement of a transaction until
someone commits it, so a client receiving updates parked the write lock until
the updates watchdog's ``save()`` -- up to fifteen minutes. Any other connection
to the same session file failed its writes with ``database is locked`` for that
whole window, and a client that died in between lost every update counter since
the last save. Reads were unaffected, which is why only writes failed.
