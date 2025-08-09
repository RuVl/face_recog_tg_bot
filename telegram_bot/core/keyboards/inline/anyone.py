from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def anyone_start_menu() -> InlineKeyboardMarkup:
	""" Answer on /start inline keyboard for anyone """

	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(
			text='Проверить в базе',
			callback_data='check_if_exist'
		)
	)

	return builder.as_markup()
