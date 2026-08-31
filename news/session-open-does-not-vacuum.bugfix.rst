Opening an existing session file no longer runs ``VACUUM``. It ran on every
open, rewriting the whole database under an exclusive lock for as long as that
took, and had nothing to reclaim once the schema was current; it now runs only
after a migration actually changes something. The connection's busy timeout is
also raised from sqlite3's 5 second default to 15, settable through
``SQLiteStorage.BUSY_TIMEOUT`` or the storage's ``busy_timeout`` argument. Both
matter only when two connections share one session file, which is the situation
that produces ``sqlite3.OperationalError: database is locked``.
