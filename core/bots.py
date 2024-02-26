from aiogram import Bot
from aiogram.enums import ParseMode

from core.misc import TgKeys

bot = Bot(token=TgKeys.TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
