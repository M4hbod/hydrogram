``send_poll`` takes ``allows_revoting``, ``shuffle_options``,
``hide_results_until_closes``, ``members_only``, ``allow_adding_options``,
``country_codes`` and ``correct_option_ids``. ``send_location`` sends live
locations through ``live_period``, ``heading`` and ``proximity_alert_radius``.
``send_video`` takes ``video_cover`` and ``video_start_timestamp``,
``send_voice`` takes ``waveform``, ``send_sticker`` takes ``emoji``, and
``send_photo``/``send_video``/``send_video_note``/``send_voice`` take
``view_once``. ``get_chat_history`` takes ``reverse``, ``max_id`` and ``min_id``;
``get_chat`` takes ``force_full``; the search methods take date and id bounds and
the ``users_only``/``groups_only``/``channels_only`` filters.
