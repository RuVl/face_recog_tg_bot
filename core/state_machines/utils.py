import asyncio
import functools
import logging
from pathlib import Path

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from core.cancel_token import CancellationToken
from core.state_machines.fields import *

_STATE_LOCK = asyncio.Lock()

TOKEN_NAMES = [CHECK_FACE_TOKEN, ADDING_IMAGE_TOKEN, ADDING_VIDEO_TOKEN]
ALL_STATE_FIELDS = TOKEN_NAMES + [FACE_GALLERY_FIELD, TEMP_PATH_FIELD, LAST_MESSAGE_FIELD]


def _with_lock_state(func):
    """ Decorator to use clear_lock for use state """

    @functools.wraps(func)
    async def wrapper(state: FSMContext, *args, **kwargs):
        async with _STATE_LOCK:
            state_data = await state.get_data()
            result = await func(state_data, *args, **kwargs)
            await state.set_data(state_data)
            return result

    return wrapper
