``Message`` gains 18 members: ``reply_dice``, ``reply_invoice``,
``reply_paid_media``, ``reply_checklist``, ``reply_rich``, ``edit_checklist``,
``edit_live_location``, ``stop_live_location``, ``copy_media_group``, ``read``,
``view``, ``summarize``, ``pay``, ``accept_gift_purchase_offer``,
``reject_gift_purchase_offer``, and the ``content``, ``html_text`` and
``md_text`` properties. Every ``reply_*`` also answers to ``answer_*``, the Bot
API spelling -- the same method object under both names, not a second
implementation. Kurigram's deprecated ``forward_from`` family is deliberately
not ported; ``forward_origin`` carries the same information.
