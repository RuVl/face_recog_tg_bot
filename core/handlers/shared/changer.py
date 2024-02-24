import logging

from aiogram import types, F, Bot, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from cancel_token import CancellationToken

from core.database.methods.client import client_have_visit
from core.database.methods.image import create_image_from_path
from core.database.methods.service import create_visit_service
from core.database.methods.user import get_tg_user_location
from core.database.methods.visit import create_visit, update_visit_name, update_visit_contacts
from core.handlers.shared import show_client
from core.handlers.utils import change_msg, download_image, clear_cancellation_tokens
from core.keyboards.inline import add_visit_info_kb, cancel_keyboard, add_visit_kb
from core.misc import TgKeys
from core.state_machines import SharedMenu
from core.text import exit_visit, adding_name, adding_contacts, adding_services, adding_photos, face_info_text, created_visit, add_image_text, \
    add_service_text, add_contacts_text, add_name_text, cancel_previous_processing

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
            await state.update_data(actions_alert=(await client_have_visit(client_id)))  # Alert to admin chat

            location = await get_tg_user_location(callback.from_user.id)
            visit = await create_visit(client_id, location.id)
            await state.update_data(visit_id=visit.id)

        await alert2admins(callback.bot, callback.from_user, state, is_new=(visit_id is None))

        await state.set_state(SharedMenu.ADD_VISIT)
        await callback.answer()

        text = await face_info_text(client_id, callback.from_user.id)
        await callback.message.edit_caption(caption=text, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit'
@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.ADD_VISIT)
async def add_visit_info(callback: types.CallbackQuery, state: FSMContext):
    """ Handle buttons to add visit info. """

    match callback.data:
        case 'add_name':
            await state.set_state(SharedMenu.ADD_VISIT_NAME)
            await callback.answer()
            await callback.message.edit_caption(caption=add_name_text(), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_contacts':
            await state.set_state(SharedMenu.ADD_VISIT_CONTACTS)
            await callback.answer()
            await callback.message.edit_caption(caption=add_contacts_text(),
                                                reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_service':
            await state.set_state(SharedMenu.ADD_VISIT_SERVICE)
            await callback.answer()
            await callback.message.edit_caption(caption=add_service_text(), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'add_images':
            await state.set_state(SharedMenu.ADD_VISIT_IMAGES)
            await callback.answer()
            await callback.message.edit_caption(caption=add_image_text(),
                                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


async def alert2admins(bot: Bot, user: types.User, state: FSMContext, **kwargs):
    state_data = await state.get_data()
    actions_alert = state_data.get('actions_alert')

    if not actions_alert:
        return

    client_id = state_data.get('client_id')

    match await state.get_state():
        case SharedMenu.SHOW_FACE_INFO:
            text = created_visit(user, client_id, kwargs)
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
        await show_client(msg, state, text='Не валидное имя\!\n\n' + add_name_text(), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_name(visit_id, name)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_contacts'
@shared_changer_router.message(SharedMenu.ADD_VISIT_CONTACTS)
async def add_visit_contacts(msg: types.Message, state: FSMContext):
    """ Add visit contacts """

    contacts = msg.text.strip()
    if contacts == '':
        await show_client(msg, state, text='Не валидные контакты\!\n\n' + add_contacts_text(), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_contacts(visit_id, contacts)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_service'
@shared_changer_router.message(SharedMenu.ADD_VISIT_SERVICE)
async def add_visit_service(msg: types.Message, state: FSMContext):
    """ Add visit services """

    title = msg.text.strip()
    if title == '':
        await show_client(msg, state, text='Не валидный сервис\!\n\n' + add_service_text(), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await create_visit_service(visit_id, title)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_images'
@shared_changer_router.message(SharedMenu.ADD_VISIT_IMAGES, F.content_type == ContentType.DOCUMENT)
async def add_visit_images(msg: types.Message, state: FSMContext):
    """ Add visit images """

    state_data = await state.get_data()
    add_image_token: CancellationToken = state_data.get('add_image_token')

    # Add image is still processing
    if add_image_token is not None:
        if not add_image_token.completed:
            await change_msg(
                msg.answer(cancel_previous_processing(), reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2'),
                state
            )
            return
        else:
            await clear_cancellation_tokens(state)

    add_image_token = CancellationToken()
    await state.update_data(add_image_token=add_image_token)  # set token to not None

    image_path, message = await download_image(msg, state, add_image_token)
    if add_image_token.completed or image_path is None:
        return

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    try:
        await create_image_from_path(image_path, visit_id)
        await alert2admins(msg.bot, msg.from_user, state)
    except Exception as e:
        logging.error(str(e))
        await change_msg(
            msg.reply('Не удалось загрузить на хостинг\! 😟\n\n' + add_image_text(), reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'),
            state
        )
        return

    add_image_token.complete()


# /start -> 'check_face' -> face found -> 'add_visit' -> '...' -> 'cancel'
@shared_changer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.ADD_VISIT_NAME, SharedMenu.ADD_VISIT_CONTACTS,
    SharedMenu.ADD_VISIT_SERVICE, SharedMenu.ADD_VISIT_IMAGES
))
async def add_visit_data_back(callback: types.CallbackQuery, state: FSMContext):
    """ Return to adding new visit data """

    await clear_cancellation_tokens(state)

    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await state.set_state(SharedMenu.ADD_VISIT)
    await callback.answer()

    caption = await face_info_text(client_id, callback.from_user.id)
    await show_client(callback.message, state, text=caption, reply_markup=add_visit_info_kb())
