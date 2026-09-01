=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "news".
    WARNING: Don't drop the next directive!

.. towncrier-draft-entries:: |release| [UNRELEASED DRAFT]

.. towncrier release notes start

3.3.2 (2026-09-01)
===================

Bugfixes
--------

- ``set_update_state`` and ``delete_update_state`` now commit. They did not, and
  sqlite holds the WAL write lock from the first statement of a transaction until
  someone commits it, so a client receiving updates parked the write lock until
  the updates watchdog's ``save()`` -- up to fifteen minutes. Any other connection
  to the same session file failed its writes with ``database is locked`` for that
  whole window, and a client that died in between lost every update counter since
  the last save. Reads were unaffected, which is why only writes failed.
  `#update-state-commits <https://github.com/M4hbod/hydrogram/issues/update-state-commits>`_


3.3.1 (2026-09-01)
===================

Bugfixes
--------

- Opening an existing session file no longer runs ``VACUUM``. It ran on every
  open, rewriting the whole database under an exclusive lock for as long as that
  took, and had nothing to reclaim once the schema was current; it now runs only
  after a migration actually changes something. The connection's busy timeout is
  also raised from sqlite3's 5 second default to 15, settable through
  ``SQLiteStorage.BUSY_TIMEOUT`` or the storage's ``busy_timeout`` argument. Both
  matter only when two connections share one session file, which is the situation
  that produces ``sqlite3.OperationalError: database is locked``.
  `#session-open-does-not-vacuum <https://github.com/M4hbod/hydrogram/issues/session-open-does-not-vacuum>`_


3.3.0 (2026-08-31)
===================

Features
--------

- :obj:`~pyrogram.types.InputRichMessage` now takes ``blocks``, so rich messages
  can be sent in their structured form instead of only as HTML or Markdown. This
  is what carries tables, lists with checkboxes, collapsible sections, headings,
  anchors, nested quotations, collages and media. The blocks are the same
  :obj:`~pyrogram.types.RichBlock` and :obj:`~pyrogram.types.RichText` classes
  that reading a rich message already returns, so a message can be parsed, edited
  and sent again rather than needing a parallel set of input types.
  `#rich-message-blocks <https://github.com/M4hbod/hydrogram/issues/rich-message-blocks>`_


Bugfixes
--------

- ``RichBlockTable._parse`` put a bare :obj:`~pyrogram.types.RichText` in
  ``caption``, which its own docstring types as a
  :obj:`~pyrogram.types.RichBlockCaption` like every other block's. It now wraps
  the raw ``title`` in a ``RichBlockCaption``. Code reading ``table.caption``
  directly as text must now read ``table.caption.text``.
  `#rich-block-table-caption <https://github.com/M4hbod/hydrogram/issues/rich-block-table-caption>`_
- The ``text``, ``summary`` and ``credit`` parameters of the
  :obj:`~pyrogram.types.RichText` and :obj:`~pyrogram.types.RichBlock` classes
  were annotated ``RichText``, but ``RichText`` is a union that includes ``str``
  and a list of spans, which is what the parser has always passed them. The
  annotations now say so.
  `#rich-text-annotations <https://github.com/M4hbod/hydrogram/issues/rich-text-annotations>`_
- Fifteen methods raised ``AttributeError: 'Updates' object has no attribute
  'messages'`` on every call, ``send_rich_message`` among them. They passed the
  result of an RPC that returns ``Updates`` straight to ``parse_messages``, which
  reads a ``messages`` vector that ``Updates`` does not have. A user sending to
  their own private chat gets the ``UpdateShortSentMessage`` shortcut, which the
  methods did handle, so the broken branch was only ever reached by bots and in
  groups. The new ``utils.parse_messages_from_updates`` reads the new messages out
  of an ``Updates``, and a contract test resolves every ``parse_messages``
  argument back to its RPC's declared return type.
  `#updates-responses-parsed <https://github.com/M4hbod/hydrogram/issues/updates-responses-parsed>`_


3.2.3 (2026-08-30)
===================

Bugfixes
--------

- Fixed five dispatcher update parsers that raised on every update they were
  routed. ``callback_query_parser`` passed four arguments to a three-argument
  ``CallbackQuery._parse``, killing every inline-keyboard button press;
  ``CallbackQuery._parse`` read ``game_short_name`` off business callback queries,
  which do not carry it; ``parse_deleted_messages`` read ``messages`` off
  ``UpdateDeleteEphemeralMessages``, which names the field ``ids``;
  ``deleted_business_messages_parser`` awaited a synchronous parser; and the
  ``Poll`` and ``Story`` parsers iterated raw fields that are optional in the
  schema and arrive as ``None``. Every one of these was swallowed by the handler
  worker, so the symptom was an update type that silently never fired.
  `#dispatcher-dead-parsers <https://github.com/M4hbod/hydrogram/issues/dispatcher-dead-parsers>`_
