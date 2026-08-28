Fixed every forum-topic method and :meth:`~pyrogram.Client.transfer_chat_ownership` raising
``AttributeError`` at call time. They invoked ``raw.functions.channels.*``, but Telegram moved
``createForumTopic``, ``editForumTopic``, ``getForumTopics``, ``getForumTopicsByID`` and
``deleteTopicHistory`` to the ``messages`` namespace (taking ``peer`` rather than ``channel``), and
replaced ``channels.editCreator`` with ``messages.editChatCreator``.
