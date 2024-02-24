import shutil

from aiogram import F, types, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from core.cancel_token import CancellationToken

from core.callback_factory import PaginatorFactory
from core.config import MEDIA_DIR
from core.database.methods.client import load_clients_profile_images, create_client, get_client
from core.database.methods.user import check_if_admin, check_if_moderator
from core.handlers.shared import show_client, show_clients_choosing, notify_admins
from core.handlers.utils import download_image, find_faces, clear_state_data, change_msg
from core.keyboards.inline import cancel_keyboard, yes_no_cancel, add_visit_kb, admin_start_menu, moderator_start_menu, anyone_start_menu
from core.state_machines import SharedMenu, AdminMenu, ModeratorMenu, AnyoneMenu
from core.text import cancel_previous_processing, file_downloaded

shared_recognizer_router = Router()


# /start -> 'check_face' -> document provided
@shared_recognizer_router.message(SharedMenu.CHECK_FACE, F.content_type == ContentType.DOCUMENT)
async def check_face(msg: types.Message, state: FSMContext):
    """ Validate and download the provided file. Find a face on it and compare with others. """

    # noinspection DuplicatedCode
    state_data = await state.get_data()
    check_face_token: CancellationToken = state_data.get('check_face_token')

    # Face recognition is still running
    if check_face_token is not None:
        if not check_face_token.completed:
            await change_msg(
                msg.answer(cancel_previous_processing(), reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2'),
                state
            )
            return
        else:
            await clear_state_data(state)

    # cancel to stop, completed if exited
    check_face_token = CancellationToken()
    await state.update_data(check_face_token=check_face_token)  # set token to not None

    # Download image from the message
    image_path, message = await download_image(msg, state, check_face_token)
    if check_face_token.completed or image_path is None:
        return

    await state.update_data(temp_image_path=image_path)
    await message.edit_text(file_downloaded(),
                            reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    clients, encoding = await find_faces(image_path, message, check_face_token)

    if check_face_token.completed:
        return

    if encoding is None:
        await message.edit_text('Распознавание лиц не удалось, повторите попытку\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await state.update_data(face_encoding=encoding)

    if clients is None:
        await state.set_state(SharedMenu.ADD_NEW_CLIENT)
        await message.edit_text('Нет в базе\! 🤯\n'
                                'Добавить такого человека?',
                                reply_markup=yes_no_cancel(None), parse_mode='MarkdownV2')
        return

    clients = await load_clients_profile_images(clients)

    await state.update_data(possible_clients=clients)
    await state.set_state(SharedMenu.CHOOSE_FACE)

    await show_clients_choosing(message, state)
    check_face_token.complete()


# /start -> 'check_face' -> [...] -> 'cancel'
@shared_recognizer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.CHECK_FACE,
    SharedMenu.GET_BY_ID,
    SharedMenu.CHOOSE_FACE,
    SharedMenu.NOT_CHOSEN,
    SharedMenu.SHOW_FACE_INFO
))
async def return2start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Returns user to moderator or admin menu (or nothing if user neither admin nor moderator) """

    await clear_state_data(state)

    if await check_if_admin(callback.from_user.id):
        new_state = AdminMenu.START
        text = 'Здравствуйте, админ 👑'
        keyboard = admin_start_menu()

    elif await check_if_moderator(callback.from_user.id):
        new_state = ModeratorMenu.START
        text = 'Здравствуйте, модератор 💼'
        keyboard = moderator_start_menu()

    else:
        new_state = AnyoneMenu.START
        text = 'Здравствуйте, вас понизили в должности ☹️'
        keyboard = anyone_start_menu()

    await callback.answer()
    await change_msg(
        callback.message.answer(text, reply_markup=keyboard, parse_mode='MarkdownV2'),
        state, clear_state=True
    )
    await state.set_state(new_state)


# /start -> 'check_face' -> document provided -> face not found
@shared_recognizer_router.callback_query(SharedMenu.ADD_NEW_CLIENT)
async def add_new_client(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'no':
            await return2start_menu(callback, state)
            return
        case 'yes':
            await notify_admins(callback, state)

            state_data = await state.get_data()

            face_path_temp = state_data.get('temp_image_path')
            face_path = shutil.copy2(face_path_temp, MEDIA_DIR)
            face_encoding = state_data.get('face_encoding')

            client = await create_client(face_path, face_encoding)

            await state.set_state(SharedMenu.SHOW_FACE_INFO)
            await callback.answer('Клиент добавлен в базу данных!')
            await state.update_data(client_id=client.id, client_photo_path=face_path)

            keyboard = await add_visit_kb(user_id=callback.from_user.id)
            await show_client(callback.message, state, reply_markup=keyboard)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(SharedMenu.CHOOSE_FACE,
                                         ~PaginatorFactory.filter(F.action == 'change_page'),
                                         F.data != 'cancel')
async def choose_face(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'add_new_client':
            await state.set_state(SharedMenu.NOT_CHOSEN)
            await callback.message.edit_text('Вы уверены?',
                                             reply_markup=yes_no_cancel(), parse_mode='MarkdownV2')
        case client_id:
            try:
                client = await get_client(client_id, True)
            except ValueError:
                await callback.answer('Не валидный ответ!')
                return

            if client is None:
                await callback.answer('Клиент не найден!')
                return

            await state.set_state(SharedMenu.SHOW_FACE_INFO)
            await state.update_data(client_id=client.id, client_photo_path=client.profile_picture.path)

            await clear_state_data(state)

            keyboard = await add_visit_kb(user_id=callback.from_user.id)
            await show_client(callback.message, state, reply_markup=keyboard)

    await callback.answer()


# /start -> 'check_face' -> document provided -> found some faces -> 'add_new_client'
@shared_recognizer_router.callback_query(SharedMenu.NOT_CHOSEN, F.data != 'cancel')
async def sure2add_new_client(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'no':
            await state.set_state(SharedMenu.CHOOSE_FACE)
            await callback.answer()
            await show_clients_choosing(callback.message, state)
        case 'yes':
            await add_new_client(callback, state)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(PaginatorFactory.filter(F.action == 'change_page'), SharedMenu.CHOOSE_FACE)
async def change_page(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
    await callback.answer()
    await show_clients_choosing(callback.message, state, callback_data.page)
