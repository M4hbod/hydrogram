New ``Client.recover_gaps()``: fetch the updates that arrived while the client
was offline and feed them through the normal handler pipeline. ``Client`` now
remembers each chat's update counters in an ``update_state`` table, which
``skip_updates=False`` catches up from at start and again whenever the updates
watchdog fires. ``skip_updates=False`` previously raised ``AttributeError``: the
dispatcher already called ``recover_gaps``, and the method did not exist.
