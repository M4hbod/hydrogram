:obj:`~pyrogram.types.Message` now parses everything layer 229 can send. Attributes go from 79 to
168, handled service actions from 18 to 67, and handled media types from 9 to 16 - checklists, paid
media, suggested posts, business messages, giveaways, stories, gifts, boosts, reactions and the
rest. 133 supporting types were added, along with the enum members they need
(``MessageServiceType`` alone gains 53).

``Client`` gains ``fetch_replies``, ``fetch_topics``, ``fetch_stories`` and ``topic_cache_size``.
``fetch_topics`` and ``fetch_stories`` default to ``False`` until the chats and stories method
groups land, because the paths they gate call methods that do not exist yet.
