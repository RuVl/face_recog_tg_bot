import logging
from pathlib import Path

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InputMediaPhoto

from core.database.methods.image import get_client_images
from core.database.models import Client, Image
from core.handlers.utils import change_msg
from core.keyboards.inline import cancel_keyboard
from core.keyboards.inline.shared import select_clients_kb
from core.env import TgKeys
from core.state_machines import SharedMenu
from core.state_machines.clearing import clear_gallery
from core.state_machines.fields import TEMP_PATH_FIELD
from core.text import face_info_text
from core.text.utils import escape_markdown_v2


async def show_client(msg: types.Message, state: FSMContext,
                      *,
                      text: str = None,
                      reply_markup: types.InlineKeyboardMarkup = None,
                      delete_gallery=True):
	""" Show the client (photo with caption and buttons). Needs client_id and client_photo_path in state data """

	state_data = await state.get_data()

	client_id: int = state_data.get('client_id')
	client_images: list[Image] = state_data.get('client_images')

	if client_images is None:
		client_images = await get_client_images(client_id, limit=10)
		await state.update_data(client_images=client_images)

	if text is None:
		text = await face_info_text(client_id, msg.from_user.id)

	if delete_gallery:
		await clear_gallery(state)

	try:
		media_msg = await msg.answer_media_group([
			InputMediaPhoto(media=FSInputFile(img.path)) for img in client_images
		])
		await state.update_data(face_gallery_msg=media_msg)

		await change_msg(
			msg.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2),
			state
		)
	except TelegramBadRequest as e:
		logging.warning(f'Cannot send image {e.message}')

		images_str = ', '.join([f'`{img.path}`' for img in client_images])
		await msg.bot.send_message(TgKeys.ADMIN_GROUP_ID,
		                           f'Произошла ошибка при отправке фотографии {images_str} клиента `{client_id}`\!\n' +
		                           escape_markdown_v2('Лимиты телеграмм: https://core.telegram.org/bots/api#sending-files'),
		                           parse_mode=ParseMode.MARKDOWN_V2)
		await change_msg(
			msg.answer('Возникла ошибка при отправке фотографии\!\n'
			           'Информация уже отправлена админам\.\n'
			           'Приносим свои извинения за неудобство 😣',
			           reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
			state
		)


async def show_clients_choosing(msg: types.Message, state: FSMContext,
                                *, page=None, delete_gallery=True):
	""" Show the clients photos and buttons to choose them """

	COLS = 3
	ROWS = 2

	state_data = await state.get_data()

	if delete_gallery:
		await clear_gallery(state)

	if page is None:
		page: int = state_data.get('page', 0)

	clients: list[Client] = state_data.get('possible_clients')
	if clients is None:
		await change_msg(
			msg.answer('Что-то пошло не так, повторите попытку\.\n'
			           'Приносим свои извинения за неудобство 😣',
			           reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
			state
		)
		return

	if delete_gallery:
		clients2show = clients[page * COLS * ROWS: (page + 1) * COLS * ROWS]

		try:
			media_msg = await msg.answer_media_group([
				InputMediaPhoto(
					media=FSInputFile(client.profile_picture.path),
					caption=f'· {client.id} ·',
					parse_mode=ParseMode.MARKDOWN_V2
				) for client in clients2show
			])
			await state.update_data(face_gallery_msg=media_msg)
		except TelegramBadRequest as e:
			logging.warning(f'Cannot send image {e.message}')

			clients_id = [str(client.id) for client in clients2show]
			await msg.bot.send_message(TgKeys.ADMIN_GROUP_ID,
			                           f'Произошла ошибка при отправке галереи из клиентов `{"`, `".join(clients_id)}`\!\n' +
			                           escape_markdown_v2('Лимиты телеграмм: https://core.telegram.org/bots/api#sending-files'),
			                           parse_mode=ParseMode.MARKDOWN_V2)
			await change_msg(
				msg.answer('Возникла ошибка при отправке фотографии\!\n'
				           'Информация уже отправлена админам\.\n'
				           'Приносим свои извинения за неудобство 😣',
				           reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
				state
			)
			return

	await change_msg(
		msg.answer('Выберите этого человека из нескольких распознанных выше\.\n'
		           'Если такого человека нет \- нажмите добавить нового',
		           reply_markup=select_clients_kb(clients, page, cols=COLS, rows=ROWS), parse_mode=ParseMode.MARKDOWN_V2),
		state
	)


async def notify_admins(clb: types.CallbackQuery, state: FSMContext, **kwargs):
	""" Send notification to admin chat according to the current state """

	state_data = await state.get_data()

	username = clb.from_user.username.strip() or 'пользователь'
	user_str = f'[{escape_markdown_v2(username)}](tg://user?id={clb.from_user.id})'

	# Check if the path exists and send the message or photo
	async def safe_send_photo(path, caption):
		if path and Path(path).exists():
			await clb.bot.send_photo(TgKeys.ADMIN_GROUP_ID, photo=FSInputFile(path),
			                         caption=caption, parse_mode=ParseMode.MARKDOWN_V2)
		else:
			await clb.bot.send_message(TgKeys.ADMIN_GROUP_ID, f'`фото не найдено` ' + caption,
			                           parse_mode=ParseMode.MARKDOWN_V2)

	match await state.get_state():
		case SharedMenu.NOT_CHOSEN:
			client: Client = kwargs.get('client')
			face_path_temp = client.profile_picture.path or state_data.get(TEMP_PATH_FIELD)
			clients: list[Client] = state_data.get('possible_clients')

			if isinstance(clients, list) and 0 < len(clients) <= 10:
				await safe_send_photo(face_path_temp, f"{user_str} создал нового клиента `{client.id}` при выборе:")

				await clb.bot.send_media_group(
					TgKeys.ADMIN_GROUP_ID,
					media=[InputMediaPhoto(
						media=FSInputFile(client.profile_picture.path),
						caption=f'id: `{client.id}`',
						parse_mode=ParseMode.MARKDOWN_V2
					) for client in clients]
				)
			else:
				all_clients_str = ('`' + '`, `'.join([clients]) + '`') if clients else 'данные не сохранились'
				await safe_send_photo(face_path_temp, f'{user_str} создал нового клиента `{client.id}` при выборе:\n{all_clients_str}')

		case SharedMenu.NOT_FOUND:
			client: Client = kwargs.get('client')
			face_path_temp = client.profile_picture.path or state_data.get(TEMP_PATH_FIELD)
			await safe_send_photo(face_path_temp, f'Такое лицо не было найдено в базе данных\n'
			                                      f'{user_str} добавил такое лицо в базу данных')
