from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from core.filters import IsAdminMessageFilter, IsAdminCallbackFilter
from core.handlers.admin.menu import admin_menu_router
from core.handlers.shared import SHARED_CALLBACK_COMMANDS
from core.handlers.utils import change_msg
from core.keyboards.inline import admin_start_menu, admin_menu
from core.state_machines import AdminMenu
from core.text.admin import admin_menu_text, hi_admin_text

admin_router = Router()
admin_router.include_routers(admin_menu_router)

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

    await change_msg(
        msg.answer(hi_admin_text(), reply_markup=admin_start_menu(), parse_mode=ParseMode.MARKDOWN_V2),
        state, clear_state=True
    )

    await state.set_state(AdminMenu.START)


@admin_router.callback_query(F.data.not_in(SHARED_CALLBACK_COMMANDS), AdminMenu.START)
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Select in start menu """

    if callback.data == 'admin_menu':
        await state.set_state(AdminMenu.ADMIN_MENU)
        await callback.answer()

        await callback.message.edit_text(admin_menu_text(), reply_markup=admin_menu(), parse_mode=ParseMode.MARKDOWN_V2)
        return


@admin_router.callback_query(F.data == 'back', AdminMenu.ADMIN_MENU)
async def back(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminMenu.START)
    await callback.answer()

    await callback.message.edit_text(hi_admin_text(), reply_markup=admin_start_menu(), parse_mode=ParseMode.MARKDOWN_V2)
