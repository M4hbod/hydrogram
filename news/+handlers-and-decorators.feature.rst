Added 16 update handlers and their decorators: ``on_story``, ``on_message_reaction``,
``on_message_reaction_count``, ``on_chat_boost``, ``on_business_message``,
``on_edited_business_message``, ``on_deleted_business_messages``, ``on_business_connection``,
``on_pre_checkout_query``, ``on_shipping_query``, ``on_purchased_paid_media``, ``on_guest_message``,
``on_managed_bot``, ``on_connect``, ``on_start`` and ``on_stop``.

The dispatcher was updated to route them, and ``add_handler``/``remove_handler`` now recognise the
four lifecycle handlers (start, stop, connect, disconnect), which are invoked by the dispatcher and
the session rather than by the routing table.

Also added six ``users`` methods: :meth:`~pyrogram.Client.check_username`,
:meth:`~pyrogram.Client.get_chat_audios`, :meth:`~pyrogram.Client.get_chat_audios_count`,
:meth:`~pyrogram.Client.set_personal_channel`, :meth:`~pyrogram.Client.update_birthday` and
:meth:`~pyrogram.Client.update_status`.
