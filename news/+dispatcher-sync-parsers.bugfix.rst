Five update parsers never reached their handlers. The dispatcher awaits whatever
its routing table returns, and ``user_status``, ``inline_query``,
``chosen_inline_result``, ``chat_member_updated`` and ``chat_join_request`` were
plain functions returning a tuple -- awaiting which raises inside the handler
worker, where it is logged and swallowed. ``deleted_messages`` was called with
four arguments where ``utils.parse_deleted_messages`` takes two.
