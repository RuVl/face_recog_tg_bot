from aiogram import F, types, Router
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile

from core.callback_factory import PaginatorFactory
from core.cancel_token import CancellationToken
from core.database.methods.client import load_clients_profile_images, create_client, get_client
from core.database.methods.user import check_if_admin, check_if_moderator
from core.handlers.shared import show_client, show_clients_choosing, notify_admins
from core.handlers.utils import download_image, find_faces, clear_state_data, change_msg
from core.keyboards.inline import cancel_keyboard, yes_no_cancel, add_visit_kb, admin_start_menu, moderator_start_menu, anyone_start_menu
from core.misc import TgKeys
from core.state_machines import SharedMenu, AdminMenu, ModeratorMenu, AnyoneMenu
from core.text import cancel_previous_processing, face_info_text
from core.text.admin import hi_admin_text
from core.text.moderator import hi_moderator_text

shared_recognizer_router = Router()


# /start -> 'check_face' -> document provided
@shared_recognizer_router.message(SharedMenu.CHECK_FACE, F.content_type == ContentType.DOCUMENT)
async def check_face(msg: types.Message, state: FSMContext):
    """ Validate and download the provided file. Find a face on it and compare with others. """

    is_moderator = await check_if_moderator(msg.from_user.id)

    async def notify_admins(text: str) -> types.Message | None:
        if not is_moderator:
            return

        try:
            msg2admins = await msg.forward(TgKeys.ADMIN_GROUP_ID)
        except:
            return await msg.bot.send_document(chat_id=TgKeys.ADMIN_GROUP_ID,
                                               document=InputFile(image_path),
                                               caption=text,
                                               parse_mode=ParseMode.MARKDOWN_V2)

        return await msg2admins.reply(text, parse_mode=ParseMode.MARKDOWN_V2)

    state_data = await state.get_data()
    check_face_token: CancellationToken = state_data.get('check_face_token')

    # Face recognition is still running
    if check_face_token is not None:
        if not check_face_token.completed:
            await change_msg(
                msg.answer(cancel_previous_processing(), reply_markup=cancel_keyboard('Отменить'), parse_mode=ParseMode.MARKDOWN_V2),
                state
            )
            return
        else:
            await clear_state_data(state)

    # cancel to stop, completed if exited
    check_face_token = CancellationToken()
    await state.update_data(check_face_token=check_face_token)  # set token to not None

    # Download image from the message
    image_path, message = await download_image(msg, state, check_face_token, additional_text='Поиск лица на фотографии\. 🔎')
    if check_face_token.completed or image_path is None:
        return

    await state.update_data(temp_image_path=image_path)

    clients, encoding = await find_faces(image_path, message, check_face_token)

    if check_face_token.completed:
        return

    if encoding is None:
        await notify_admins(f'Модератор @{msg.from_user.username} \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
                            f'Распознавание лиц не удалось\!')

        await message.edit_text('Распознавание лиц не удалось, повторите попытку\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return

    await state.update_data(face_encoding=encoding)

    if clients is None:
        await notify_admins(f'Модератор @{msg.from_user.username} \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
                            f'Такого лица нет в базе данных\!\n'
                            f'Модератору предложено добавить нового человека\.')

        await state.set_state(SharedMenu.NOT_FOUND)
        await message.edit_text('Нет в базе\! 🤯\n'
                                'Добавить такого человека?',
                                reply_markup=yes_no_cancel(None), parse_mode=ParseMode.MARKDOWN_V2)
        return

    clients = await load_clients_profile_images(clients)

    await state.update_data(possible_clients=clients)
    await state.set_state(SharedMenu.CHOOSE_FACE)

    check_face_token.complete()
    await state.update_data(check_face_token=check_face_token)

    await notify_admins(f'Модератор @{msg.from_user.username} \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
                        f'В базе данных найдено {len(clients)} похожих лиц\!\n'
                        f'Модератору предложен выбор\.')
    await show_clients_choosing(message, state)


# /start -> 'check_face' -> [...] -> 'cancel'
@shared_recognizer_router.callback_query(F.data == 'cancel', or_f(
    SharedMenu.CHECK_FACE,
    SharedMenu.GET_BY_ID,
    SharedMenu.GET_BY_PHONE_NUMBER,
    SharedMenu.CHOOSE_FACE,
    SharedMenu.NOT_CHOSEN,
    SharedMenu.SHOW_FACE_INFO
))
async def return2start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Returns user to moderator or admin menu (or nothing if user neither admin nor moderator) """

    await clear_state_data(state)

    if await check_if_admin(callback.from_user.id):
        new_state = AdminMenu.START
        text = hi_admin_text()
        keyboard = admin_start_menu()

    elif await check_if_moderator(callback.from_user.id):
        new_state = ModeratorMenu.START
        text = hi_moderator_text()
        keyboard = moderator_start_menu()

    else:
        new_state = AnyoneMenu.START
        text = 'Здравствуйте, вас понизили в должности ☹️'
        keyboard = anyone_start_menu()

    await callback.answer()
    await change_msg(
        callback.message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2),
        state, clear_state=True
    )
    await state.set_state(new_state)


# /start -> 'check_face' -> document provided -> face not found
@shared_recognizer_router.callback_query(SharedMenu.NOT_FOUND)
async def add_new_client(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'no':
            await return2start_menu(callback, state)
            return
        case 'yes':
            state_data = await state.get_data()

            if state_data.get('creating_client', False):
                await callback.answer('Подождите, клиент создается.')
                return

            await state.update_data(creating_client=True)

            face_path_temp = state_data.get('temp_image_path')
            face_encoding = state_data.get('face_encoding')

            client = await create_client(face_path_temp, face_encoding)

            await notify_admins(callback, state, client_id=client.id)

            await state.set_state(SharedMenu.SHOW_FACE_INFO)
            await callback.answer('Клиент добавлен в базу данных!')
            await state.update_data(client_id=client.id)

            keyboard = await add_visit_kb(user_id=callback.from_user.id)
            await show_client(callback.message, state, reply_markup=keyboard)

            await state.update_data(creating_client=False)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(SharedMenu.CHOOSE_FACE,
                                         ~PaginatorFactory.filter(F.action == 'change_page'),
                                         F.data != 'cancel')
async def choose_face(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'add_new_client':
            await state.set_state(SharedMenu.NOT_CHOSEN)
            await callback.message.edit_text('Вы уверены?',
                                             reply_markup=yes_no_cancel(), parse_mode=ParseMode.MARKDOWN_V2)
        case client_id:
            try:
                client = await get_client(client_id)
            except ValueError:
                await callback.answer('Не валидный ответ!')
                return

            if client is None:
                await callback.answer('Клиент не найден!')
                return

            await state.set_state(SharedMenu.SHOW_FACE_INFO)
            await state.update_data(client_id=client.id)

            await clear_state_data(state)

            keyboard = await add_visit_kb(user_id=callback.from_user.id)
            text = await face_info_text(client_id, callback.from_user.id)
            await show_client(callback.message, state, text=text, reply_markup=keyboard)

    await callback.answer()


# /start -> 'check_face' -> document provided -> found some faces -> 'add_new_client'
@shared_recognizer_router.callback_query(SharedMenu.NOT_CHOSEN, F.data != 'cancel')
async def sure2add_new_client(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'no':
            await state.set_state(SharedMenu.CHOOSE_FACE)
            await callback.answer()
            await show_clients_choosing(callback.message, state, delete_gallery=False)
        case 'yes':
            await add_new_client(callback, state)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(PaginatorFactory.filter(F.action == 'change_page'), SharedMenu.CHOOSE_FACE)
async def change_page(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
    await callback.answer()
    await show_clients_choosing(callback.message, state, page=callback_data.page)
