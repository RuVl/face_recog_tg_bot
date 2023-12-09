from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from core.filters import IsAdminMessageFilter, IsAdminCallbackFilter
from core.handlers.admin.menu import admin_menu_router
from core.keyboards.inline import admin_start_menu, admin_menu
from core.state_machines import AdminMenu

admin_router = Router()
admin_router.include_router(admin_menu_router)

# Filters
admin_router.message.filter(
    F.chat.type == 'private',
    IsAdminMessageFilter()
)
admin_router.callback_query.filter(
    IsAdminCallbackFilter()
)


@admin_router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    """ /start from admin """

    await state.set_state(AdminMenu.START)
    await msg.answer('Здравствуйте, админ 👑', reply_markup=admin_start_menu(), parse_mode='MarkdownV2')


@admin_router.callback_query(F.data != 'check_face', AdminMenu.START)
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Select in start menu """

    if callback.data == 'admin_menu':
        await state.set_state(AdminMenu.ADMIN_MENU)
        await callback.answer()

        await callback.message.edit_text('Меню админа 👑', reply_markup=admin_menu(), parse_mode='MarkdownV2')
        return


@admin_router.callback_query(F.data == 'back', AdminMenu.ADMIN_MENU)
async def back(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminMenu.START)
    await callback.answer()

    await callback.message.edit_text('Здравствуйте, админ 👑', reply_markup=admin_start_menu(), parse_mode='MarkdownV2')
