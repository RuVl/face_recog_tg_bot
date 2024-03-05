from aiogram.fsm.context import FSMContext

from core.state_machines.utils import _cancel_all_tokens, _clear_gallery, _clear_path, _clear_state_data, _cancel_token, _complete_token


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
