from aiogram import Router, F, types
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.database.methods.client import get_client
from core.database.methods.image import get_image_by_id
from core.filters import IsAdminOrModeratorMessageFilter, IsAdminOrModeratorCallbackFilter
from core.handlers.shared import show_client
from core.keyboards.inline import cancel_keyboard, add_visit_kb
from core.state_machines import AdminMenu, ModeratorMenu, SharedMenu
from core.text import send_me_image

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


# /start -> 'get_by_id'
@admin_moderator_router.message(SharedMenu.GET_BY_ID)
async def get_by_id(msg: types.Message, state: FSMContext):
    try:
        client_id = int(msg.text)
    except ValueError:
        await msg.reply('Должен быть числом\!', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    client = await get_client(client_id)
    if client is None:
        await msg.answer('Не найден\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    profile_picture = await get_image_by_id(client.profile_picture_id)

    # TODO save telegram_image_id for this image
    await state.update_data(client_id=client.id, client_photo_path=profile_picture.path)
    await state.set_state(SharedMenu.SHOW_FACE_INFO)

    await show_client(msg, state, add_visit_kb())