- Fixed two parsers that crashed on ordinary traffic by iterating a raw field the
  schema marks optional. ``Thumbnail._parse`` iterated ``Document.thumbs``, so
  every document without a thumbnail raised ``TypeError``, and
  ``ChatPreview._parse`` iterated ``ChatInvite.participants``, so every invite
  without a member preview did the same. A new contract test,
  ``test_optional_raw_fields_are_guarded``, resolves raw attribute chains against
  the generated schema across the whole package and fails on any unguarded
  iteration of an optional field.
  `#optional-raw-fields-guarded <https://github.com/M4hbod/hydrogram/issues/optional-raw-fields-guarded>`_
- ``ForumTopicCreated._parse`` read ``action`` off the raw message directly, which
  raises ``AttributeError`` for anything but a service message. Two ``_parse``
  annotations were also wrong in a way that hid the same class of defect:
  ``Chat._parse_full`` declared the un-namespaced full types while its body
  handles ``raw.types.users.UserFull`` and ``raw.types.messages.ChatFull``, and
  ``GiftAuctionState._parse`` declared ``raw.base.StarGiftAuctionState`` where the
  RPC returns ``raw.types.payments.StarGiftAuctionState``. A second check in
  ``test_optional_raw_fields_are_guarded`` now fails on any read of a field no
  constructor the annotated input can hold declares.
  `#raw-field-reads-checked <https://github.com/M4hbod/hydrogram/issues/raw-field-reads-checked>`_


3.2.2 (2026-08-30)
===================

Bugfixes
--------

- A client started, stopped, and started again under a different event loop
  crashed with ``RuntimeError: got Future attached to a different loop`` out of
  ``Session.send``. ``Client.loop`` was a ``functools.cached_property``, so the
  first access pinned a loop onto the instance for good; it resolves per access
  now. The dispatcher's update queue and the client's locks, semaphores and
  watchdog event had the same affinity and are rebuilt on each ``connect()``
  rather than in ``__init__``.



3.2.1 (2026-08-30)
===================

Features
--------

- ``Client`` takes ``client_platform``, an :obj:`~pyrogram.enums.ClientPlatform`
  reported when opening a web app. Defaults to ``OTHER``.



Bugfixes
--------

- Nine methods raised ``AttributeError`` or ``TypeError`` on every call.
  ``get_main_web_app``, ``open_web_app``, ``get_web_app_url`` and
  ``get_web_app_link_url`` read ``Client.client_platform``, which did not exist;
  ``get_upgraded_gift``, ``get_upgraded_gift_value_info`` and
  ``send_gift_purchase_offer`` read ``Client.UPGRADED_GIFT_RE``, and
  ``check_chat_folder_invite_link`` read ``Client.CHATLIST_INVITE_RE`` -- neither
  constant was defined. ``send_web_page`` forwarded ``quote_text``,
  ``quote_entities``, ``quote_offset``, ``reply_to_chat_id`` and
  ``reply_to_story_id`` to ``send_message``, which removed them in the Bot API 7
  migration.



Misc
----

- ``tests/contract/test_every_method_builds_a_request.py`` calls 211 client
  methods and asserts each reaches a request without raising. The harness before
  it returned a plausible reply and so had to parse one, which is why 75 methods
  skipped with "needs more client than the stub provides" -- and a method that
  skips is a method nobody has ever run. This one stops at the request instead,
  and uses a real ``Client`` with only ``invoke`` overridden, so nothing but the
  wire is stubbed. It found all nine dead methods above.



3.2.0 (2026-08-30)
===================

Features
--------

- 243 fields were missing from 22 types, ``Chat`` short by 118 and ``User`` by 76.
  Both now carry Kurigram's full field set and parse it: ``Chat`` gains
  ``emoji_status``, ``linked_chat_id``, ``slow_mode_delay``, ``level``,
  ``is_blocked``, ``folder_id``, ``message_auto_delete_time``, ``reactions_limit``,
  the ``business_*`` block and 100 more; ``User`` gains ``bio``, ``birthday``,
  ``personal_channel``, ``can_*`` rights and the rest. ``Sticker`` gains ``type``,
  ``mask_position``, ``custom_emoji_id``, ``needs_repainting`` and
  ``premium_animation``; ``ChatPermissions`` the eight per-media rights;
  ``KeyboardButton`` the ``request_users``/``request_chat`` buttons.



Misc
----

- ``tests/contract/test_type_fields.py`` compares every type's fields against a
  Kurigram checkout. The parity checks before it compared *names*, so ``Chat``
  counted as closed while missing 118 fields. Point ``KURIGRAM_PATH`` at a
  checkout to run it; without one it skips rather than reporting a gap it did not
  measure.



3.1.1 (2026-08-30)
===================

Bugfixes
--------

