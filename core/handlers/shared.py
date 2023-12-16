import logging
import shutil
from pathlib import Path

import numpy as np
from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from core.config import MEDIA_DIR, SUPPORTED_IMAGE_TYPES
from core.database.methods.client import create_client, get_client
from core.database.methods.image import get_image_by_id, create_image_from_path
from core.database.methods.service import add_client_service
from core.database.methods.user import check_if_admin, check_if_moderator, get_tg_user_location
from core.database.methods.visit import create_visit, update_visit_name, update_visit_contacts
from core.database.models import Client
from core.filters import IsAdminOrModeratorMessageFilter, IsAdminOrModeratorCallbackFilter
from core.handlers.utils import find_faces, download_image
from core.keyboards.inline import cancel_keyboard, admin_start_menu, moderator_start_menu, yes_no_cancel, add_visit, add_visit_info
from core.state_machines import AdminMenu, ModeratorMenu, SharedMenu
from core.text import face_info_text, send_me_image, cancel_previous_processing

admin_moderator_router = Router()

admin_moderator_router.message.filter(
    F.chat.type == 'private',
    IsAdminOrModeratorMessageFilter()
)
admin_moderator_router.callback_query.filter(
    IsAdminOrModeratorCallbackFilter()
)


# /start -> 'check_face'
@admin_moderator_router.callback_query(F.data.in_(['check_face', 'get_by_id']), or_f(
    AdminMenu.START, ModeratorMenu.START
))
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Branches after /start """

    match callback.data:
        case 'check_face':
            await state.set_state(SharedMenu.CHECK_FACE)
            await callback.answer()
            await callback.message.edit_text(send_me_image(), reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        case 'get_by_id':
            await state.set_state(SharedMenu.GET_BY_ID)
            await callback.answer()
            await callback.message.edit_text('Отправьте мне `id` клиента в базе данных',
                                             reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


async def show_client(msg: types.Message, state: FSMContext, reply_markup: types.InlineKeyboardMarkup):
    """ Show the client (photo with caption and buttons). Needs client_id and client_photo_path in state data """

    state_data = await state.get_data()

    client_id = state_data.get('client_id')
    face_path = state_data.get('client_photo_path')

    text = await face_info_text(client_id)
    await msg.answer_photo(
        FSInputFile(face_path), caption=text,
        reply_markup=reply_markup, parse_mode='MarkdownV2'
    )


# /start -> 'check_face' -> document provided
@admin_moderator_router.message(SharedMenu.CHECK_FACE, F.content_type == ContentType.DOCUMENT)
async def check_face(msg: types.Message, state: FSMContext):
    """ Validate and download the provided file. Find a face on it and compare with others. """

    # Face recognition is still running
    if (await state.get_data()).get('check_face'):
        await msg.answer(cancel_previous_processing(),
                         reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2')
        return

    await state.update_data(check_face=True)
    document_path, message = await download_image(msg, state, 'check_face')

    if document_path is None:
        return

    await state.update_data(client_photo_path=document_path)
    await message.edit_text('✅ Файл скачан\.\n'
                            'Поиск лица на фотографии\. 🔎', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    result = await find_faces(document_path, message, state, 'check_face')

    if result is None:
        return

    if isinstance(result, np.ndarray):
        await state.update_data(check_face=False, face_encoding=result)
        await state.set_state(SharedMenu.ADD_NEW_FACE)

        await message.edit_text('Нет в базе\! 🤯\n'
                                'Добавить такого человека?', reply_markup=yes_no_cancel(None), parse_mode='MarkdownV2')
        return

    if not isinstance(result, Client):
        logging.warning("Type checking aren't successful!")
        await message.edit_text('Что\-то пошло не так, повторите попытку\.', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    profile_picture = await get_image_by_id(result.profile_picture_id)

    # TODO save telegram_image_id for this image
    await state.update_data(check_face=False, client_id=result.id, client_photo_path=profile_picture.path)
    await state.set_state(SharedMenu.SHOW_FACE_INFO)

    await show_client(message, state, add_visit())
    await message.delete()


@admin_moderator_router.message(SharedMenu.GET_BY_ID)
async def get_by_id(msg: types.Message, state: FSMContext):
    try:
        client_id = int(msg.text)
    except ValueError:
        await msg.reply('Must be number\!', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    client = await get_client(client_id)
    profile_picture = await get_image_by_id(client.profile_picture_id)

    # TODO save telegram_image_id for this image
    await state.update_data(client_id=client.id, client_photo_path=profile_picture.path)
    await state.set_state(SharedMenu.SHOW_FACE_INFO)

    await show_client(msg, state, add_visit())


async def return2start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Returns user to moderator or admin menu (or nothing if user neither admin nor moderator) """

    state_data = await state.get_data()
    document_path = state_data.get('client_photo_path')

    if document_path is not None:
        document_path = Path(document_path)
        if document_path.exists():
            document_path.unlink()

    if await check_if_admin(callback.from_user.id):
        await state.set_state(AdminMenu.START)
        await callback.answer()

        await callback.message.answer('Здравствуйте, админ 👑', reply_markup=admin_start_menu(), parse_mode='MarkdownV2')

    elif await check_if_moderator(callback.from_user.id):
        await state.set_state(ModeratorMenu.START)

        await callback.answer()
        await callback.message.answer('Здравствуйте, модератор 💼', reply_markup=moderator_start_menu(), parse_mode='MarkdownV2')


