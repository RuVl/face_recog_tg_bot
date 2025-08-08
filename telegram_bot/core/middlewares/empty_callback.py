import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram import types
from aiogram.dispatcher.event.bases import CancelHandler


class DropEmptyButtonMiddleware(BaseMiddleware):
	async def __call__(self,
	                   handler: Callable[[types.CallbackQuery, dict[str, Any]], Awaitable[Any]],
	                   event: types.CallbackQuery,
	                   data: dict[str, Any],
	                   ) -> Any:
		if not isinstance(event, types.CallbackQuery):
			logging.warning("DropEmptyButtonMiddleware is only CallbackQuery Middleware!")
			return await handler(event, data)

		if event.data == 'empty_button':
			await event.answer()
			raise CancelHandler()

		return await handler(event, data)
