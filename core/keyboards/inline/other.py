from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_keyboard(text='Отмена') -> InlineKeyboardMarkup:
    """ Cancel inline keyboard"""

    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text=text, callback_data='cancel')
    ).as_markup()


def yes_no_cancel(cancel_text='Отмена') -> InlineKeyboardMarkup:
    """
        Yes, no or cancel keyboard.
        If cancel_text is None won't cancel button
    """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Да', callback_data='yes'),
        InlineKeyboardButton(text='Нет', callback_data='no')
    )

    if cancel_text is not None:
        builder.row(InlineKeyboardButton(text=cancel_text, callback_data='cancel'))

    return builder.as_markup()
