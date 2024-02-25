from aiogram.fsm.state import State, StatesGroup


class SharedMenu(StatesGroup):
    """ State machine for admin and moderator menu """

    # main.py
    GET_BY_ID = State()  # /start -> 'get_by_id'

    # recognizer.py
    CHECK_FACE = State()  # /start -> 'check_face'

    NOT_FOUND = State()  # 'check_face' -> face not found
    SHOW_FACE_INFO = State()  # 'check_face' -> 1 face found or 1 face chosen

    DELETE_CLIENT = State()  # face found -> 'delete_client'

    CHOOSE_FACE = State()  # 'check_face' -> some face matches
    NOT_CHOSEN = State()  # some face matches -> 'add_new_client'

    # changer.py
    ADD_VISIT = State()  # face found -> 'add_visit'

    ADD_VISIT_NAME = State()  # 'add_visit' -> 'add_name'
    ADD_VISIT_CONTACTS = State()  # 'add_visit' -> 'add_contact'

    ADD_VISIT_SERVICE = State()  # 'add_visit' -> 'add_service'
    ADD_VISIT_IMAGES = State()  # 'add_visit' -> 'add_images'
