import logging
from pathlib import Path

from aiogram import types, F, Bot, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.config import SUPPORTED_IMAGE_TYPES, MEDIA_DIR
from core.database.methods.client import client_have_visit
from core.database.methods.image import create_image_from_path
from core.database.methods.service import create_visit_service
from core.database.methods.user import get_tg_user_location
from core.database.methods.visit import create_visit, update_visit_name, update_visit_contacts
from core.handlers.shared import show_client
from core.keyboards.inline import add_visit_info_kb, cancel_keyboard, add_visit_kb
from core.misc import TgKeys
from core.state_machines import SharedMenu
from core.text import exit_visit, adding_name, adding_contacts, adding_services, adding_photos, face_info_text, created_visit


shared_changer_router = Router()


# /start -> 'check_face' -> face found
@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.SHOW_FACE_INFO)
async def add_visit(callback: types.CallbackQuery, state: FSMContext):
    """ Show face info. Add a new client visit. """

    if callback.data == 'add_visit':
        state_data = await state.get_data()

        client_id = state_data.get('client_id')
        visit_id = state_data.get('visit_id')

        # Create visit
        if visit_id is None:
            if await client_have_visit(client_id):
                await state.update_data(actions_alert=True)

                text = created_visit(callback.from_user, client_id)
                await callback.bot.send_message(TgKeys.ADMIN_GROUP_ID, text, parse_mode='MarkdownV2')

            location = await get_tg_user_location(callback.from_user.id)
            visit = await create_visit(client_id, location.id)
            await state.update_data(visit_id=visit.id)

        await state.set_state(SharedMenu.ADD_VISIT)
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit'
@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.ADD_VISIT)
async def add_visit_info(callback: types.CallbackQuery, state: FSMContext):
    """ Handle buttons to add visit info. """

    match callback.data:
        case 'add_name':
            await state.set_state(SharedMenu.ADD_VISIT_NAME)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `имя`:', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_contacts':
            await state.set_state(SharedMenu.ADD_VISIT_CONTACTS)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `контакты` одним сообщением:',
                                                reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_service':
            await state.set_state(SharedMenu.ADD_VISIT_SERVICE)
            await callback.answer()
            await callback.message.edit_caption(caption='Введите `сервис`:', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_images':
            await state.set_state(SharedMenu.ADD_VISIT_IMAGES)
            await callback.answer()
            await callback.message.edit_caption(caption='Отправляйте мне `фотографии` как документ\.',
                                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


async def alert2admins(bot: Bot, user: types.User, state: FSMContext):
    state_data = await state.get_data()
    actions_alert = state_data.get('actions_alert')

    if not actions_alert:
        return

    client_id = state_data.get('client_id')

    match await state.get_state():
        case SharedMenu.ADD_VISIT:
            text = exit_visit(user, client_id)
        case SharedMenu.ADD_VISIT_NAME:
            text = adding_name(user, client_id)
        case SharedMenu.ADD_VISIT_CONTACTS:
            text = adding_contacts(user, client_id)
        case SharedMenu.ADD_VISIT_SERVICE:
            text = adding_services(user, client_id)
        case SharedMenu.ADD_VISIT_IMAGES:
            text = adding_photos(user, client_id)

    await bot.send_message(TgKeys.ADMIN_GROUP_ID, text, parse_mode='MarkdownV2')


# /start -> 'check_face' -> face found -> 'add_visit' -> 'cancel'
@shared_changer_router.callback_query(F.data == 'cancel', SharedMenu.ADD_VISIT)
async def add_visit_back(callback: types.CallbackQuery, state: FSMContext):
    """ Return to show face info """

    await alert2admins(callback.bot, callback.from_user, state)

    await state.set_state(SharedMenu.SHOW_FACE_INFO)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=add_visit_kb(True))


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_name'
@shared_changer_router.message(SharedMenu.ADD_VISIT_NAME)
async def add_visit_name(msg: types.Message, state: FSMContext):
    """ Add visit name """

    name = msg.text.strip()
    if name == '':
        await msg.answer('Не валидное имя\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_name(visit_id, name)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_contacts'
@shared_changer_router.message(SharedMenu.ADD_VISIT_CONTACTS)
async def add_visit_contacts(msg: types.Message, state: FSMContext):
    """ Add visit contacts """

    contacts = msg.text.strip()
    if contacts == '':
        await msg.answer('Не валидные контакты\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_contacts(visit_id, contacts)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_service'
@shared_changer_router.message(SharedMenu.ADD_VISIT_SERVICE)
async def add_visit_service(msg: types.Message, state: FSMContext):
    """ Add visit services """

    title = msg.text.strip()
    if title == '':
        await msg.answer('Не валидный сервис\!\n', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await create_visit_service(visit_id, title)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_images'
@shared_changer_router.message(SharedMenu.ADD_VISIT_IMAGES, F.content_type == ContentType.DOCUMENT)
async def add_visit_images(msg: types.Message, state: FSMContext):
    """ Add visit images """

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
        await msg.edit_text('Скачивание файла не удалось\. 😭\n'
                            'Попробуйте ещё раз или обратитесь к админам\.', parse_mode='MarkdownV2')
        return

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    try:
        await create_image_from_path(document_path, visit_id)
        await alert2admins(msg.bot, msg.from_user, state)
    except Exception as e:
        logging.error(str(e))
        await msg.reply('Не удалось загрузить на хостинг\!', parse_mode='MarkdownV2')
        return


# /start -> 'check_face' -> face found -> 'add_visit' -> '...' -> 'cancel'
@shared_changer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.ADD_VISIT_NAME, SharedMenu.ADD_VISIT_CONTACTS,
    SharedMenu.ADD_VISIT_SERVICE, SharedMenu.ADD_VISIT_IMAGES
))
async def add_visit_data_back(callback: types.CallbackQuery, state: FSMContext):
    """ Return to adding new visit data """

    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await state.set_state(SharedMenu.ADD_VISIT)
    await callback.answer()

    caption = await face_info_text(client_id)
    await callback.message.edit_caption(caption=caption, reply_markup=add_visit_info_kb(), parse_mode='MarkdownV2')
