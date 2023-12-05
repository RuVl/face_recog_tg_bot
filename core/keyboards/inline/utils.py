import math
from typing import Callable

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.callback_factory import PaginatorFactory


def paginate(data: list, page: int, element2button: Callable, prefix: str) -> InlineKeyboardBuilder:
    """
        Create pages by inline buttons from data.
        :param data: list of data to split by page.
        :param page: current page.
        :param element2button: adapter data to InlineKeyboardButton.
        :param prefix: prefix for unique menu
    """

    COLS = 2  # Max buttons in one row
    ROWS = 5  # Max rows

    ON_PAGE = COLS * ROWS  # Buttons on one page

    page_data = data[page * ON_PAGE:(page + 1) * ON_PAGE]
    max_pages = math.ceil(len(data) / ON_PAGE)

    builder = InlineKeyboardBuilder()

    for d in page_data:
        builder.add(element2button(d))

    builder.adjust(COLS)

    if max_pages == 1:
        return builder

    page_switch_buttons = []

    if page > 0:
        page_switch_buttons.append(
            InlineKeyboardButton(
                text='<',
                callback_data=PaginatorFactory(menu=prefix, action='change_page', page=page - 1).pack()
            )
        )

    page_switch_buttons.append(
        InlineKeyboardButton(text=f'·{page + 1}/{max_pages}·', callback_data='empty_button')
    )

    if page + 1 < max_pages:
        page_switch_buttons.append(
            InlineKeyboardButton(
                text='>',
                callback_data=PaginatorFactory(menu=prefix, action='change_page', page=page + 1).pack()
            )
        )

    builder.row(*page_switch_buttons)

    return builder

