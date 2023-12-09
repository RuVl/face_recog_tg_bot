from typing import Any

from aiogram import types
from aiogram.filters import BaseFilter

from core.database.methods.user import check_if_admin, check_if_moderator, update_username


class IsModeratorMessageFilter(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool | dict[str, Any]:
        if not await check_if_moderator(msg.chat.id):
            return False

        await update_username(msg.chat.id, msg.from_user.username)
        return True


class IsModeratorCallbackFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> bool | dict[str, Any]:
        return await check_if_moderator(callback.from_user.id)


class IsAdminMessageFilter(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool | dict[str, Any]:
        if not await check_if_admin(msg.chat.id):
            return False

        await update_username(msg.chat.id, msg.from_user.username)
        return True


class IsAdminCallbackFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> bool | dict[str, Any]:
        return await check_if_admin(callback.from_user.id)

