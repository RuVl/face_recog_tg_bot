import logging
from datetime import datetime, timedelta
from typing import Awaitable, Any, Callable

from aiogram import BaseMiddleware
from aiogram import types
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.fsm.storage.base import StorageKey

from core.misc.utils import get_storage


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, prefix: str = 'antiflood', timeout=timedelta(seconds=5)):
        self.storage = get_storage(key_builder_prefix=prefix)
        self.timeout = timeout
        
        super(ThrottlingMiddleware, self).__init__()

    async def __call__(
            self,
            handler: Callable[[types.CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: types.CallbackQuery,
            data: dict[str, Any]
    ) -> Any:
        if not isinstance(event, types.CallbackQuery):
            logging.warning("ThrottlingMiddleware is only CallbackQuery Middleware!")
            return await handler(event, data)

        # key for KeyBuilder
        key = StorageKey(
            bot_id=event.bot.id,
            chat_id=event.message.chat.id,
            user_id=event.message.from_user.id
        )

        now_ = datetime.now()
        antiflood_data: dict = await self.storage.get_data(key=key) or {}

        antiflood_data.setdefault('response_received', False)
        antiflood_data.setdefault('callback_time', now_)

        # Cancel handler
        if not antiflood_data.get('response_received') and now_ - antiflood_data['callback_time'] < self.timeout:
            await event.answer()
            raise CancelHandler()

        await self.storage.set_data(key=key, data=antiflood_data)

        try:
            result = await handler(event, data)
        finally:
            antiflood_data['response_received'] = True
            await self.storage.set_data(key=key, data=antiflood_data)

        return result

    async def close(self) -> None:
        await self.storage.close()
