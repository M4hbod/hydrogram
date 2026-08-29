``SQLiteStorage.close()`` commits before closing. SQLite rolls an open
transaction back on close, so anything written without an explicit commit --
which now includes every chat's update counters -- was discarded exactly when
it was needed, on the next start.
