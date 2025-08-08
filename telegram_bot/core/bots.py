from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.env import TgKeys

bot = Bot(token=TgKeys.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
