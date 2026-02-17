#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
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

import asyncio
import inspect
import logging
from collections import OrderedDict
from typing import Any

import pyrogram
from pyrogram import utils, types, raw
from pyrogram.handlers import (
    CallbackQueryHandler, MessageHandler, EditedMessageHandler, ErrorHandler, DeletedMessagesHandler,
    UserStatusHandler, RawUpdateHandler, InlineQueryHandler, PollHandler,
    ChosenInlineResultHandler, ChatMemberUpdatedHandler, ChatJoinRequestHandler, StoryHandler
)

log = logging.getLogger(__name__)


class Dispatcher:
    NEW_MESSAGE_UPDATES = (raw.types.UpdateNewMessage, raw.types.UpdateNewChannelMessage, raw.types.UpdateNewScheduledMessage)
    EDIT_MESSAGE_UPDATES = (raw.types.UpdateEditMessage, raw.types.UpdateEditChannelMessage)
    DELETE_MESSAGES_UPDATES = (raw.types.UpdateDeleteMessages, raw.types.UpdateDeleteChannelMessages)
    CALLBACK_QUERY_UPDATES = (raw.types.UpdateBotCallbackQuery, raw.types.UpdateInlineBotCallbackQuery)
    CHAT_MEMBER_UPDATES = (raw.types.UpdateChatParticipant, raw.types.UpdateChannelParticipant)
    USER_STATUS_UPDATES = (raw.types.UpdateUserStatus,)
    BOT_INLINE_QUERY_UPDATES = (raw.types.UpdateBotInlineQuery,)
    POLL_UPDATES = (raw.types.UpdateMessagePoll,)
    CHOSEN_INLINE_RESULT_UPDATES = (raw.types.UpdateBotInlineSend,)
    CHAT_JOIN_REQUEST_UPDATES = (raw.types.UpdateBotChatInviteRequester,)
    NEW_STORY_UPDATES = (raw.types.UpdateStory,)

    def __init__(self, client: "pyrogram.Client"):
        self.client = client
        self.loop = asyncio.get_event_loop()

        self.handler_worker_tasks = []
        self.locks_list = []
        self.error_handlers = []

        self.updates_queue = asyncio.Queue()
        self.groups = OrderedDict()

        async def message_parser(update, users, chats):
            return (
                await pyrogram.types.Message._parse(self.client, update.message, users, chats, None,
                                                    isinstance(update, raw.types.UpdateNewScheduledMessage)),
                MessageHandler
            )

        async def edited_message_parser(update, users, chats):
            # Edited messages are parsed the same way as new messages, but the handler is different
            parsed, _ = await message_parser(update, users, chats)

            return (
                parsed,
                EditedMessageHandler
            )

        async def deleted_messages_parser(update, users, chats):
            return (
                utils.parse_deleted_messages(self.client, update),
                DeletedMessagesHandler
            )

        async def callback_query_parser(update, users, chats):
            return (
                await pyrogram.types.CallbackQuery._parse(self.client, update, users, chats),
                CallbackQueryHandler
            )

        async def user_status_parser(update, users, chats):
            return (
                pyrogram.types.User._parse_user_status(self.client, update),
                UserStatusHandler
            )

        async def inline_query_parser(update, users, chats):
            return (
                pyrogram.types.InlineQuery._parse(self.client, update, users),
                InlineQueryHandler
            )

        async def poll_parser(update, users, chats):
            return (
                pyrogram.types.Poll._parse_update(self.client, update),
                PollHandler
            )

        async def chosen_inline_result_parser(update, users, chats):
            return (
                pyrogram.types.ChosenInlineResult._parse(self.client, update, users),
                ChosenInlineResultHandler
            )

        async def chat_member_updated_parser(update, users, chats):
            return (
                pyrogram.types.ChatMemberUpdated._parse(self.client, update, users, chats),
                ChatMemberUpdatedHandler
            )

        async def chat_join_request_parser(update, users, chats):
            return (
                pyrogram.types.ChatJoinRequest._parse(self.client, update, users, chats),
                ChatJoinRequestHandler
            )

        async def story_parser(update, users, chats):
            return (
                await pyrogram.types.Story._parse(self.client, update.story, users, chats, update.peer),
                StoryHandler
            )

        self.update_parsers = {
            Dispatcher.NEW_MESSAGE_UPDATES: message_parser,
            Dispatcher.EDIT_MESSAGE_UPDATES: edited_message_parser,
            Dispatcher.DELETE_MESSAGES_UPDATES: deleted_messages_parser,
            Dispatcher.CALLBACK_QUERY_UPDATES: callback_query_parser,
            Dispatcher.USER_STATUS_UPDATES: user_status_parser,
            Dispatcher.BOT_INLINE_QUERY_UPDATES: inline_query_parser,
            Dispatcher.POLL_UPDATES: poll_parser,
            Dispatcher.CHOSEN_INLINE_RESULT_UPDATES: chosen_inline_result_parser,
            Dispatcher.CHAT_MEMBER_UPDATES: chat_member_updated_parser,
            Dispatcher.CHAT_JOIN_REQUEST_UPDATES: chat_join_request_parser,
            Dispatcher.NEW_STORY_UPDATES: story_parser
        }

        self.update_parsers = {key: value for key_tuple, value in self.update_parsers.items() for key in key_tuple}

    async def start(self):
        if not self.client.no_updates:
            for i in range(self.client.workers):
                self.locks_list.append(asyncio.Lock())

                self.handler_worker_tasks.append(
                    self.loop.create_task(self.handler_worker(self.locks_list[-1]))
                )

            log.info("Started %s HandlerTasks", self.client.workers)

    async def stop(self):
        if not self.client.no_updates:
            for i in range(self.client.workers):
                self.updates_queue.put_nowait(None)

            for i in self.handler_worker_tasks:
                await i

            self.handler_worker_tasks.clear()
            self.groups.clear()
            self.error_handlers.clear()

            log.info("Stopped %s HandlerTasks", self.client.workers)

    def add_handler(self, handler, group: int):
        async def fn():
            for lock in self.locks_list:
                await lock.acquire()

            try:
                if isinstance(handler, ErrorHandler):
                    if handler not in self.error_handlers:
                        self.error_handlers.append(handler)
                else:
                    if group not in self.groups:
                        self.groups[group] = []
                        self.groups = OrderedDict(sorted(self.groups.items()))
                    self.groups[group].append(handler)
            finally:
                for lock in self.locks_list:
                    lock.release()

        self.loop.create_task(fn())

    def remove_handler(self, handler, group: int):
        async def fn():
            for lock in self.locks_list:
                await lock.acquire()

            try:
                if isinstance(handler, ErrorHandler):
                    if handler not in self.error_handlers:
                        raise ValueError(
                            f"Error handler {handler} does not exist. Handler was not removed."
                        )
                    self.error_handlers.remove(handler)
                else:
                    if group not in self.groups:
                        raise ValueError(f"Group {group} does not exist. Handler was not removed.")
                    self.groups[group].remove(handler)
            finally:
                for lock in self.locks_list:
                    lock.release()

    async def handler_worker(self, lock: asyncio.Lock):
        while True:
            packet = await self.updates_queue.get()

            if packet is None:
                break

            try:
                await self._handle_packet(packet, lock)
            except pyrogram.StopPropagation:
                pass
            except Exception as e:
                log.exception(e)
            finally:
                self.updates_queue.task_done()
    
    async def _handle_packet(self, packet, lock: asyncio.Lock):
        update, users, chats = packet
        parser = self.update_parsers.get(type(update))

        try:
            parsed_update, handler_type = (
                await parser(update, users, chats)
                if parser is not None
                else (None, type(None))
            )
        except (KeyError, IndexError):
            return
        except Exception as e:
            log.exception(e)
            return
        async with lock:
            await self._dispatch_to_handlers(update, users, chats, parsed_update, handler_type)


    async def _dispatch_to_handlers(
        self, update, users, chats, parsed_update, handler_type,
    ):
        for group in self.groups.values():
            for handler in group:
                args = await self._match_handler(
                    handler, update, users, chats, parsed_update, handler_type,
                )
                if args is None:
                    continue

                try:
                    await self._execute_handler(handler, *args)
                except pyrogram.StopPropagation:
                    raise
                except pyrogram.ContinuePropagation:
                    continue
                except Exception as error:
                    if parsed_update is not None:
                        await self._handle_exception(parsed_update, error)
                break

    async def _match_handler(
        self, handler, update, users, chats, parsed_update, handler_type,
    ):
        try:
            if isinstance(handler, handler_type):
                if await handler.check(self.client, parsed_update):
                    return (parsed_update,)
            elif isinstance(handler, RawUpdateHandler):
                if await handler.check(self.client, update):
                    return (update, users, chats)
        except Exception as e:
            log.exception(e)

        return None

    async def _execute_handler(self, handler, *args: Any):
        if inspect.iscoroutinefunction(handler.callback):
            await handler.callback(self.client, *args)
        else:
            await self.loop.run_in_executor(
                self.client.executor,
                handler.callback,
                self.client,
                *args
            )

    async def _handle_exception(
        self, parsed_update: types.Update, exception: Exception,
    ):
        handled_error = False
        for error_handler in self.error_handlers:
            try:
                if await error_handler.check(
                    self.client, parsed_update, exception,
                ):
                    handled_error = True
                    break
            except pyrogram.StopPropagation:
                raise
            except pyrogram.ContinuePropagation:
                continue
            except Exception as inner_exception:
                log.exception("Error in error handler: %s", inner_exception)

        if not handled_error:
            log.exception("Unhandled exception: %s", exception)