- Two documentation references named things that do not exist:
  ``enums.ChatEvenAction`` (a missing ``t``) in ``ChatEvent``, and
  ``MessageServiceType.VIDEO_CHAT_PARTICIPANTS_INVITED``, whose member is
  ``VIDEO_CHAT_MEMBERS_INVITED``. Both are the same typo class as the
  ``raw.pyrogram.ClientDHInnerData`` that broke fresh logins, found by the sweep
  added to catch it.

- ``Auth.create()`` referenced ``raw.pyrogram.ClientDHInnerData``, which does not exist (the
  constructor lives at ``raw.types.ClientDHInnerData``) -- a leftover from the whole-tree
  ``hydrogram`` -> ``pyrogram`` rename. Every DH key exchange failed, so no session could ever
  authenticate for the first time; a pre-existing session file masked it. Fixed, and
  ``tests/contract/test_raw_references.py`` now flags any ``raw.<namespace>.*`` reference whose
  namespace isn't one of ``types``/``functions``/``base``/``core``, which this typo did not trip
  before (its fixed namespace list only checked references it already recognized).



Misc
----

- ``Auth.create()`` is exercised for the first time.
  ``tests/integration/test_fresh_authorization.py`` logs in with no session file
  and asserts the DH exchange yields a 256-byte key. Every other test starts from
  a session string or file, both of which skip authorization entirely -- which is
  why a broken key exchange shipped in two releases without failing anything.



3.1.0 (2026-08-30)
===================

Features
--------

- The last thirteen parameters Kurigram had and this fork did not:
  ``add_contact(note=)``, ``search_messages(offset_id=)``,
  ``get_messages(pinned=, reply=)``, ``send_sticker(caption=, caption_entities=,
  parse_mode=)``, ``send_poll(description=, description_media=,
  explanation_media=)`` with its own ``description_parse_mode`` and
  ``description_entities``, ``edit_message_text(rich_message=)``,
  ``edit_inline_text(rich_message=, entities=)`` and
  ``forward_messages(reply_parameters=)``, which forwards a message as a reply.



Bugfixes
--------

- ``types.FormattedText(text=...)`` accepts a plain ``str``. It was annotated
  ``Str`` -- the ``str`` subclass the parser hands back -- which no caller passes.



3.0.0 (2026-08-29)
===================

Features
--------

- Added the `transfer_chat_ownershipt` method to the `Client`. This method allows the owner of a chat to transfer ownership to another user.
  `#43 <https://github.com/M4hbod/hydrogram/issues/43>`_
- 22 filters are added: ``admin``, ``business``, ``chat_shared``, ``direct``,
  ``ephemeral``, ``forum``, ``gift``, ``gift_code``, ``gift_offer``,
  ``gift_offer_accepted``, ``gift_offer_rejected``, ``giveaway``,
  ``giveaway_winners``, ``live_location``, ``paid_message``, ``quote``,
  ``self_destruction``, ``sender_chat``, ``story``, ``successful_payment``,
  ``topic`` and ``users_shared``. ``Chat`` gains ``is_admin``, which ``admin``
  reads.

- 96 types are added, closing the gap with Kurigram's type surface: privacy rules
  and ``GlobalPrivacySettings``, payment forms and credentials, gift collections,
  upgrades and craft results, business intro/hours/recipients, active sessions and
  authentication settings, chat folder invite links, group call members, boost
  status, story views, and the reply-keyboard request buttons. 66 of them were
  already named by shipped methods, which would have raised ``AttributeError`` on
  use.

- :obj:`~pyrogram.types.Message` now parses everything layer 229 can send. Attributes go from 79 to
  168, handled service actions from 18 to 67, and handled media types from 9 to 16 - checklists, paid
  media, suggested posts, business messages, giveaways, stories, gifts, boosts, reactions and the
  rest. 133 supporting types were added, along with the enum members they need
  (``MessageServiceType`` alone gains 53).

  ``Client`` gains ``fetch_replies``, ``fetch_topics``, ``fetch_stories`` and ``topic_cache_size``.
  ``fetch_topics`` and ``fetch_stories`` default to ``False`` until the chats and stories method
  groups land, because the paths they gate call methods that do not exist yet.

- Added 16 update handlers and their decorators: ``on_story``, ``on_message_reaction``,
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

- Added 28 enums, taking the public set from 15 to 43: ``BlockList``, ``BusinessSchedule``,
  ``ChatJoinRequestQueryResult``, ``ChatJoinType``, ``ChatPhotoStickerType``, ``ClientPlatform``,
  ``FolderColor``, ``GiftAttributeType``, ``GiftForResaleOrder``, ``GiftPurchaseOfferState``,
  ``GiftType``, ``MaskPointType``, ``MediaAreaType``, ``MessageOriginType``, ``PaidReactionPrivacy``,
  ``PaymentFormType``, ``PhoneCallDiscardReason``, ``PhoneNumberCodeType``, ``PrivacyKey``,
  ``PrivacyRuleType``, ``ProfileTab``, ``ProxyScheme``, ``StickerType``, ``StoriesPrivacyRules``,
  ``SuggestedPostRefundReason``, ``SuggestedPostState``, ``TopChatCategory`` and
  ``UpgradedGiftOrigin``.

  These are the value types the remaining API-surface work depends on. Enum member names and values
  are now frozen by a snapshot test, since renaming either is a breaking change nothing else would
  catch.

