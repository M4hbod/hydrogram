Fixed the updates watchdog and the session reconnect throttle measuring elapsed time with a wall
clock. Both used ``datetime.now()``, which steps at DST boundaries, on NTP corrections and when the
system time is set: a backward step stalled the watchdog for the length of the step and made the
reconnect throttle see a negative interval, so it throttled every attempt. Both now use
``time.monotonic()``.

``Session.RECONNECT_THRESHOLD`` is consequently a number of seconds (``10.0``) rather than a
``timedelta``, and the throttle tests ``is not None`` rather than truthiness -- a monotonic reading
of ``0.0`` is legitimate and would previously have disabled the throttle.
