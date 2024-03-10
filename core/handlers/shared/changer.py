import logging

import phonenumbers
from aiogram import types, F, Bot, Router
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.cancel_token import CancellationToken
from core.config import PHONE_NUMBER_REGION
from core.database.methods.client import client_have_visit, delete_client
from core.database.methods.image import create_image_from_path
from core.database.methods.service import create_visit_service
from core.database.methods.user import get_tg_user_location, check_if_admin
from core.database.methods.video import create_video_from_path
from core.database.methods.visit import create_visit, update_visit_name, update_visit_social_media
from core.database.methods.visit.update import update_visit_phone_number
from core.handlers.shared import show_client
from core.handlers.shared.recogniser import return2start_menu
from core.handlers.utils import change_msg, download_document, download_video
from core.keyboards.inline import add_visit_info_kb, cancel_keyboard, add_visit_kb, yes_no_cancel
from core.misc import TgKeys
from core.state_machines import SharedMenu
from core.state_machines.clearing import cancel_all_tokens
from core.text import exit_visit_text, adding_name_text, adding_social_media_text, adding_service_text, adding_photo_text, face_info_text, \
    created_visit_text, add_image_text, add_service_text, add_social_media_text, add_name_text, cancel_previous_processing, add_phone_number_text, \
    add_video_text
from core.text.admin_alerts import adding_phone_number_text, adding_video_text

shared_changer_router = Router()


# /start -> 'check_face' -> face found
@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.SHOW_FACE_INFO)
async def add_visit(callback: types.CallbackQuery, state: FSMContext):
    """ Show face info. Add a new client visit. """

    state_data = await state.get_data()

    client_id = state_data.get('client_id')
    visit_id = state_data.get('visit_id')

    match callback.data:
        case 'add_visit':
            if visit_id is None:
                await state.update_data(actions_alert=(await client_have_visit(client_id)))  # Alert to admin chat

                location = await get_tg_user_location(callback.from_user.id)
                visit = await create_visit(client_id, location.id)
                await state.update_data(visit_id=visit.id)

            await alert2admins(callback.bot, callback.from_user, state, is_new=(visit_id is None))

            await state.set_state(SharedMenu.ADD_VISIT)
            await callback.answer()

            text = await face_info_text(client_id, callback.from_user.id)
            await callback.message.edit_text(text + '\n\n*Выберите что добавить:*', reply_markup=add_visit_info_kb())
        case 'delete_client':
            await state.set_state(SharedMenu.DELETE_CLIENT)
            await callback.answer()
            await callback.message.edit_text('Вы уверены?', reply_markup=yes_no_cancel(None))


@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.DELETE_CLIENT)
async def delete_client_handler(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    if client_id is None:
        await callback.answer('Клиент не найден!')

    match callback.data:
        case 'yes':
            if not await check_if_admin(callback.from_user.id):
                await callback.bot.send_message(TgKeys.ADMIN_GROUP_ID,
                                                text=f'`{callback.from_user.username}` попытался удалить клиента `{client_id}`\n'
                                                     f'Отказано в доступе\.')
                await callback.answer('Отказано в доступе!')
                return

            await delete_client(client_id)
            await callback.answer('Удалено!')

            await return2start_menu(callback, state)
        case 'no':
            await state.set_state(SharedMenu.SHOW_FACE_INFO)
            await callback.answer()

            keyboard = await add_visit_kb(user_id=callback.from_user.id)
            text = await face_info_text(client_id, callback.from_user.id)

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)


