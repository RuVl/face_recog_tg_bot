from aiogram import F, Router, types
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from core.callback_factory import PaginatorFactory
from core.database.methods.client import create_client, get_client, load_clients_profile_images
from core.database.methods.user import check_if_admin, check_if_moderator
from core.env import TgKeys
from core.face_recognition import find_faces_with_match
from core.handlers.shared import notify_admins, show_client, show_clients_choosing
from core.handlers.utils import TokenCancelCheck, change_msg, download_image_document, handler_with_token
from core.keyboards.inline import add_visit_kb, admin_start_menu, anyone_start_menu, moderator_start_menu, yes_no_cancel
from core.state_machines import AdminMenu, AnyoneMenu, ModeratorMenu, SharedMenu
from core.state_machines.clearing import clear_all_in_one, clear_gallery
from core.state_machines.fields import CHECK_FACE_TOKEN, TEMP_PATH_FIELD
from core.text import face_info_text
from core.text.admin import hi_admin_text
from core.text.moderator import hi_moderator_text

shared_recognizer_router = Router()


# /start -> 'check_face' -> document provided
@shared_recognizer_router.message(SharedMenu.CHECK_FACE, F.content_type == ContentType.DOCUMENT)
@handler_with_token(token_name=CHECK_FACE_TOKEN)
async def check_face(msg: types.Message, state: FSMContext, token_canceled: TokenCancelCheck):
	""" Validate and download the provided file. Find a face on it and compare with others. """

	is_moderator = await check_if_moderator(msg.from_user.id)

	async def notify_admins(text: str) -> types.Message | None:
		if not is_moderator:
			return None

		try:
			msg2admins = await msg.forward(TgKeys.ADMIN_GROUP_ID)
		except:
			return await msg.bot.send_document(chat_id=TgKeys.ADMIN_GROUP_ID,
			                                   document=FSInputFile(image_path),
			                                   caption=text,
			                                   parse_mode=ParseMode.MARKDOWN_V2)

		return await msg2admins.reply(text, parse_mode=ParseMode.MARKDOWN_V2)

	# Download image from the message
	image_path, message = await download_image_document(msg, state, token_canceled, additional_text='Поиск лица на фотографии\. 🔎')

	if image_path is None or await token_canceled():
		return

	await state.update_data({TEMP_PATH_FIELD: image_path})

	# Find face on image and compare with faces in db
	clients, encoding = await find_faces_with_match(image_path, message, token_canceled)

	if await token_canceled():
		return

	if encoding is None:
		await notify_admins(f'Модератор `{msg.from_user.username}` \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
		                    f'Распознавание лиц не завершилось успехом:\n{message.text}')
		return

	# Face not found in db
	if clients is None:
		await notify_admins(f'Модератор `{msg.from_user.username}` \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
		                    f'Такого лица нет в базе данных\!\n'
		                    f'Модератору предложено добавить нового человека\.')

		await state.set_state(SharedMenu.NOT_FOUND)
		await state.update_data(face_encoding=encoding)

		await message.edit_text('Нет в базе\! 🤯\n'
		                        'Добавить такого человека?',
		                        reply_markup=yes_no_cancel(None), parse_mode=ParseMode.MARKDOWN_V2)
		return

	# Get the list of possible clients by their ids and update check_face_token
	clients = await load_clients_profile_images(clients)

	await state.update_data(face_encoding=encoding, possible_clients=clients)
	await state.set_state(SharedMenu.CHOOSE_FACE)

	await notify_admins(f'Модератор `{msg.from_user.username}` \({msg.from_user.id}\) отправил фото для поиска в бд\.\n'
	                    f'В базе данных найдено {len(clients)} похожих лиц\!\n'
	                    f'Модератору предложен выбор\.')
	await show_clients_choosing(message, state)


