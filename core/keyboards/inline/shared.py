from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_visit() -> InlineKeyboardMarkup:
    """ Add a visit, photos or services """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Добавить информацию', callback_data='add_visit')
    ).row(
        InlineKeyboardButton(text='Добавить сервис', callback_data='add_service')
    ).row(
        InlineKeyboardButton(text='Добавить фотографии', callback_data='add_images')
    ).row(
        InlineKeyboardButton(text='Назад', callback_data='cancel')
    )

    return builder.as_markup()


def add_visit_info() -> InlineKeyboardMarkup:
    """ Add info about a visit """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Добавить имя', callback_data='add_name'),
    ).row(
        InlineKeyboardButton(text='Добавить контакты', callback_data='add_contacts')
    ).row(
        InlineKeyboardButton(text='Назад', callback_data='cancel')
    )

    return builder.as_markup()
