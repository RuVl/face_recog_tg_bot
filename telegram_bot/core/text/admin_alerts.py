import phonenumbers
from aiogram import types
from phonenumbers import PhoneNumber


def created_visit_text(user: types.User, client_id: int, is_new: bool = True) -> str:
	return (f'`{user.id}` \- `{user.username}` начал добавлять информацию о `{client_id}` записи\!'
	        if is_new else
	        f'`{user.id}` \- `{user.username}` продолжил добавлять информацию о `{client_id}` записи\!')


def exit_visit_text(user: types.User, client_id: int) -> str:
	return f'`{user.id}` \- `{user.username}` перестал добавлять информацию о `{client_id}` записи\.'


def adding_name_text(user: types.User, client_id: int, name: str = None) -> str:
	return f'`{user.id}` \- `{user.username}` добавил имя: `{name or "нет информации"}` к `{client_id}` записи\!'


def adding_social_media_text(user: types.User, client_id: int, social_media: str = None) -> str:
	return f'`{user.id}` \- `{user.username}` добавил соц\. сети: `{social_media or "нет информации"}` к `{client_id}` записи\!'


def adding_phone_number_text(user: types.User, client_id: int, phone_number: PhoneNumber = None) -> str:
	phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164) or "нет информации"
	return f'`{user.id}` \- `{user.username}` добавил номер телефона: `{phone}` к `{client_id}` записи\!'


def adding_service_text(user: types.User, client_id: int, service: str = None) -> str:
	return f'`{user.id}` \- `{user.username}` добавил сервис: `{service or "Нет информации"}` к `{client_id}` записи\!'


def adding_photo_text(user: types.User, client_id: int) -> str:
	return f'`{user.id}` \- `{user.username}` добавил фото к `{client_id}` записи\!'


def adding_video_text(user: types.User, client_id: int) -> str:
	return f'`{user.id}` \- `{user.username}` добавил видео к `{client_id}` записи\!'
