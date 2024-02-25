from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from core.filters import IsModeratorMessageFilter, IsModeratorCallbackFilter
from core.handlers.utils import change_msg
from core.keyboards.inline import moderator_start_menu
from core.state_machines import ModeratorMenu
from core.text.moderator import hi_moderator_text

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

    await change_msg(
        msg.answer(hi_moderator_text(), reply_markup=moderator_start_menu(), parse_mode='MarkdownV2'),
        state, clear_state=True
    )

    await state.set_state(ModeratorMenu.START)
