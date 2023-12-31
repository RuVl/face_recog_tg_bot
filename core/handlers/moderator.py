from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from core.filters import IsModeratorMessageFilter, IsModeratorCallbackFilter
from core.keyboards.inline import moderator_start_menu
from core.state_machines import ModeratorMenu

moderator_router = Router()

# Filters
moderator_router.message.filter(
    F.chat.type == 'private',
    IsModeratorMessageFilter()
)
moderator_router.callback_query.filter(
    IsModeratorCallbackFilter()
)


@moderator_router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    """ /start from moderator """

    await state.set_state(ModeratorMenu.START)
    await msg.answer('Здравствуйте, модератор 💼', reply_markup=moderator_start_menu(), parse_mode='MarkdownV2')
