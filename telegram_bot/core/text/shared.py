import phonenumbers

from core.database.methods.image import get_client_images
from core.database.methods.service import get_client_services
from core.database.methods.user import check_if_admin
from core.database.methods.video import get_client_videos
from core.database.methods.visit import get_visit_with_location, get_client_visits_with_location
from core.database.models import Visit, Service, Image, Video
from core.text.utils import escape_markdown_v2


def send_me_image() -> str:
	return ('Отправьте фотографию как `документ` \(до 10мб\)\.\n'
	        'Допустимые форматы: `.jpg`, `.heic`')


def cancel_previous_processing() -> str:
	return 'Отмените предыдущую обработку прежде чем отправлять новую фотографию\. 🤔'


def file_downloaded() -> str:
	return '✅ Файл скачан\.'


def add_name_text() -> str:
	return 'Введите `имя`:'


def add_social_media_text() -> str:
	return 'Введите `соц сети` одним сообщением:'


def add_phone_number_text() -> str:
	return 'Введите `номер телефона` одним сообщением:'


def add_service_text() -> str:
	return 'Введите `сервис`:'


def add_image_text() -> str:
	return ('Отправьте мне `фото` как документ\.\n'
	        'Поддерживаемые форматы: `jpg` и `heic`')


def add_video_text() -> str:
	return 'Отправьте мне `видео`\.'


async def face_info_text(
		client_id: int | str,
		user_id: int | str = None,
		*,
		images: list[Image] = None,
		videos: list[Video] = None,
		visits: list[Visit] = None,
		services: list[Service] = None
) -> str:
	""" Returns text info about client """

	is_admin = await check_if_admin(user_id) if user_id is not None else False

	if is_admin and images is None:
		images = await get_client_images(client_id)

	if videos is None:
		videos = await get_client_videos(client_id)

	if visits is None:
		visits = await get_client_visits_with_location(client_id)

	if services is None:
		services = await get_client_services(client_id)

	result = f'*id в базе:* `{client_id}`\n\n'

	if is_admin:
		images_str = '\n'.join(
			f'`{image.url}`'
			for image in images
			if image.url is not None
		).strip()

		if images_str != '' and images_str != '``':
			result += ('*Ссылки на фотографии:*\n'
			           f'{images_str}\n\n')

	videos_str = '\n'.join(
		f'`{video.url}`'
		for video in videos
		if video.url is not None
	).strip()

	if videos_str != '' and videos_str != '``':
		result += ('*Ссылки на видео:*\n'
		           f'{videos_str}\n\n')

	# All contacts from visits
	social_media_str = '\n'.join(set(
		f'`{contact}`'
		for visit in visits
		if visit.social_media is not None
		for contact in visit.social_media.split('\n')
	)).strip()

	if social_media_str != '':
		result += ('*Соц сети:*\n'
		           f'{social_media_str}\n\n')

	# All phone numbers from visits
	phone_number_str = '\n'.join(set(
		f'`{phonenumbers.format_number(visit.phone_number, phonenumbers.PhoneNumberFormat.E164)}`'
		for visit in visits
		if visit.phone_number is not None
	))

	if phone_number_str != '':
		result += ('*Номера телефонов:*\n'
		           f'{phone_number_str}\n\n')

	# Check if each visit has location
	for i in range(len(visits)):
		if visits[i].location is None:
			visits[i] = await get_visit_with_location(visits[i].id)

	# All names with dates and locations
	name_and_date_str = '\n'.join(
		f"{escape_markdown_v2(visit.name) or 'Отсутствует'} "
		f"\({visit.date:%H:%M %d\.%m\.%Y}\) "
		f"\- {escape_markdown_v2(visit.location.address) or 'отсутствует'}"
		for visit in visits
	).strip()

	if name_and_date_str != '':
		result += ('*Имя и дата:*\n'
		           f'{name_and_date_str}\n\n')

	# All services
	services_list = [
		f'{escape_markdown_v2(service.title)} \({service.date:%H:%M %d\.%m\.%Y}\)'
		for service in services
	]

	services_str = '\n'.join(services_list).strip()

	if services_str != '':
		result += ('*Сервисы:*\n'
		           f'{services_str}\n\n')

	return result
