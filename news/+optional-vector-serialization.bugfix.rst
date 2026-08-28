Fixed serialization of any TL object with an optional ``Vector`` field that had been deserialized
first. ``read()`` gives an absent ``flags.n?Vector<T>`` the value ``[]``, but the generated
``write()`` guarded the body on ``is not None`` while the flag bit was computed by truthiness, so
re-serializing wrote an empty vector with no flag set - eight stray bytes that desynchronized every
field after it. 97 generated types were affected.
