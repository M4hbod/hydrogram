``delete_forum_topic`` no longer swallows every exception. It caught all errors, printed them to
stdout and returned ``False``, so a ``FloodWait`` looked identical to "the topic was not deleted" --
and a caller retrying on ``False`` would hammer straight through the flood wait. Errors now
propagate, matching every other forum-topic method.
