from typing import Any

from aiogram import types
from aiogram.filters import BaseFilter

from core.database.methods.user import check_if_admin, check_if_moderator, update_username, check_if_moderator_or_admin


class IsModeratorMessageFilter(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool | dict[str, Any]:
        if not await check_if_moderator(msg.chat.id):
            return False

        await update_username(msg.chat.id, msg.from_user.username)
        return True


class IsModeratorCallbackFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> bool | dict[str, Any]:
        if not await check_if_moderator(callback.from_user.id):
            return False

        return True


class IsAdminMessageFilter(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool | dict[str, Any]:
        if not await check_if_admin(msg.chat.id):
            return False

        await update_username(msg.chat.id, msg.from_user.username)
        return True


class IsAdminCallbackFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> bool | dict[str, Any]:
        if not await check_if_admin(callback.from_user.id):
            return False

        return True


class IsAdminOrModeratorMessageFilter(BaseFilter):
    async def __call__(self, msg: types.Message) -> bool | dict[str, Any]:
        if not await check_if_moderator_or_admin(msg.chat.id):
            return False

        await update_username(msg.chat.id, msg.from_user.username)
        return True


class IsAdminOrModeratorCallbackFilter(BaseFilter):
    async def __call__(self, callback: types.CallbackQuery) -> bool | dict[str, Any]:
        if not await check_if_moderator_or_admin(callback.from_user.id):
            return False

        return True
