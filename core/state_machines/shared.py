from aiogram.fsm.state import StatesGroup, State


class SharedMenu(StatesGroup):
    """ State machine for admin and moderator menu """

    CHECK_FACE = State()  # /start -> 'check_face'
    GET_BY_ID = State()  # /start -> 'get_by_id'

    ADD_NEW_FACE = State()  # 'check_face' -> face not found
    SHOW_FACE_INFO = State()  # 'check_face' -> face found

    ADD_VISIT = State()  # face found -> 'add_visit'

    ADD_VISIT_NAME = State()  # 'add_visit' -> 'add_name'
    ADD_VISIT_CONTACTS = State()  # 'add_visit' -> 'add_contact'

    ADD_VISIT_SERVICE = State()  # 'add_visit' -> 'add_service'
    ADD_VISIT_IMAGES = State()  # 'add_visit' -> 'add_images'
