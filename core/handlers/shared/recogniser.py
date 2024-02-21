import shutil

from aiogram import F, types, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from cancel_token import CancellationToken

from core.callback_factory import PaginatorFactory
from core.config import MEDIA_DIR
from core.database.methods.client import load_clients_profile_images, create_client, get_client
from core.database.methods.user import check_if_admin, check_if_moderator
from core.handlers.shared import show_client, show_clients_choosing, notify_admins
from core.handlers.utils import download_image, find_faces, clear_temp_image
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
            await msg.answer(cancel_previous_processing(),
                             reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2')
            return
        else:
            await clear_temp_image(state)

    # cancel to stop, completed if exited
    check_face_token = CancellationToken()
    await state.update_data(check_face_token=check_face_token)  # set token to not None

    # Download image from the message
    image_path, message = await download_image(msg, check_face_token)
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

    # if len(clients) == 1:  # Found 1 face
    #     client = clients[0]
    #
    #     # TODO save telegram_image_id for this image
    #     profile_picture = await get_image_by_id(client.profile_picture_id)
    #
    #     await state.update_data(client_id=client.id, client_photo_path=profile_picture.path)
    #     await state.set_state(SharedMenu.SHOW_FACE_INFO)
    #
    #     await show_client(message, state, add_visit_kb())
    #     await message.delete()
    # else:  # Found more than one face
    clients = await load_clients_profile_images(clients)

    await state.update_data(possible_clients=clients)
    await state.set_state(SharedMenu.CHOOSE_FACE)

    await show_clients_choosing(message, state)
    await message.delete()

    check_face_token.complete()


# /start -> 'check_face' -> [...] -> 'cancel'
@shared_recognizer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.CHECK_FACE,
    SharedMenu.GET_BY_ID,
    SharedMenu.SHOW_FACE_INFO,
    SharedMenu.CHOOSE_FACE,
    SharedMenu.NOT_CHOSEN
))
async def return2start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Returns user to moderator or admin menu (or nothing if user neither admin nor moderator) """

    await clear_temp_image(state)

    if await check_if_admin(callback.from_user.id):
        await state.set_state(AdminMenu.START)
        await callback.answer()
        await callback.message.answer('Здравствуйте, админ 👑',
                                      reply_markup=admin_start_menu(), parse_mode='MarkdownV2')
    elif await check_if_moderator(callback.from_user.id):
        await state.set_state(ModeratorMenu.START)
        await callback.answer()
        await callback.message.answer('Здравствуйте, модератор 💼',
                                      reply_markup=moderator_start_menu(), parse_mode='MarkdownV2')
    else:
        await state.set_state(AnyoneMenu.START)
        await callback.answer()
        await callback.message.edit_text('Здравствуйте, возможно вас понизили в должности ☹️',
                                         reply_markup=anyone_start_menu(), parse_mode='MarkdownV2')


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

            await show_client(callback.message, state, add_visit_kb())
            await callback.message.delete()


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

            await state.update_data(client_id=client.id, client_photo_path=client.profile_picture.path)

            await show_client(callback.message, state, add_visit_kb())
            await callback.message.delete()

    await callback.answer()


# /start -> 'check_face' -> document provided -> found some faces -> 'add_new_client'
@shared_recognizer_router.callback_query(SharedMenu.NOT_CHOSEN, F.data != 'cancel')
async def sure2add_new_client(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'no':
            await state.set_state(SharedMenu.CHOOSE_FACE)
            await show_clients_choosing(callback.message, state)

            await callback.answer()
            await callback.message.delete()
        case 'yes':
            await add_new_client(callback, state)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(PaginatorFactory.filter(F.action == 'change_page'), SharedMenu.CHOOSE_FACE)
async def change_page(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
    await show_clients_choosing(callback.message, state, callback_data.page)

    await callback.answer()
    await callback.message.delete()
