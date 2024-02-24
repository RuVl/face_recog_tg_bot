from aiogram import types


def created_visit(user: types.User, client_id: int, is_new=True) -> str:
    return (f'`{user.id}` \- `{user.username}` начал добавлять информацию о `{client_id}` записи\!'
            if is_new else
            f'`{user.id}` \- `{user.username}` продолжил добавлять информацию о `{client_id}` записи\!')


def exit_visit(user: types.User, client_id: int) -> str:
    return f'`{user.id}` \- `{user.username}` перестал добавлять информацию о `{client_id}` записи\.'


def adding_name(user: types.User, client_id: int) -> str:
    return f'`{user.id}` \- `{user.username}` добавил имя к `{client_id}` записи\!'


def adding_contacts(user: types.User, client_id: int) -> str:
    return f'`{user.id}` \- `{user.username}` добавил контакты к `{client_id}` записи\!'


def adding_services(user: types.User, client_id: int) -> str:
    return f'`{user.id}` \- `{user.username}` добавил сервис к `{client_id}` записи\!'


def adding_photos(user: types.User, client_id: int) -> str:
    return f'`{user.id}` \- `{user.username}` добавил фото к `{client_id}` записи\!'
