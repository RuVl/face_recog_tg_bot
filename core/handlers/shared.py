import face_recognition
from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.config import MEDIA_DIR, LOCATION_MODEL_NAME, ENCODING_MODEL_NAME, TOLERANCE
from core.database.methods.user import check_if_admin, check_if_moderator
from core.filters import IsAdminOrModeratorMessageFilter, IsAdminOrModeratorCallbackFilter
from core.keyboards.inline import cancel_keyboard, admin_start_menu, moderator_start_menu
from core.state_machines import AdminMenu, ModeratorMenu, SharedMenu

admin_moderator_router = Router()

admin_moderator_router.message.filter(
    F.chat.type == 'private',
    IsAdminOrModeratorMessageFilter()
)
admin_moderator_router.callback_query.filter(
    IsAdminOrModeratorCallbackFilter()
)


@admin_moderator_router.callback_query(F.data == 'check_face', or_f(
    AdminMenu.START, ModeratorMenu.START
))
async def start_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Wait for document """

    await state.set_state(SharedMenu.CHECK_FACE)
    await callback.answer()
    await callback.message.edit_text('Отправьте фотографию как `документ` \(до 20мб\)\.\n'
                                     'Допустимые форматы: `.jpg, .heic`',
                                     reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')


@admin_moderator_router.message(SharedMenu.CHECK_FACE, F.content_type == ContentType.DOCUMENT)
async def check_face(msg: types.Message, state: FSMContext):
    """ Validate and download provided file. Find face on it and compare with others. """

    if msg.document.file_size > 20 * 1024 * 1024:
        await msg.answer('Файл слишком большой\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    if msg.document.mime_type not in ['image/jpeg', 'image/heif']:
        await msg.answer('Файл некорректного формата\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await state.update_data(check_face=True)
    message = await msg.answer('Скачивание файла 📄', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    file = await msg.bot.download(msg.document, MEDIA_DIR)

    if file is None:
        await message.edit_text('Что\-то пошло не так\.', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    # Was cancel
    if not (await state.get_data()).get('check_face'):
        return

    await message.edit_text('Файл скачан\.\n'
                            'Поиск лица на фотографии\.', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    image = face_recognition.load_image_file(file)
    face_locations = face_recognition.face_locations(image, model=LOCATION_MODEL_NAME)

    if len(face_locations) == 0:
        await message.edit_text('Ни одного лица не обнаружено\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    if len(face_locations) > 1:
        await message.edit_text(f'Обнаружено {len(face_locations)} лиц\.\n'
                                'На фотографии должно быть только 1 лицо\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    face_encodings = face_recognition.face_encodings(image, face_locations, model=ENCODING_MODEL_NAME)

    await message.edit_text('Обнаружено 1 лицо\.\n'
                            'Проверяю на наличие такого же лица в базе данных\.', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    # TODO get all encodings from database and compare
    # face_recognition.compare_faces(tolerance=TOLERANCE)


@admin_moderator_router.callback_query(F.data == 'cancel', SharedMenu.CHECK_FACE)
async def check_face(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(check_face=False)

    if await check_if_admin(callback.from_user.id):
        await state.set_state(AdminMenu.START)
        await callback.answer()

        await callback.message.edit_text('Здравствуйте, админ 👑', reply_markup=admin_start_menu(), parse_mode='MarkdownV2')

    elif await check_if_moderator(callback.from_user.id):
        await state.set_state(ModeratorMenu.START)

        await callback.answer()
        await callback.message.edit_text('Здравствуйте, модератор 💼', reply_markup=moderator_start_menu(), parse_mode='MarkdownV2')