# /start -> 'check_face' -> face found -> 'add_visit'
@shared_changer_router.callback_query(F.data != 'cancel', SharedMenu.ADD_VISIT)
async def add_visit_info(callback: types.CallbackQuery, state: FSMContext):
    """ Handle buttons to add visit info. """

    keyboard = cancel_keyboard()

    match callback.data:
        case 'add_name':
            state_ = SharedMenu.ADD_VISIT_NAME
            text = add_name_text()
        case 'add_social_media':
            state_ = SharedMenu.ADD_VISIT_SOCIAL_MEDIA
            text = add_social_media_text()
        case 'add_phone_number':
            state_ = SharedMenu.ADD_VISIT_PHONE_NUMBER
            text = add_phone_number_text()
        case 'add_service':
            state_ = SharedMenu.ADD_VISIT_SERVICE
            text = add_service_text()
        case 'add_images':
            state_ = SharedMenu.ADD_VISIT_IMAGES
            text = add_image_text()
            keyboard = cancel_keyboard('Назад')
        case 'add_videos':
            state_ = SharedMenu.ADD_VISIT_VIDEOS
            text = add_video_text()
            keyboard = cancel_keyboard('Назад')
        case _:
            raise NotImplementedError('Не реализовано!')

    await state.set_state(state_)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)


async def alert2admins(bot: Bot, user: types.User, state: FSMContext, **kwargs):
    state_data = await state.get_data()
    actions_alert = state_data.get('actions_alert')

    if not actions_alert:
        return

    client_id = state_data.get('client_id')

    match await state.get_state():
        case SharedMenu.SHOW_FACE_INFO:
            text = created_visit_text(user, client_id, **kwargs)
        case SharedMenu.ADD_VISIT:
            text = exit_visit_text(user, client_id)
        case SharedMenu.ADD_VISIT_NAME:
            text = adding_name_text(user, client_id, **kwargs)
        case SharedMenu.ADD_VISIT_SOCIAL_MEDIA:
            text = adding_social_media_text(user, client_id, **kwargs)
        case SharedMenu.ADD_VISIT_PHONE_NUMBER:
            text = adding_phone_number_text(user, client_id, **kwargs)
        case SharedMenu.ADD_VISIT_SERVICE:
            text = adding_service_text(user, client_id, **kwargs)
        case SharedMenu.ADD_VISIT_IMAGES:
            text = adding_photo_text(user, client_id)
        case SharedMenu.ADD_VISIT_IMAGES:
            text = adding_video_text(user, client_id)

    await bot.send_message(TgKeys.ADMIN_GROUP_ID, text, parse_mode=ParseMode.MARKDOWN_V2)


