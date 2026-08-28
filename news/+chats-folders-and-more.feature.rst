Added 44 methods across five groups.

**chats (36)** - chat folders (create, edit, delete, reorder, join, leave, invite links, tags),
direct-message topics, forum topic pin/unpin and toggling, accent and profile colours, chat TTL,
discussion and direct-message groups, member tags, similar and personal channels, top chats,
per-chat notification settings, and message reaction deletion.

**contacts (3)** - :meth:`~pyrogram.Client.search_contacts`,
:meth:`~pyrogram.Client.set_contact_note`, :meth:`~pyrogram.Client.get_blocked_message_senders`.

**premium (3)** - :meth:`~pyrogram.Client.apply_boost`, :meth:`~pyrogram.Client.get_boosts`,
:meth:`~pyrogram.Client.get_boosts_status`.

**phone (1)** - :meth:`~pyrogram.Client.get_call_members`.

**folders (1)** - :meth:`~pyrogram.Client.check_chat_folder_invite_link`, in a new ``folders``
method group.
