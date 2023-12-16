import logging

import numpy as np
from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from core.database.methods.image import get_image_by_id
from core.database.models import Client
from core.handlers.utils import download_image, find_faces
from core.keyboards.inline import anyone_start_menu, cancel_keyboard
from core.state_machines import AnyoneMenu
from core.text import send_me_image, cancel_previous_processing

anyone_router = Router()

anyone_router.message.filter(
    F.chat.type == 'private',
)


# '/start'
@anyone_router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await state.set_state(AnyoneMenu.START)
    await msg.answer('Здравствуйте, выберите действие\.', reply_markup=anyone_start_menu(), parse_mode='MarkdownV2')


# '/start' -> action selected
@anyone_router.callback_query(AnyoneMenu.START)
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'check_if_exist':
            await state.set_state(AnyoneMenu.CHECK_IF_EXIST)
            await callback.answer()
            await callback.message.edit_text(send_me_image(), reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


# '/start' -> 'check_if_exist' -> document provided
@anyone_router.message(AnyoneMenu.CHECK_IF_EXIST, F.content_type == ContentType.DOCUMENT)
async def check_if_exist_face(msg: types.Message, state: FSMContext):
    """ Validate and download the provided file. Find a face on it and check if exists in db. """

    # Face recognition is still running
    if (await state.get_data()).get('check_if_exist'):
        await msg.answer(cancel_previous_processing(),
                         reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2')
        return

    await state.update_data(check_if_exist=True)
    document_path, message = await download_image(msg, state, 'check_if_exist')

    if document_path is None:
        return

    await message.edit_text('✅ Файл скачан\.\n'
                            'Поиск лица на фотографии\. 🔎', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    result = await find_faces(document_path, message, state, 'check_if_exist')

    if result is None:
        return

    if isinstance(result, np.ndarray):
        await state.update_data(check_if_exist=False)
        await message.edit_text('Нет в базе\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    if not isinstance(result, Client):
        logging.warning("Type checking aren't successful!")
        await message.edit_text('Что\-то пошло не так, повторите попытку\.', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    profile_picture = await get_image_by_id(result.profile_picture_id)

    # TODO save telegram_image_id for this image
    await state.update_data(check_face=False)

    await message.answer_photo(
        FSInputFile(profile_picture), caption=f'*id в базе:* `{result.id}`',
        reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'
    )

    await message.delete()


# /start -> 'check_if_exist' -> document provided -> 'cancel'
@anyone_router.callback_query(F.data == 'cancel', AnyoneMenu.CHECK_IF_EXIST)
async def cancel_check_face(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(check_if_exist=False)
    await callback.message.answer('Здравствуйте, выберите действие\.', reply_markup=anyone_start_menu(), parse_mode='MarkdownV2')