# /start -> 'check_face' -> face found -> 'add_visit' -> 'cancel'
@shared_changer_router.callback_query(F.data == 'cancel', SharedMenu.ADD_VISIT)
async def add_visit_back(callback: types.CallbackQuery, state: FSMContext):
    """ Return to show face info """

    await alert2admins(callback.bot, callback.from_user, state)

    await state.set_state(SharedMenu.SHOW_FACE_INFO)
    await callback.answer()

    keyboard = await add_visit_kb(was_added=True, user_id=callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_name'
@shared_changer_router.message(SharedMenu.ADD_VISIT_NAME)
async def add_visit_name(msg: types.Message, state: FSMContext):
    """ Add visit name """

    name = msg.text.strip()
    if name == '':
        await show_client(msg, state, text=('Не валидное имя\!\n\n' + add_name_text()), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state, name=name)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_name(visit_id, name)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_social_media'
@shared_changer_router.message(SharedMenu.ADD_VISIT_SOCIAL_MEDIA)
async def add_visit_social_media(msg: types.Message, state: FSMContext):
    """ Add visit's social_media """

    social_media = msg.text.strip()
    if social_media == '':
        await show_client(msg, state, text='Не валидные соц сети\!\n\n' + add_social_media_text(), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state, social_media=social_media)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_social_media(visit_id, social_media)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_phone_number'
@shared_changer_router.message(SharedMenu.ADD_VISIT_PHONE_NUMBER)
async def add_visit_phone_number(msg: types.Message, state: FSMContext):
    """ Add visit's phone_number """

    try:
        phone_number = phonenumbers.parse(msg.text.strip(), region=PHONE_NUMBER_REGION)
        if not phonenumbers.is_valid_number(phone_number):
            raise phonenumbers.NumberParseException(5, 'Validation not passed!')
    except phonenumbers.NumberParseException as e:
        logging.info(f'User {msg.from_user.username} ({msg.from_user.id}) sent invalid phone number: {str(e)}')
        await show_client(msg, state, text='Не валидный номер телефона\!\n\n' + add_phone_number_text(), reply_markup=cancel_keyboard('Назад'))

    await alert2admins(msg.bot, msg.from_user, state, phone_number=phone_number)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await update_visit_phone_number(visit_id, phone_number)
    await state.set_state(SharedMenu.ADD_VISIT)

    await show_client(msg, state, reply_markup=add_visit_info_kb())


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_service'
@shared_changer_router.message(SharedMenu.ADD_VISIT_SERVICE)
async def add_visit_service(msg: types.Message, state: FSMContext):
    """ Add visit services """

    service = msg.text.strip()
    if service == '':
        await show_client(msg, state, text='Не валидный сервис\!\n\n' + add_service_text(), reply_markup=cancel_keyboard('Назад'))
        return

    await alert2admins(msg.bot, msg.from_user, state, service=service)

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    await create_visit_service(visit_id, service)
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
                msg.answer(cancel_previous_processing(), reply_markup=cancel_keyboard('Отменить'), parse_mode=ParseMode.MARKDOWN_V2),
                state
            )
            return
        else:
            await cancel_all_tokens(state)

    add_image_token = CancellationToken()
    await state.update_data(add_image_token=add_image_token)  # set token to not None

    image_path, message = await download_document(msg, state, add_image_token, additional_text='Загрузка изображения на фото хостинг 🔗')
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
            msg.reply('Не удалось загрузить на хостинг\! 😟\n\n' + add_image_text(),
                      reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return

    add_image_token.complete()
    await state.update_data(add_image_token=add_image_token)

    await message.edit_text('Фотография загружена\!\n'
                            'Отправьте ещё или нажмите назад\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)


# /start -> 'check_face' -> face found -> 'add_visit' -> 'add_videos'
@shared_changer_router.message(SharedMenu.ADD_VISIT_VIDEOS, F.content_type == ContentType.VIDEO)
async def add_visit_videos(msg: types.Message, state: FSMContext):
    """ Add visit videos """

    state_data = await state.get_data()
    add_video_token: CancellationToken = state_data.get('add_video_token')

    # Add image is still processing
    if add_video_token is not None:
        if not add_video_token.completed:
            await change_msg(
                msg.answer(cancel_previous_processing(), reply_markup=cancel_keyboard('Отменить'), parse_mode=ParseMode.MARKDOWN_V2),
                state
            )
            return
        else:
            await cancel_all_tokens(state)

    add_video_token = CancellationToken()
    await state.update_data(add_video_token=add_video_token)  # set token to not None

    video_path, message = await download_video(msg, state, add_video_token, additional_text='Загрузка видео в облако 🔗')
    if add_video_token.completed or video_path is None:
        return

    state_data = await state.get_data()
    visit_id = state_data.get('visit_id')

    try:
        await create_video_from_path(video_path, visit_id)
        await alert2admins(msg.bot, msg.from_user, state)
    except Exception as e:
        logging.error(str(e))
        await change_msg(
            msg.reply('Что\-то пошло не так\! 😟\n\n' + add_image_text(),
                      reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return

    add_video_token.complete()
    await state.update_data(add_video_token=add_video_token)

    await message.edit_text('Видео загружается\!\n'
                            'Отправьте ещё или нажмите назад\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)


# /start -> 'check_face' -> face found -> 'add_visit' -> '...' -> 'cancel'
@shared_changer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.ADD_VISIT_NAME,
    SharedMenu.ADD_VISIT_SOCIAL_MEDIA,
    SharedMenu.ADD_VISIT_PHONE_NUMBER,
    SharedMenu.ADD_VISIT_SERVICE,
    SharedMenu.ADD_VISIT_IMAGES,
    SharedMenu.ADD_VISIT_VIDEOS
))
async def add_visit_data_back(callback: types.CallbackQuery, state: FSMContext):
    """ Return to adding new visit data """

    await cancel_all_tokens(state)

    state_data = await state.get_data()
    client_id = state_data.get('client_id')

    await state.set_state(SharedMenu.ADD_VISIT)
    await callback.answer()

    text = await face_info_text(client_id, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=add_visit_info_kb(), parse_mode=ParseMode.MARKDOWN_V2)
