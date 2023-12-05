from aiogram import Router, F, types
from aiogram.filters import CommandStart

from core.filters import IsModeratorMessageFilter, IsModeratorCallbackFilter

moderator_router = Router()

# Filters
moderator_router.message.filter(
    F.chat.type == 'private',
    IsModeratorMessageFilter()
)
moderator_router.callback_query.filter(
    IsModeratorCallbackFilter()
)


@moderator_router.message(CommandStart())
async def start(msg: types.Message):
    await msg.answer('Hello moderator', parse_mode='MarkdownV2')
