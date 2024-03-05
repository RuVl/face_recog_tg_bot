import asyncio
import logging
from pathlib import Path

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from core.cancel_token import CancellationToken
from core.state_machines.fields import *


_STATE_LOCK = asyncio.Lock()

TOKEN_NAMES = [CHECK_FACE_FIELD, ADDING_IMAGE_FIELD, ADDING_VIDEO_FIELD]
ALL_STATE_FIELDS = TOKEN_NAMES + [FACE_GALLERY_FIELD, TEMP_PATH_FIELD, LAST_MESSAGE_FIELD]


def _with_lock_state(func):
    """ Decorator to use clear_lock for use state """

    async def wrapper(state: FSMContext, *args, **kwargs):
        async with _STATE_LOCK:
            state_data = await state.get_data()
            result = await func(state_data, *args, **kwargs)
            await state.set_data(state_data)
            return result

    return wrapper


@_with_lock_state
async def _cancel_token(state_data: dict, token_name: str):
    if token_name not in state_data:
        return

    token: CancellationToken = state_data[token_name]
    if not token.completed:
        token.cancel()


@_with_lock_state
async def _complete_token(state_data: dict, token_name: str):
    if token_name not in state_data:
        return

    state_data[token_name].complete()


@_with_lock_state
async def _cancel_all_tokens(state_data: dict):
    for token_name in TOKEN_NAMES:
        if token_name not in state_data:
            continue

        token: CancellationToken = state_data[token_name]
        if not token.completed:
            token.cancel()


@_with_lock_state
async def _clear_gallery(state_data: dict):
    if FACE_GALLERY_FIELD not in state_data:
        return

    face_gallery_msg: list[types.Message] = state_data.pop(FACE_GALLERY_FIELD)
    for msg in face_gallery_msg:
        try:
            await msg.delete()
        except TelegramBadRequest as e:
            logging.warning(f'Exception during delete gallery: {e.message}')


@_with_lock_state
async def _clear_path(state_data: dict):
    document_path = state_data.pop(TEMP_PATH_FIELD, None)
    if document_path is not None:
        Path(document_path).unlink(missing_ok=True)


@_with_lock_state
async def _clear_state_data(state_data: dict):
    for key in state_data.keys():
        if key not in ALL_STATE_FIELDS:
            state_data.pop(key)