- Added 44 methods across five groups.

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

- Added :obj:`~pyrogram.types.ReplyParameters` and :obj:`~pyrogram.types.LinkPreviewOptions`, the
  parameter objects that replace the flat ``reply_to_message_id`` and ``disable_web_page_preview``
  arguments in the Bot API 7 model.

  They are the prerequisite for that migration rather than the migration itself: the send and edit
  methods still take the flat parameters for now. ``ReplyParameters`` expresses the combinations the
  flat argument could not -- quoting a substring with a position, replying to a story, an ephemeral
  message, a checklist task or a poll option -- and ``LinkPreviewOptions`` can choose a preview's URL
  and size instead of only switching it off.

- Added the 31 shared value types that the remaining API-surface work depends on: the gift cluster
  (:obj:`~pyrogram.types.Gift`, :obj:`~pyrogram.types.GiftAttribute`,
  :obj:`~pyrogram.types.GiftAuction`, the auction states, resale prices, purchase limits and upgraded
  gift rarities), :obj:`~pyrogram.types.Folder` and :obj:`~pyrogram.types.FolderInviteLink`,
  :obj:`~pyrogram.types.Invoice` and :obj:`~pyrogram.types.LabeledPrice`,
  :obj:`~pyrogram.types.SuggestedPostParameters` with its price variants,
  :obj:`~pyrogram.types.FormattedText` and :obj:`~pyrogram.types.Birthday`.

  ``utils.parse_text_with_entities`` was added alongside them - the read-side counterpart to
  ``parse_text_entities``, turning a received ``TextWithEntities`` into text plus high-level entities.

- Added the ``skip_updates`` client option. It defaults to ``True``, dropping updates that queued
  while the client was offline; pass ``False`` to receive them on connect. The ported dispatcher
  requires it.

- Added the remaining 154 methods, taking the public ``Client`` surface from 285 to 441 and closing
  the gap with Kurigram.

  **payments (44)** - gifts, stars, auctions, resale, gift collections, invoices, payment forms, star
  subscriptions and TON balances.
  **messages (41)** - checklists, paid media, paid reactions, scheduled messages, post search,
  translation, AI compose, web-app links, drafts, read/view marking and forwarding of media groups.
  **bots (27)** - invoices and invoice links, pre-checkout and shipping answers, bot info and name
  management, managed bots, ephemeral message editing, star payment refunds.
  **stories (21)** - send, edit, delete, forward and copy stories; pin, hide and read them; stealth
  mode and view lists.
  **account (10)** - privacy rules and keys, global privacy settings, account and session TTLs,
  profile audio.
  **auth (6)** - active sessions, session reset, phone-number change and code resending.
  **business (5)** - business connections, account gifts, star balance and transfers.

- New ``Client.recover_gaps()``: fetch the updates that arrived while the client
  was offline and feed them through the normal handler pipeline. ``Client`` now
  remembers each chat's update counters in an ``update_state`` table, which
  ``skip_updates=False`` catches up from at start and again whenever the updates
  watchdog fires. ``skip_updates=False`` previously raised ``AttributeError``: the
  dispatcher already called ``recover_gaps``, and the method did not exist.

- New ``Client.set_bot_profile_photo()``: set, replace or remove the profile photo
  or video of a bot you own.

- New ``pyrogram.crypto.faketls`` and
  ``pyrogram.connection.transport.tcp.faketls_records``: the ClientHello an ``ee``
  MTProxy secret is greeted with, and the TLS record layer the stream is cut into
  afterwards. The proxy's answer is authenticated against the secret, so a censor
  answering the greeting in its place is rejected rather than trusted.

- The ``proxy`` dict is validated when the ``Client`` is built rather than on the
  first connection attempt: an unknown scheme, a missing ``hostname``/``port``, or
  a secret that does not decode now raises ``ValueError`` immediately.

- The send, edit, copy and forward methods gain the layer-229 parameters they were
  missing: ``business_connection_id``, ``allow_paid_broadcast``,
  ``paid_message_star_count``, ``effect_id``, ``direct_messages_topic_id``,
  ``suggested_post_parameters``, ``repeat_period``, and ``receiver_user_id`` /
  ``callback_query_id`` for ephemeral messages. ``Client.invoke()`` takes
  ``business_connection_id`` and routes the request to the connection's own data
  centre; ``Client.get_session()`` is the reusable session lookup that makes that
  possible. The bound methods on ``Message`` and ``Story`` pass them through.

