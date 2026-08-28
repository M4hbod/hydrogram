``pin_forum_topic`` called ``raw.functions.channels.UpdatePinnedForumTopic``, which does not exist
at layer 229 - Telegram moved it to the ``messages`` namespace along with the rest of the
forum-topic RPCs. It would have raised ``AttributeError`` on the first call.
