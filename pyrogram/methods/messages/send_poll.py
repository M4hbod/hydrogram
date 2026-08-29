#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import TYPE_CHECKING

import pyrogram
from pyrogram import enums, raw, types, utils

if TYPE_CHECKING:
    from datetime import datetime


class SendPoll:
    async def send_poll(
        self: pyrogram.Client,
        chat_id: int | str,
        question: str,
        options: list[types.InputPollOption],
        *,
        question_parse_mode: enums.ParseMode = None,
        question_entities: list[types.MessageEntity] | None = None,
        message_thread_id: int | None = None,
        is_anonymous: bool = True,
        type: enums.PollType = enums.PollType.REGULAR,
        allows_multiple_answers: bool | None = None,
        correct_option_id: int | None = None,
        explanation: str | None = None,
        explanation_parse_mode: enums.ParseMode = None,
        explanation_entities: list[types.MessageEntity] | None = None,
        open_period: int | None = None,
        close_date: datetime | None = None,
        is_closed: bool | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_parameters: types.ReplyParameters | None = None,
        schedule_date: datetime | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
        direct_messages_topic_id: int | None = None,
        effect_id: int | None = None,
        repeat_period: int | None = None,
        allow_paid_broadcast: bool | None = None,
        paid_message_star_count: int | None = None,
        suggested_post_parameters: types.SuggestedPostParameters | None = None,
        business_connection_id: str | None = None,
    ) -> types.Message:
        """Send a new poll.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            question (``str``):
                Poll question, 1-255 characters.

            options (List of :obj:`~pyrogram.types.InputPollOption`):
                List of answer options, 2-10 answer options,  1-100 characters for each option.

            question_parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            question_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the poll question, which can be specified instead of *question_parse_mode*.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            is_anonymous (``bool``, *optional*):
                True, if the poll needs to be anonymous.
                Defaults to True.

            type (:obj`~pyrogram.enums.PollType`, *optional*):
                Poll type, :obj:`~pyrogram.enums.PollType.QUIZ` or :obj:`~pyrogram.enums.PollType.REGULAR`.
                Defaults to :obj:`~pyrogram.enums.PollType.REGULAR`.

            allows_multiple_answers (``bool``, *optional*):
                True, if the poll allows multiple answers, ignored for polls in quiz mode.
                Defaults to False.

            correct_option_id (``int``, *optional*):
                0-based identifier of the correct answer option, required for polls in quiz mode.

            explanation (``str``, *optional*):
                Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style
                poll, 0-200 characters with at most 2 line feeds after entities parsing.

            explanation_parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            explanation_entities (List of :obj:`~pyrogram.types.MessageEntity`):
                List of special entities that appear in the poll explanation, which can be specified instead of
                *parse_mode*.

            open_period (``int``, *optional*):
                Amount of time in seconds the poll will be active after creation, 5-600.
                Can't be used together with *close_date*.

            close_date (:py:obj:`~datetime.datetime`, *optional*):
                Point in time when the poll will be automatically closed.
                Must be at least 5 and no more than 600 seconds in the future.
                Can't be used together with *open_period*.

            is_closed (``bool``, *optional*):
                Pass True, if the poll needs to be immediately closed.
                This can be useful for poll preview.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_parameters (:obj:`~pyrogram.types.ReplyParameters`, *optional*):
                Description of the message to reply to.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            direct_messages_topic_id (``int``, *optional*):
                Unique identifier of the direct messages topic to send the message to.

            effect_id (``int``, *optional*):
                Unique identifier of the message effect to be added to the message.

            repeat_period (``int``, *optional*):
                Period in seconds for which a scheduled message should be repeated.

            allow_paid_broadcast (``bool``, *optional*):
                Pass True to bypass the broadcast rate limit for a fee, charged to the bot's Telegram Star balance.

            paid_message_star_count (``int``, *optional*):
                Number of Telegram Stars the sender is willing to pay to send the message, when the chat charges for incoming messages.

            suggested_post_parameters (:obj:`~pyrogram.types.SuggestedPostParameters`, *optional*):
                Parameters of the suggested post this message proposes. Channel direct messages only.

            business_connection_id (``str``, *optional*):
                Unique identifier of the business connection to send the message on behalf of.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent poll message is returned.

        Example:
            .. code-block:: python

                await app.send_poll(chat_id, "Is this a poll question?", ["Yes", "No", "Maybe"])
        """

        solution, solution_entities = (
            (
                await utils.parse_text_entities(
                    self, explanation, explanation_parse_mode, explanation_entities
                )
            ).values()
            if explanation
            else (None, None)
        )

        reply_to = await utils.get_reply_to(
            self, reply_parameters, message_thread_id, direct_messages_topic_id
        )

        question, question_entities = (
            await utils.parse_text_entities(self, question, question_parse_mode, question_entities)
        ).values()
        if not question_entities:
            question_entities = []

        answers = []
        for i, answer_ in enumerate(options):
            if isinstance(answer_, str):
                answer, answer_entities = answer_, []
            else:
                answer, answer_entities = (
                    await utils.parse_text_entities(
                        self, answer_.text, answer_.text_parse_mode, answer_.text_entities
                    )
                ).values()
                if not answer_entities:
                    answer_entities = []
            answers.append(
                raw.types.PollAnswer(
                    text=raw.types.TextWithEntities(text=answer, entities=answer_entities),
                    option=bytes([i]),
                )
            )

        r = await self.invoke(
            raw.functions.messages.SendMedia(
                peer=await self.resolve_peer(chat_id),
                media=raw.types.InputMediaPoll(
                    poll=raw.types.Poll(
                        id=self.rnd_id(),
                        question=raw.types.TextWithEntities(
                            text=question, entities=question_entities
                        ),
                        answers=answers,
                        closed=is_closed,
                        public_voters=not is_anonymous,
                        multiple_choice=allows_multiple_answers,
                        quiz=type == enums.PollType.QUIZ or False,
                        close_period=open_period,
                        close_date=utils.datetime_to_timestamp(close_date),
                    ),
                    correct_answers=[bytes([correct_option_id])]
                    if correct_option_id is not None
                    else None,
                    solution=solution,
                    solution_entities=None if solution is None else (solution_entities or []),
                ),
                message="",
                silent=disable_notification,
                reply_to=reply_to,
                random_id=self.rnd_id(),
                suggested_post=suggested_post_parameters.write()
                if suggested_post_parameters
                else None,
                allow_paid_stars=paid_message_star_count,
                allow_paid_floodskip=allow_paid_broadcast,
                schedule_repeat_period=repeat_period,
                effect=effect_id,
                schedule_date=utils.datetime_to_timestamp(schedule_date),
                noforwards=protect_content,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
            ),
            business_connection_id=business_connection_id,
        )

        for i in r.updates:
            if isinstance(
                i,
                (
                    raw.types.UpdateNewMessage,
                    raw.types.UpdateNewChannelMessage,
                    raw.types.UpdateNewScheduledMessage,
                ),
            ):
                return await types.Message._parse(
                    client=self,
                    message=i.message,
                    users={i.id: i for i in r.users},
                    chats={i.id: i for i in r.chats},
                    is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage),
                )
        return None