- Updated the MTProto API schema to layer 229.

  Keyboard buttons were redesigned in this layer: the eighteen flat ``= KeyboardButton;``
  constructors are replaced by two base types -- ``keyboardButton`` for reply keyboards and a new
  ``keyboardInlineButton`` for inline ones -- each carrying the kind in a discriminator union
  (``ButtonType`` and ``InlineButtonType``). The public :obj:`~pyrogram.types.InlineKeyboardButton`
  and :obj:`~pyrogram.types.KeyboardButton` API is unchanged, and ``style`` /
  ``icon_custom_emoji_id`` behave exactly as before.

  :obj:`~pyrogram.types.InlineKeyboardButton` also gains ``copy_text``, ``pay``, ``disabled`` and
  ``requires_password``, which the new union makes reachable. Button kinds that previously had no
  ``read()`` branch -- and so disappeared silently from parsed markup -- are now all handled.

- ``BaseStorage`` gains ``get_update_states``, ``set_update_state`` and
  ``delete_update_state``, and a ``UpdateState`` record to go with them. Custom
  storage engines must implement all three. SQLite session files are migrated to
  schema version 4 on open; nothing has to be done by hand.

- ``Client.send_reaction`` reacts to stories, via ``story_id``, and accepts custom
  emoji ids and lists of reactions as well as a single emoji string. ``Story.react``
  depended on the story path and raised ``TypeError`` without it.

- ``Client`` speaks Telegram's own MTProxy transport. Pass
  ``proxy=dict(scheme="mtproxy", hostname=..., port=..., secret=...)`` -- or the
  ``tg://proxy?...`` / ``https://t.me/proxy?...`` link itself, which is parsed
  into one. Plain 16-byte, ``dd`` (random padding) and ``ee`` (fake-TLS) secrets
  are all accepted, in hex or base64, and the secret picks the framing:
  ``TCPIntermediatePadded`` for a padded secret, ``TCPAbridgedO`` for a plain one.
  A ``tg://socks?...`` link is accepted for SOCKS5 the same way.

- ``Message`` gains 18 members: ``reply_dice``, ``reply_invoice``,
  ``reply_paid_media``, ``reply_checklist``, ``reply_rich``, ``edit_checklist``,
  ``edit_live_location``, ``stop_live_location``, ``copy_media_group``, ``read``,
  ``view``, ``summarize``, ``pay``, ``accept_gift_purchase_offer``,
  ``reject_gift_purchase_offer``, and the ``content``, ``html_text`` and
  ``md_text`` properties. Every ``reply_*`` also answers to ``answer_*``, the Bot
  API spelling -- the same method object under both names, not a second
  implementation. Kurigram's deprecated ``forward_from`` family is deliberately
  not ported; ``forward_origin`` carries the same information.

- ``send_poll`` takes ``allows_revoting``, ``shuffle_options``,
  ``hide_results_until_closes``, ``members_only``, ``allow_adding_options``,
  ``country_codes`` and ``correct_option_ids``. ``send_location`` sends live
  locations through ``live_period``, ``heading`` and ``proximity_alert_radius``.
  ``send_video`` takes ``video_cover`` and ``video_start_timestamp``,
  ``send_voice`` takes ``waveform``, ``send_sticker`` takes ``emoji``, and
  ``send_photo``/``send_video``/``send_video_note``/``send_voice`` take
  ``view_once``. ``get_chat_history`` takes ``reverse``, ``max_id`` and ``min_id``;
  ``get_chat`` takes ``force_full``; the search methods take date and id bounds and
  the ``users_only``/``groups_only``/``channels_only`` filters.



Bugfixes
--------

- Fixes a bug that caused the chat parser to return `ChatForbidden` or `ChannelForbidden` which caused some methods like `get_chat_history` to throw `AttributeError`.
  `#45 <https://github.com/M4hbod/hydrogram/issues/45>`_
- 13 bound methods raised ``TypeError`` on every call. Each passed keywords its
  client method does not accept -- all eleven ``Story.reply_*`` shortcuts, plus
  ``Story.react`` and two new ``Message`` ones -- because the bound methods were
  ported with Kurigram's signatures while the client methods stayed behind. The
  parameters that could not work are gone from both the call and the signature,
  and ``tests/contract/test_bound_method_delegation.py`` now walks every
  ``self._client.X(...)`` in the type tree and fails when a keyword is not in
  ``Client.X``'s signature.

- :meth:`Chat._parse_chat` now returns ``None`` for a missing peer instead of raising
  ``AttributeError``. Callers routinely look a peer up in the ``users``/``chats`` maps that arrive
  with an update and pass the result straight in; a miss yields ``None``, which fell through to the
  channel parser. :meth:`User._parse` already behaved this way.

- :meth:`str` on a type that keeps its source MTProto object no longer dumps it. Several types
  (:obj:`~pyrogram.types.Gift`, :obj:`~pyrogram.types.Invoice`, :obj:`~pyrogram.types.Folder`) hold
  the raw constructor they were parsed from as an escape hatch; it is enormous, it is an
  implementation detail, and it can carry fields the wrapper deliberately masks. ``Object.default``
  now hides it, as it already masked ``phone_number``.

