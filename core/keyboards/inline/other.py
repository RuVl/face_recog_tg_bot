from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_keyboard(text='Отмена') -> InlineKeyboardMarkup:
    """ Cancel inline keyboard"""

    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=text, callback_data='cancel')
    ).as_markup()


def yes_no_cancel() -> InlineKeyboardMarkup:
    """ Yes, no or cancel keyboard """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Да', callback_data='yes'),
        InlineKeyboardButton(text='Нет', callback_data='no')
    ).row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    return builder.as_markup()
