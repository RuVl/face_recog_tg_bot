from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.methods.location import get_all_locations
from core.database.methods.user import get_all_moderators
from core.keyboards.inline.utils import paginate
from core.misc import location2keyboard, moderator2keyboard


def admin_start_menu() -> InlineKeyboardMarkup:
    """ Answer on /start inline keyboard for admin """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='Проверить в базе',
            callback_data='check_face'
        )
    ).row(
        InlineKeyboardButton(
            text='Найти по id',
            callback_data='get_by_id'
        )
    ).row(
        InlineKeyboardButton(
            text='Меню админа',
            callback_data='admin_menu'
        )
    )

    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    """ Admin menu """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='Добавить модератора',
            callback_data='add_moderator'
        ),
        InlineKeyboardButton(
            text='Редактировать модераторов',
            callback_data='moderators_list'
        )
    ).row(
        InlineKeyboardButton(
            text='Назад',
            callback_data='back'
        )
    )

    return builder.as_markup()


def add_location() -> InlineKeyboardMarkup:
    """ Add new location by message or back to choosing """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Выбрать локацию', callback_data='back')
    ).row(
        InlineKeyboardButton(text='Отмена', callback_data='cancel')
    )

    return builder.as_markup()


async def select_location(page=0) -> InlineKeyboardMarkup:
    """ Select location for user keyboard """

    locations = await get_all_locations()
    builder = paginate(locations, page, location2keyboard, 'location_menu')

    builder.row(InlineKeyboardButton(text='Добавить локацию', callback_data='add_location'))
    builder.row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    return builder.as_markup()


async def select_moderator(page=0) -> InlineKeyboardMarkup:
    """ Moderators keyboard list """

    moderators = await get_all_moderators()
    builder = paginate(moderators, page, moderator2keyboard, 'moderator_list_menu')

    builder.row(InlineKeyboardButton(text='Назад', callback_data='back'))

    return builder.as_markup()


def edit_moderator() -> InlineKeyboardMarkup:
    """ Actions with moderator (edit location or delete) """

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Изменить локацию', callback_data='change_location_moderator')
    ).row(
        InlineKeyboardButton(text='Удалить', callback_data='delete_moderator')
    ).row(
        InlineKeyboardButton(text='Назад', callback_data='back')
    )

    return builder.as_markup()
