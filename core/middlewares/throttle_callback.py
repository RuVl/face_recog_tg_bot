import logging
from typing import Awaitable, Any, Callable

from aiogram import BaseMiddleware
from aiogram import types
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.fsm.storage.base import BaseStorage


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, storage: BaseStorage, key_prefix: str = '_antiflood'):
        self.prefix = key_prefix
        self.storage = storage

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

        # Build key
        key = f'{self.prefix}:{event.message.chat.id}{event.from_user}:was_pressed'
        was_pressed: bool = await self.storage.get_data(key=key)

        if was_pressed:
            await event.answer()
            raise CancelHandler()  # Cancel current handler

        await self.storage.set_data(key=key, data=True)

        try:
            result = await handler(event, data)
        finally:
            await self.storage.set_data(key=key, data=False)

        return result