# /start -> 'check_face' -> document provided -> 'cancel'
@admin_moderator_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.CHECK_FACE, SharedMenu.GET_BY_ID, SharedMenu.SHOW_FACE_INFO
))
async def cancel_check_face(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(check_face=False)
    await return2start_menu(callback, state)


# /start -> 'check_face' -> document provided -> face not found
@admin_moderator_router.callback_query(SharedMenu.ADD_NEW_FACE)
async def add_new_face(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'no':
        await return2start_menu(callback, state)
        return

    if callback.data == 'yes':
        state_data = await state.get_data()

        face_path_temp = state_data.get('client_photo_path')
        face_path = shutil.copy2(face_path_temp, MEDIA_DIR)

        face_encoding = state_data.get('face_encoding')

        client = await create_client(face_path, face_encoding)

        await state.set_state(SharedMenu.ADD_VISIT)
        await callback.answer('Клиент добавлен в базу данных!')
        await state.update_data(client_id=client.id, client_photo_path=face_path)

        await show_client(callback.message, state, add_visit())
        await callback.message.delete()


# /start -> 'check_face' -> face found
@admin_moderator_router.callback_query(F.data != 'cancel', SharedMenu.SHOW_FACE_INFO)
async def edit_face_info(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'add_visit':
            state_data = await state.get_data()
            client_id = state_data.get('client_id')

            location = await get_tg_user_location(callback.from_user.id)

            visit = await create_visit(client_id, location.id)
            await state.update_data(visit_id=visit.id)

            await state.set_state(SharedMenu.ADD_VISIT)
            await callback.answer()
            await callback.message.edit_reply_markup(reply_markup=add_visit_info())
        case 'add_service':
            await state.set_state(SharedMenu.ADD_CLIENT_SERVICE)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `сервис`:', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_images':
            await state.set_state(SharedMenu.ADD_CLIENT_IMAGES)
            await callback.answer()
            await callback.message.edit_caption(caption='Отправляйте мне `фотографии` как документ\.',
                                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


# /start -> 'check_face' -> face found -> 'add_service'
@admin_moderator_router.message(SharedMenu.ADD_CLIENT_SERVICE)
async def add_new_service(msg: types.Message, state: FSMContext):
    title = msg.text.strip()
    if title == '':
        await msg.answer('Не валидный сервис\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await add_client_service(client_id, title)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit())


# /start -> 'check_face' -> face found -> 'add_images'
@admin_moderator_router.message(SharedMenu.ADD_CLIENT_IMAGES, F.content_type == ContentType.DOCUMENT)
async def add_new_images(msg: types.Message, state: FSMContext):
    # File is so big
    if msg.document.file_size > 20 * 1024 * 1024:
        await msg.reply(f'Файл слишком большой\! 😖', parse_mode='MarkdownV2')
        return

    # Unsupported file type
    if msg.document.mime_type not in SUPPORTED_IMAGE_TYPES.keys():
        await msg.reply(f'Файл неподдерживаемого формата\! 😩', parse_mode='MarkdownV2')
        return

    # Download image
    filename = msg.document.file_id + SUPPORTED_IMAGE_TYPES[msg.document.mime_type]
    document_path = Path(MEDIA_DIR / filename)
    await msg.bot.download(msg.document, document_path)

    # Is the image downloaded?
    if not document_path.exists():
        await msg.edit_text('Загрузка файла не удалась\. 😭\n'
                            'Попробуйте ещё раз или обратитесь к админам\.', parse_mode='MarkdownV2')
        return

    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    try:
        await create_image_from_path(document_path, client_id)
    except Exception as e:
        logging.error(str(e))
        await msg.reply('Не удалось загрузить на хостинг\!', parse_mode='MarkdownV2')
        return


# /start -> 'check_face' -> face found -> 'add_visit'
@admin_moderator_router.callback_query(F.data != 'cancel', SharedMenu.ADD_VISIT)
async def add_new_visit(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'add_name':
            await state.set_state(SharedMenu.ADD_VISIT_NAME)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `имя`:', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_contacts':
            await state.set_state(SharedMenu.ADD_VISIT_CONTACTS)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `контакты` одним сообщением:', reply_markup=cancel_keyboard(),
                                                parse_mode='MarkdownV2')


# /start -> 'check_face' -> face found -> '...' -> 'cancel'
@admin_moderator_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.ADD_VISIT, SharedMenu.ADD_CLIENT_SERVICE, SharedMenu.ADD_CLIENT_IMAGES
))
async def add_client_data_back(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await state.set_state(SharedMenu.SHOW_FACE_INFO)
    await callback.answer()

    await callback.message.edit_caption(caption=await face_info_text(client_id),
                                        reply_markup=add_visit(), parse_mode='MarkdownV2')


# /start -> 'check_face' -> face found -> 'add_visit' -> 'cancel'
@admin_moderator_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.ADD_VISIT_NAME, SharedMenu.ADD_VISIT_CONTACTS, SharedMenu.ADD_CLIENT_SERVICE
))
async def add_visit_info_back(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await state.set_state(SharedMenu.SHOW_FACE_INFO)
    await callback.answer()

    await callback.message.edit_caption(caption=await face_info_text(client_id),
                                        reply_markup=add_visit_info(), parse_mode='MarkdownV2')


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_name'
@admin_moderator_router.message(SharedMenu.ADD_VISIT_NAME)
async def add_visit_name(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    if name == '':
        await msg.answer('Не валидное имя\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_name(visit_id, name)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit_info())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_contacts'
@admin_moderator_router.message(SharedMenu.ADD_VISIT_CONTACTS)
async def add_visit_contacts(msg: types.Message, state: FSMContext):
    contacts = msg.text.strip()
    if contacts == '':
        await msg.answer('Не валидные контакты\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_contacts(visit_id, contacts)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit_info())
