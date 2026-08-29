``pin_forum_topic`` and ``unpin_forum_topic`` raised ``TypeError`` on every call:
they passed ``channel=`` to ``messages.UpdatePinnedForumTopic``, whose field is
``peer``. ``tests/contract/test_raw_keywords.py`` now checks every keyword handed
to a raw constructor against that constructor's signature.
