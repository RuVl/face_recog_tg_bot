import logging

import phonenumbers
from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.config import PHONE_NUMBER_REGION
from core.database.methods.client import get_client, get_client_by_phone
from core.filters import IsAdminOrModeratorMessageFilter, IsAdminOrModeratorCallbackFilter
from core.handlers.shared import show_client
from core.handlers.shared.changer import shared_changer_router
from core.handlers.utils import change_msg
from core.keyboards.inline import cancel_keyboard, add_visit_kb
from core.state_machines import AdminMenu, ModeratorMenu, SharedMenu
from core.text import send_me_image

admin_moderator_router = Router()
admin_moderator_router.include_routers(shared_changer_router)

admin_moderator_router.message.filter(
    F.chat.type == 'private',
    IsAdminOrModeratorMessageFilter()
)
admin_moderator_router.callback_query.filter(
    IsAdminOrModeratorCallbackFilter()
)

SHARED_CALLBACK_COMMANDS = ['check_face', 'get_by_id', 'get_by_phone_number']


# /start -> 'check_face'
@admin_moderator_router.callback_query(F.data.in_(SHARED_CALLBACK_COMMANDS), or_f(
    AdminMenu.START, ModeratorMenu.START
))
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Branches after /start """

    match callback.data:
        case 'check_face':
            state_ = SharedMenu.CHECK_FACE
            text = send_me_image()
        case 'get_by_id':
            state_ = SharedMenu.GET_BY_ID
            text = 'Отправьте мне `id` клиента в базе данных'
        case 'get_by_phone_number':
            state_ = SharedMenu.GET_BY_PHONE_NUMBER
            text = 'Отправьте мне `номер телефона` клиента в базе данных'

    await state.set_state(state_)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)


# /start -> 'get_by_id'
@admin_moderator_router.message(SharedMenu.GET_BY_ID)
async def get_by_id(msg: types.Message, state: FSMContext):
    try:
        client_id = int(msg.text)
    except ValueError:
        await change_msg(
            msg.reply('Должен быть числом\!\n\n'
                      'Отправьте мне `id` клиента в базе данных',
                      reply_markup=cancel_keyboard(), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return

    client = await get_client(client_id)
    if client is None:
        await change_msg(
            msg.answer('Не найден\!', reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return

    await state.update_data(client_id=client.id)
    await state.set_state(SharedMenu.SHOW_FACE_INFO)

    keyboard = await add_visit_kb(user_id=msg.from_user.id)
    await show_client(msg, state, reply_markup=keyboard)


# /start -> 'get_by_phone_number'
@admin_moderator_router.message(SharedMenu.GET_BY_PHONE_NUMBER)
async def get_by_phone_number(msg: types.Message, state: FSMContext):
    try:
        phone_number = phonenumbers.parse(msg.text.strip(), region=PHONE_NUMBER_REGION)
        if not phonenumbers.is_valid_number(phone_number):
            raise phonenumbers.NumberParseException(5, 'Validation not passed!')
    except phonenumbers.NumberParseException as e:
        logging.info(f'User {msg.from_user.username} ({msg.from_user.id}) sent invalid phone number: {str(e)}')
        await change_msg(
            msg.answer('Не валидный номер\!', reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )

    client = await get_client_by_phone(phone_number)
    if client is None:
        await change_msg(
            msg.answer('Не найден\!', reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return

    await state.update_data(client_id=client.id)
    await state.set_state(SharedMenu.SHOW_FACE_INFO)

    keyboard = await add_visit_kb(user_id=msg.from_user.id)
    await show_client(msg, state, reply_markup=keyboard)
