from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def moderator_start_menu() -> InlineKeyboardMarkup:
	""" Answer on /start inline keyboard for moderator """

	builder = InlineKeyboardBuilder()
	builder.row(
		InlineKeyboardButton(text='Проверить в базе', callback_data='check_face')
	).row(
		InlineKeyboardButton(text='Найти по id', callback_data='get_by_id')
	).row(
		InlineKeyboardButton(
			text='Найти по тел номеру',
			callback_data='get_by_phone_number'
		)
	)

	return builder.as_markup()
