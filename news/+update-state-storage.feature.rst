``BaseStorage`` gains ``get_update_states``, ``set_update_state`` and
``delete_update_state``, and a ``UpdateState`` record to go with them. Custom
storage engines must implement all three. SQLite session files are migrated to
schema version 4 on open; nothing has to be done by hand.
