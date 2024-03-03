from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.methods.user import check_if_admin
from core.database.models import Client
from core.keyboards.inline.utils import paginate
from core.misc.adapters import client2keyboard


async def add_visit_kb(*, was_added=False, user_id: int | str = None) -> InlineKeyboardMarkup:
    """ Text for add a visit or edit-existed visit """

    is_admin = await check_if_admin(user_id) if user_id is not None else False

    text = 'Редактировать' if was_added else 'Добавить визит'

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=text, callback_data='add_visit'))

    if is_admin:
        builder.row(InlineKeyboardButton(text='Удалить', callback_data='delete_client'))

    builder.row(InlineKeyboardButton(text='Назад', callback_data='cancel'))

    return builder.as_markup()


def add_visit_info_kb() -> InlineKeyboardMarkup:
    """ Add info about a visit """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Имя', callback_data='add_name')
    ).row(
        InlineKeyboardButton(text='Соц сети', callback_data='add_social_media'),
        InlineKeyboardButton(text='Номер телефона', callback_data='add_phone_number')
    ).row(
        InlineKeyboardButton(text='Сервис', callback_data='add_service')
    ).row(
        InlineKeyboardButton(text='Фотографии', callback_data='add_images'),
        InlineKeyboardButton(text='Видео', callback_data='add_videos')
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
