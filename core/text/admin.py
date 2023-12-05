def add_moderator_text(moderator_id: int | str = 'введите', location: str = 'выберите') -> str:
    return ('Добавление модератора 💼\n'
            '\n'
            f'id пользователя: `{moderator_id}`\n'
            f'локация: `{location}`')


def added_moderator_text(updated: bool = True) -> str:
    return 'Добавлен модератор' if updated else 'Пользователь уже является модератором'