# /start -> 'check_face' -> [...] -> 'cancel'
@shared_recognizer_router.callback_query(F.data == 'cancel', or_f(
	SharedMenu.CHECK_FACE,
	SharedMenu.GET_BY_ID,
	SharedMenu.GET_BY_PHONE_NUMBER,
	SharedMenu.CHOOSE_FACE,
	SharedMenu.NOT_CHOSEN,
	SharedMenu.SHOW_FACE_INFO
))
async def return2start_menu(callback: types.CallbackQuery, state: FSMContext):
	""" Returns user to moderator or admin menu (or nothing if user neither admin nor moderator) """

	await clear_all_in_one(state, clear_state=True)

	if await check_if_admin(callback.from_user.id):
		new_state = AdminMenu.START
		text = hi_admin_text()
		keyboard = admin_start_menu()

	elif await check_if_moderator(callback.from_user.id):
		new_state = ModeratorMenu.START
		text = hi_moderator_text()
		keyboard = moderator_start_menu()

	else:
		new_state = AnyoneMenu.START
		text = 'Здравствуйте, вас понизили в должности ☹️'
		keyboard = anyone_start_menu()

	await callback.answer()
	await change_msg(
		callback.message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2),
		state
	)
	await state.set_state(new_state)


# /start -> 'check_face' -> document provided -> face not found
@shared_recognizer_router.callback_query(SharedMenu.NOT_FOUND)
async def add_new_client(callback: types.CallbackQuery, state: FSMContext):
	match callback.data:
		case 'no':
			await return2start_menu(callback, state)
			return
		case 'yes':
			state_data = await state.get_data()

			if state_data.get('creating_client', False):
				await callback.answer('Подождите, клиент создается.')
				return

			await state.update_data(creating_client=True)

			face_path_temp = state_data.get(TEMP_PATH_FIELD)
			face_encoding = state_data.get('face_encoding')

			client = await create_client(face_path_temp, face_encoding)

			await notify_admins(callback, state, client=client)

			await state.set_state(SharedMenu.SHOW_FACE_INFO)
			await callback.answer('Клиент добавлен в базу данных!')
			await state.update_data(client_id=client.id)

			keyboard = await add_visit_kb(user_id=callback.from_user.id)
			await show_client(callback.message, state, reply_markup=keyboard)

			await state.update_data(creating_client=False)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(SharedMenu.CHOOSE_FACE,
                                         ~PaginatorFactory.filter(F.action == 'change_page'),
                                         F.data != 'cancel')
async def choose_face(callback: types.CallbackQuery, state: FSMContext):
	match callback.data:
		case 'add_new_client':
			await state.set_state(SharedMenu.NOT_CHOSEN)
			await callback.message.edit_text('Вы уверены?',
			                                 reply_markup=yes_no_cancel(), parse_mode=ParseMode.MARKDOWN_V2)
		case client_id:
			try:
				client = await get_client(client_id)
			except ValueError:
				await callback.answer('Не валидный ответ!')
				return

			if client is None:
				await callback.answer('Клиент не найден!')
				return

			await state.set_state(SharedMenu.SHOW_FACE_INFO)
			await state.update_data(client_id=client.id)

			await clear_gallery(state)

			keyboard = await add_visit_kb(user_id=callback.from_user.id)
			text = await face_info_text(client_id, callback.from_user.id)
			await show_client(callback.message, state, text=text, reply_markup=keyboard)

	await callback.answer()


# /start -> 'check_face' -> document provided -> found some faces -> 'add_new_client'
@shared_recognizer_router.callback_query(SharedMenu.NOT_CHOSEN, F.data != 'cancel')
async def sure2add_new_client(callback: types.CallbackQuery, state: FSMContext):
	match callback.data:
		case 'no':
			await state.set_state(SharedMenu.CHOOSE_FACE)
			await callback.answer()
			await show_clients_choosing(callback.message, state, delete_gallery=False)
		case 'yes':
			await add_new_client(callback, state)


# /start -> 'check_face' -> document provided -> found some faces
@shared_recognizer_router.callback_query(PaginatorFactory.filter(F.action == 'change_page'), SharedMenu.CHOOSE_FACE)
async def change_page(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
	await callback.answer()
	await show_clients_choosing(callback.message, state, page=callback_data.page)
