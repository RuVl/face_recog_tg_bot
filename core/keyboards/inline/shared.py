from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models import Client
from core.keyboards.inline.utils import paginate
from core.misc import client2keyboard


def add_visit_kb(was_added=False) -> InlineKeyboardMarkup:
    """ Text for add a visit or edit-existed visit """

    text = 'Редактировать' if was_added else 'Добавить информацию'

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=text, callback_data='add_visit')
    ).row(
        InlineKeyboardButton(text='Назад', callback_data='cancel')
    )

    return builder.as_markup()


def add_visit_info_kb() -> InlineKeyboardMarkup:
    """ Add info about a visit """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Добавить имя', callback_data='add_name'),
        InlineKeyboardButton(text='Добавить контакты', callback_data='add_contacts')
    ).row(
        InlineKeyboardButton(text='Добавить сервис', callback_data='add_service')
    ).row(
        InlineKeyboardButton(text='Добавить фотографии', callback_data='add_images')
    ).row(
        InlineKeyboardButton(text='Назад', callback_data='cancel')
    )

    return builder.as_markup()


def select_clients_kb(clients: list[Client], page=0, **kwargs) -> InlineKeyboardMarkup:
    """ Select the client from a list of clients """

    builder = paginate(clients, page, client2keyboard, 'clients_choosing', **kwargs)

    builder.row(InlineKeyboardButton(text='Добавить нового', callback_data='add_new_client'))
    builder.row(InlineKeyboardButton(text='Назад', callback_data='cancel'))

    return builder.as_markup()
