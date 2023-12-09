from aiogram.fsm.state import StatesGroup, State


class SharedMenu(StatesGroup):
    """ State machine for admin and moderator menu """

    CHECK_FACE = State()  # /start -> 'check_face'