- Eight update types never reached their handlers. The dispatcher routed them to
  ``pyrogram.types.PreCheckoutQuery``, ``ShippingQuery``, ``MessageReactionUpdated``,
  ``MessageReactionCountUpdated``, ``ChatBoostUpdated``, ``BusinessConnection``,
  ``ManagedBotUpdated`` and ``PurchasedPaidMedia`` -- none of which existed, so the
  ``AttributeError`` was logged and swallowed by the handler worker and
  ``@on_pre_checkout_query`` and friends simply never fired. All eight types are
  ported, and ``tests/contract/test_type_references.py`` now fails on any
  ``types.X`` that hand-written code names but the package does not define.

- Filters that read a field off the update no longer assume it is a ``Message``.
  ``filters.private``/``group``/``channel`` raised ``ValueError`` on any update
  that was not a ``Message`` or a ``CallbackQuery``, and ``incoming``/``outgoing``
  raised ``AttributeError``; both die inside the handler worker, where they are
  logged and swallowed, so the handler just never runs. Each field is now taken
  only from the update types that carry it -- ``me``, ``bot``, ``incoming``,
  ``outgoing`` and the chat-type filters work across the whole update surface and
  simply do not match where the field is absent.

- Five update parsers never reached their handlers. The dispatcher awaits whatever
  its routing table returns, and ``user_status``, ``inline_query``,
  ``chosen_inline_result``, ``chat_member_updated`` and ``chat_join_request`` were
  plain functions returning a tuple -- awaiting which raises inside the handler
  worker, where it is logged and swallowed. ``deleted_messages`` was called with
  four arguments where ``utils.parse_deleted_messages`` takes two.

- Fixed :obj:`~pyrogram.types.InlineKeyboardButton` silently dropping ``style`` and
  ``icon_custom_emoji_id`` on buttons that use ``login_url``. ``LoginUrl.write()`` accepted no style
  argument, so the value computed by the caller was discarded for that branch alone.

- Fixed crashes parsing users, chats and messages that omit a flags-gated vector.
  ``User._parse`` and ``Chat._parse_*`` iterated ``usernames`` and ``restriction_reason``
  unconditionally, and ``Message`` did the same with ``entities`` - all of which are absent rather
  than empty for the many peers and messages that have none. ``getattr(obj, "field", [])`` was also
  used in nine places where it cannot work: the attribute exists and holds ``None``, so the default
  never applies.

- Fixed every forum-topic method and :meth:`~pyrogram.Client.transfer_chat_ownership` raising
  ``AttributeError`` at call time. They invoked ``raw.functions.channels.*``, but Telegram moved
  ``createForumTopic``, ``editForumTopic``, ``getForumTopics``, ``getForumTopicsByID`` and
  ``deleteTopicHistory`` to the ``messages`` namespace (taking ``peer`` rather than ``channel``), and
  replaced ``channels.editCreator`` with ``messages.editChatCreator``.

- Fixed serialization of any TL object with an optional ``Vector`` field that had been deserialized
  first. ``read()`` gives an absent ``flags.n?Vector<T>`` the value ``[]``, but the generated
  ``write()`` guarded the body on ``is not None`` while the flag bit was computed by truthiness, so
  re-serializing wrote an empty vector with no flag set - eight stray bytes that desynchronized every
  field after it. 97 generated types were affected.

- Fixed the updates watchdog and the session reconnect throttle measuring elapsed time with a wall
  clock. Both used ``datetime.now()``, which steps at DST boundaries, on NTP corrections and when the
  system time is set: a backward step stalled the watchdog for the length of the step and made the
  reconnect throttle see a negative interval, so it throttled every attempt. Both now use
  ``time.monotonic()``.

  ``Session.RECONNECT_THRESHOLD`` is consequently a number of seconds (``10.0``) rather than a
  ``timedelta``, and the throttle tests ``is not None`` rather than truthiness -- a monotonic reading
  of ``0.0`` is legitimate and would previously have disabled the throttle.

- ``@on_chat_boost`` registered a ``ShippingQueryHandler`` rather than a ``ChatBoostHandler``, so the
  decorated callback would never have fired for a boost and would have fired for shipping queries
  instead. The bug came in with the ported decorator and was caught by a test asserting every
  decorator registers its own handler.

- ``Client.message_cache`` is now a proper LRU guarded by a lock. It was an unlocked dict that, once
  full, discarded *half* its contents at once - so a burst of traffic threw away entries that were
  still in use. Access is now ``await client.message_cache.get(key)`` / ``.set(key, value)`` rather
  than subscripting.

- ``SQLiteStorage.close()`` commits before closing. SQLite rolls an open
  transaction back on close, so anything written without an explicit commit --
  which now includes every chat's update counters -- was discarded exactly when
  it was needed, on the next start.

