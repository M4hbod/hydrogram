``send_paid_media`` passed ``direct_messages_topic_id`` into
``get_reply_to``'s ``message_thread_id`` slot, scoping the message to the wrong
topic. ``tests/contract/test_parameters_are_used.py`` now fails when a method
declares a parameter its own body never reads -- an option accepted and silently
dropped is worse than one that is missing.
