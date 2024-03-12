import logging
from pathlib import Path

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from core.cancel_token import CancellationToken
from core.state_machines.fields import FACE_GALLERY_FIELD, TEMP_PATH_FIELD
from core.state_machines.utils import _with_lock_state, TOKEN_NAMES, ALL_STATE_FIELDS


async def cancel_token(state: FSMContext, token_name: str):
    await _cancel_token(state, token_name)


async def complete_token(state: FSMContext, token_name: str):
    await _complete_token(state, token_name)


async def cancel_all_tokens(state: FSMContext):
    await _cancel_all_tokens(state)


async def clear_gallery(state: FSMContext):
    await _clear_gallery(state)


async def clear_path(state: FSMContext):
    await _clear_path(state)


async def clear_state_data(state: FSMContext):
    await _clear_state_data(state)


async def clear_all_in_one(state: FSMContext, clear_state=False):
    await cancel_all_tokens(state)
    await clear_gallery(state)
    await clear_path(state)

    if clear_state:
        await clear_state_data(state)


# Real functions

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

        token: CancellationToken = state_data.get(token_name)
        if token and not token.completed:
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
    for key in list(state_data.keys()):
        if key not in ALL_STATE_FIELDS:
            del state_data[key]
