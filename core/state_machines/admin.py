from aiogram.fsm.state import StatesGroup, State


class AdminMenu(StatesGroup):
    """ State machine for admin menu """

    START = State()  # /start

    ADMIN_MENU = State()  # /start -> 'admin_menu'

    ADD_MODERATOR = State()  # 'admin_menu' -> 'add_moderator'
    ADD_ID_ANYWAY = State()  # 'add_moderator' -> id not found

    SELECT_LOCATION = State()  # 'add_moderator' -> id passed
    ADD_LOCATION = State()  # id passed -> 'add_location'

    MODERATORS_LIST = State()  # 'admin_menu' -> 'moderators_list'
    EDIT_MODERATOR = State()  # 'moderators_list' -> moderator selected

    CHANGE_LOCATION = State()  # moderator selected -> 'change_location'
    NEW_LOCATION = State()  # 'change_location' -> 'add_location'