- ``delete_forum_topic`` no longer swallows every exception. It caught all errors, printed them to
  stdout and returned ``False``, so a ``FloodWait`` looked identical to "the topic was not deleted" --
  and a caller retrying on ``False`` would hammer straight through the flood wait. Errors now
  propagate, matching every other forum-topic method.

- ``pin_forum_topic`` and ``unpin_forum_topic`` raised ``TypeError`` on every call:
  they passed ``channel=`` to ``messages.UpdatePinnedForumTopic``, whose field is
  ``peer``. ``tests/contract/test_raw_keywords.py`` now checks every keyword handed
  to a raw constructor against that constructor's signature.

- ``pin_forum_topic`` called ``raw.functions.channels.UpdatePinnedForumTopic``, which does not exist
  at layer 229 - Telegram moved it to the ``messages`` namespace along with the rest of the
  forum-topic RPCs. It would have raised ``AttributeError`` on the first call.

- ``send_paid_media`` passed ``direct_messages_topic_id`` into
  ``get_reply_to``'s ``message_thread_id`` slot, scoping the message to the wrong
  topic. ``tests/contract/test_parameters_are_used.py`` now fails when a method
  declares a parameter its own body never reads -- an option accepted and silently
  dropped is worse than one that is missing.

- ``send_poll`` raised ``TypeError`` on every call since the layer-229 bump:
  ``raw.types.Poll`` gained a required ``hash`` field and the request did not pass
  it. Parsing the reply then failed too -- ``Poll._parse`` built ``PollOption``
  with seven fields it did not have, so any poll reaching the parser raised inside
  the handler worker. ``PollOption`` now carries the full set (persistent id,
  media, vote percentage, recent voters, who added the option and when).

- ``types.Location`` accepts ``client``. Two inline-query parsers passed it and
  raised ``TypeError``, which meant an inline query carrying a location never
  reached its handler.



Improved Documentation
----------------------

- Corrected the documentation for :obj:`~pyrogram.types.InlineKeyboardButton`'s ``style`` and
  ``icon_custom_emoji_id``. Both were documented as requiring the bot owner to have Telegram Premium.
  Verified against production Telegram from a non-Premium bot owner: ``style`` works and has no such
  requirement, while ``icon_custom_emoji_id`` is accepted and then **silently dropped** by the server
  -- the message sends without error and the button reads back with no icon.



Deprecations and Removals
-------------------------

- **Breaking.** Dates returned by the library are now timezone-aware UTC.

  :func:`~pyrogram.utils.timestamp_to_datetime` -- and therefore every date on a parsed object, such
  as ``Message.date`` and ``Message.edit_date`` -- previously returned a *naive local* datetime while
  :func:`~pyrogram.utils.zero_datetime` returned an aware UTC one. The two could not be compared:
  checking a message date against the library's own default for ``until_date`` or ``offset_date``
  raised ``TypeError: can't compare offset-naive and offset-aware datetimes``.

  Telegram sends dates as Unix timestamps, which are instants rather than wall-clock readings, so the
  aware form is the accurate one. Code that compares a message date against a naive datetime now
  raises ``TypeError`` instead of silently working; use ``datetime.now(timezone.utc)`` in place of
  ``datetime.now()``, or call ``.astimezone()`` on the message date to render it locally.

  Datetimes *passed to* the library are unchanged: an aware one converts exactly, and a naive one is
  still read as local time, matching ``datetime.now()``.

- **Breaking.** ``reply_to_message_id`` and ``disable_web_page_preview`` are removed from every send
  and edit method, replaced by :obj:`~pyrogram.types.ReplyParameters` and
  :obj:`~pyrogram.types.LinkPreviewOptions`. There are no deprecation shims: passing the old names
  raises ``TypeError``.

  The exhaustive list, so the downstream sweep is a grep:

  * ``reply_to_message_id=N`` becomes ``reply_parameters=ReplyParameters(message_id=N)``. Affects
    ``send_message``, ``send_photo``, ``send_audio``, ``send_document``, ``send_sticker``,
    ``send_video``, ``send_animation``, ``send_voice``, ``send_video_note``, ``send_location``,
    ``send_venue``, ``send_contact``, ``send_dice``, ``send_poll``, ``send_media_group``,
    ``send_cached_media``, ``send_game``, ``send_inline_bot_result``, ``copy_message``,
    ``copy_media_group``, and the 18 ``Message.reply_*`` bound methods.
  * ``disable_web_page_preview=True`` becomes
    ``link_preview_options=LinkPreviewOptions(is_disabled=True)``. Affects ``send_message``,
    ``edit_message_text``, ``edit_inline_text``, :obj:`~pyrogram.types.InputTextMessageContent` and
    ``CallbackQuery.edit_message_text``.

  Two things that keep the old spelling and are **not** affected: the ``Message.reply_to_message_id``
  attribute, which describes an incoming message, and ``get_messages(reply_to_message_ids=...)``,
  which fetches replies.

  The replacements do more than the parameters they retire. ``ReplyParameters`` can quote a substring
  at a given UTF-16 position, and can reply to a story, an ephemeral message, a checklist task or a
  poll option. ``LinkPreviewOptions`` can choose which URL is previewed, prefer a larger or smaller
  image, and place the preview above the text -- a message with an explicit preview URL is now sent
  through ``messages.sendMedia`` with an ``InputMediaWebPage``, which is the only way to express it.

