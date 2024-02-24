from aiogram import Dispatcher, types
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from core import bot
from core.handlers import register_all_handlers
from core.misc.env import SettingsKeys


async def set_default_commands(bot):
    await bot.set_my_commands(
        [
            types.BotCommand(command='start', description='Запустить бота'),
        ]
    )


def get_storage() -> BaseStorage:
    if SettingsKeys.DEBUG:
        return MemoryStorage()

    return RedisStorage.from_url('redis://localhost:6379/0')


async def start_bot():
    dp = Dispatcher(storage=get_storage())

    register_all_handlers(dp)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
