def hi_admin_text() -> str:
	return 'Здравствуйте, админ 👑'


def admin_menu_text() -> str:
	return ('Меню админа 👑\n'
	        'Выберите действие с модераторами:')


def select_moderator_text() -> str:
	return 'Выберите модератора 💼'


def add_moderator_text(moderator_id: int | str = 'введите', location: str = 'выберите') -> str:
	return ('Добавление модератора 💼\n'
	        '\n'
	        f'id пользователя: `{moderator_id}`\n'
	        f'локация: `{location}`')


def edit_moderator_text(tg_id: int | str, username: str, address: str) -> str:
	return ('Модератор 💼\n'
	        '\n'
	        f'id: `{tg_id}`\n'
	        f'имя пользователя: `{username}`\n'
	        f'локация: `{address}`')


def added_moderator_text(updated: bool = True) -> str:
	return 'Добавлен модератор' if updated else 'Пользователь уже является модератором'
