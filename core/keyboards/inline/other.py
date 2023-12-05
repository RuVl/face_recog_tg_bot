from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_keyboard(text='Отмена') -> InlineKeyboardMarkup:
    """ Cancel inline keyboard"""

    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=text, callback_data='cancel')
    ).as_markup()
