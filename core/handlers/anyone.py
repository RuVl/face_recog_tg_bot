from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from cancel_token import CancellationToken

from core.database.methods.image import get_image_by_id
from core.handlers.utils import download_image, find_faces, clear_temp_image
from core.keyboards.inline import anyone_start_menu, cancel_keyboard
from core.state_machines import AnyoneMenu
from core.text import send_me_image, cancel_previous_processing, file_downloaded

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
    """ Validate and download the provided file. Find a face on it and check if it exists in db. """

    state_data = await state.get_data()
    check_face_token: CancellationToken = state_data.get('check_face_token')

    # Face recognition is still running
    if check_face_token is not None and not check_face_token.completed:
        await msg.answer(cancel_previous_processing(),
                         reply_markup=cancel_keyboard('Отменить'), parse_mode='MarkdownV2')
        return

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
        await message.edit_text('Нет в базе\!',
                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    if len(clients) == 1:  # Found 1 face
        client = clients[0]

        # TODO save telegram_image_id for this image
        profile_picture = await get_image_by_id(client.profile_picture_id)

        await message.answer_photo(
            FSInputFile(profile_picture.path), caption=f'*id в базе:* `{client.id}`',
            reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'
        )
        await message.delete()
    else:  # Found more than one face
        await message.edit_text(
            'Найдено более одного совпадения в базе данных\.\n'
            'В целях конфиденциальности мы не можем показать результаты 😟',
            reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'
        )

    check_face_token.complete()


# /start -> 'check_if_exist' -> document provided -> 'cancel'
@anyone_router.callback_query(F.data == 'cancel', AnyoneMenu.CHECK_IF_EXIST)
async def cancel_check_face(callback: types.CallbackQuery, state: FSMContext):
    """ Return to the main menu """

    await clear_temp_image(state)
    await state.set_state(AnyoneMenu.START)

    await callback.answer()
    await callback.message.answer('Здравствуйте, выберите действие\.', reply_markup=anyone_start_menu(), parse_mode='MarkdownV2')
    await callback.message.delete()
