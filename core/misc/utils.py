from typing import Iterator

from aiogram.types import InlineKeyboardButton

from core.database.models import Location, User, Client


def location2keyboard(location: Location) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=location.address, callback_data=f'{location.id}-{location.address}')


def moderator2keyboard(moderator: User) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=f'{moderator.telegram_id} · {moderator.username}', callback_data=f'{moderator.id}-{moderator.telegram_id}')


def client2keyboard(client: Client) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=f'· {client.id} ·', callback_data=f'{client.id}')


def str2int(*args) -> Iterator[int]:
    for value in args:
        yield int(value) if isinstance(value, str) else value
