from aiogram import Router, F, types
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from core.database.methods.image import get_image_by_id
from core.handlers.utils import download_document, find_faces, change_msg, handler_with_token, TokenCancelCheck
from core.keyboards.inline import anyone_start_menu, cancel_keyboard
from core.state_machines import AnyoneMenu
from core.state_machines.clearing import clear_all_in_one
from core.state_machines.fields import CHECK_FACE_FIELD
from core.text import send_me_image

anyone_router = Router()

anyone_router.message.filter(
    F.chat.type == 'private',
)


# '/start'
@anyone_router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    await change_msg(
        msg.answer('Здравствуйте, выберите действие\.', reply_markup=anyone_start_menu(), parse_mode=ParseMode.MARKDOWN_V2),
        state, clear_state=True
    )

    await state.set_state(AnyoneMenu.START)


# '/start' -> action selected
@anyone_router.callback_query(AnyoneMenu.START)
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    match callback.data:
        case 'check_if_exist':
            await state.set_state(AnyoneMenu.CHECK_IF_EXIST)
            await callback.answer()
            await callback.message.edit_text(send_me_image(), reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)


# '/start' -> 'check_if_exist' -> document provided
@anyone_router.message(AnyoneMenu.CHECK_IF_EXIST, F.content_type == ContentType.DOCUMENT)
@handler_with_token(CHECK_FACE_FIELD)
async def check_if_exist_face(msg: types.Message, state: FSMContext, token_canceled: TokenCancelCheck):
    """ Validate and download the provided file. Find a face on it and check if it exists in db. """

    # Download image from the message
    image_path, message = await download_document(msg, state, token_canceled, additional_text='Поиск лица на фотографии\. 🔎')

    if image_path is None or await token_canceled():
        return

    await state.update_data(temp_image_path=image_path)

    clients, encoding = await find_faces(image_path, message, token_canceled)

    if await token_canceled():
        return

    if encoding is None:
        await message.edit_text('Распознавание лиц не удалось, повторите попытку\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return

    await state.update_data(face_encoding=encoding)

    if clients is None:
        await message.edit_text('Нет в базе\!',
                                reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return

    if len(clients) == 1:  # Found 1 face
        client = clients[0]
        profile_picture = await get_image_by_id(client.profile_picture_id)

        await change_msg(
            message.answer_photo(FSInputFile(profile_picture.path), caption=f'*id в базе:* `{client.id}`',
                                 reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
    else:  # Found more than one face
        await message.edit_text(
            'Найдено более одного совпадения в базе данных\.\n'
            'В целях конфиденциальности мы не можем показать результаты 😟',
            reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2
        )


# /start -> 'check_if_exist' -> document provided -> 'cancel'
@anyone_router.callback_query(F.data == 'cancel', AnyoneMenu.CHECK_IF_EXIST)
async def cancel_check_face(callback: types.CallbackQuery, state: FSMContext):
    """ Return to the main menu """

    await clear_all_in_one(state)
    await state.set_state(AnyoneMenu.START)

    await callback.answer()
    await change_msg(
        callback.message.answer('Здравствуйте, выберите действие\.', reply_markup=anyone_start_menu(), parse_mode=ParseMode.MARKDOWN_V2),
        state
    )