- ``pysocks`` is replaced by ``python-socks[asyncio]``. The SOCKS and HTTP proxy
  handshake was synchronous and ran on the event loop, blocking every other task
  for its duration -- long enough to deadlock outright against a proxy served
  from the same loop. Proxy failures now raise ``python_socks.ProxyError`` with
  the reason rather than a bare ``TimeoutError``. The ``proxy`` dict is unchanged.



Misc
----

- Defer loop obtaining to when it's actually used.
  `#49 <https://github.com/M4hbod/hydrogram/issues/49>`_


0.2.0 (2024-06-30)
===================

Deprecations and Removals
-------------------------

- Removed the `async-to-sync` wrapper, making the library fully asynchronous.
- Removed the `emoji` submodule. Please try out the `emoji` package from PyPI.

Features
--------

- Integrate pyromod patches into the project (many thanks to @usernein for his excellent work). To check out the pyromod specific features, have a look at https://pyromod.pauxis.dev/.
  You can use the features in the same way as in pyromod, except that you import them directly from the pyrogram package.
  `#1 <https://github.com/pyrogram/pyrogram/issues/1>`_
- Changed the minimum required version of Python to 3.9 and integrated the newest Python type hints.
  `#5 <https://github.com/pyrogram/pyrogram/issues/5>`_
- Added the attribute `is_participants_hidden` to the `Chat` type. If the list of members is hidden, `True` will be returned; otherwise, `False` will be returned.
  `#11 <https://github.com/pyrogram/pyrogram/issues/11>`_
- Allowed the use of filters.{private,group,channel} in callback queries.
  `#32 <https://github.com/pyrogram/pyrogram/issues/32>`_
- Added the `ChatBackground` type and the `background` field for the `Chat` object.
  `#33 <https://github.com/pyrogram/pyrogram/issues/33>`_
- Added support for error handlers.
  `#38 <https://github.com/pyrogram/pyrogram/issues/38>`_


Bugfixes
--------

- Fixed `Message.is_scheduled` field being always `False` when parsing `UpdateNewScheduledMessage`.
  `#14 <https://github.com/pyrogram/pyrogram/issues/14>`_
- Fixed an issue with the bool parsing of the raw api that was causing the wrong value to be returned.
  `#20 <https://github.com/pyrogram/pyrogram/issues/20>`_
- Make the quiz explanation an optional parameter.
  `#21 <https://github.com/pyrogram/pyrogram/issues/21>`_
- Support newly-created chats by increating `MIN_CHANNEL_ID` and `MIN_CHAT_ID`.
  `#25 <https://github.com/pyrogram/pyrogram/issues/25>`_


Improved Documentation
----------------------

- Added a tool to extract documentation parameters from the Telegram documentation, allowing us to self-host raw API documentation.
  `#34 <https://github.com/pyrogram/pyrogram/issues/34>`_


Misc
----

- Make `Message._parse` accept only keyword-only arguments.
  `#14 <https://github.com/pyrogram/pyrogram/issues/14>`_
- Added `if TYPE_CHECKING` to import modules for type checking only when needed. This flag avoids importing modules that are not needed for runtime execution. This change reduces the number of imports in the module and improves the performance of the code.
  `#24 <https://github.com/pyrogram/pyrogram/issues/24>`_
- Added the `from __future__ import annotations` statement to the codebase in order to simplify the usage of the typing module. This statement allows for the use of forward references in type hints, which can improve code readability and maintainability.
  `#24 <https://github.com/pyrogram/pyrogram/issues/24>`_
- Various fixes, improvements and micro-optimizations.



0.1.4 (2023-12-04)
===================

Bugfixes
--------

- Fix a boolean instead of file name in send_audio
  `#4 <https://github.com/pyrogram/pyrogram/issues/4>`_
- Prevent from closing BytesIO object in handle_download
  `#4 <https://github.com/pyrogram/pyrogram/issues/4>`_


0.1.3 (2023-12-03)
===================

Bugfixes
--------

- Fix handle_download file name
  `#3 <https://github.com/pyrogram/pyrogram/issues/3>`_


0.1.2 (2023-12-03)
===================

Bugfixes
--------

- Fix save_file reporting size as 0


0.1.1 (2023-12-01)
===================

Fixup release that fixes our logo url in PyPI.


0.1.0 (2023-12-01)
===================

Initial project release. To see all changes and improvements compared to Pyrogram, see `Pyrogram vs Pyrogram <https://pyrogram.org/en/latest/pyrogram-vs-pyrogram.html>`_
