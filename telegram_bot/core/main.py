from aiogram import Dispatcher, types

from core.bots import bot
from core.handlers import register_all_handlers
from core.misc.utils import get_storage


async def set_default_commands(bot):
	await bot.set_my_commands(
		[
			types.BotCommand(command='start', description='Запустить бота'),
		]
	)


async def start_bot():
	dp = Dispatcher(storage=get_storage())
	register_all_handlers(dp)

	await set_default_commands(bot)

	# await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
