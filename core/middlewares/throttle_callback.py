import logging
from typing import Awaitable, Any, Callable

from aiogram import BaseMiddleware
from aiogram import types
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.storage.base import StorageKey

from core.misc.utils import get_storage


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, prefix: str = 'antiflood'):
        self.storage = get_storage(key_builder_prefix=prefix)
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

        was_pressed: bool = await self.storage.get_data(key=key)

        if was_pressed:
            logging.info('Callback was skipped')

            await event.answer()
            raise SkipHandler()

        logging.info("Callback wasn't skipped")

        await self.storage.set_data(key=key, data=True)

        try:
            result = await handler(event, data)
        except Exception as e:
            raise e
        finally:
            await self.storage.set_data(key=key, data=False)

        return result
