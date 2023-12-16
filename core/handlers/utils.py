from pathlib import Path

import face_recognition
import numpy as np
from aiogram import types
from aiogram.fsm.context import FSMContext

from core.config import SUPPORTED_IMAGE_TYPES, TEMP_DIR, LOCATION_MODEL_NAME, ENCODING_MODEL_NAME, TOLERANCE
from core.database.methods.client import get_all_clients
from core.database.models import Client
from core.keyboards.inline import cancel_keyboard


async def download_image(msg: types.Message, state: FSMContext, cancel_flag: str) -> tuple[Path | None, types.Message]:
    """ Download the file. Returns Path to downloaded image and message to show status """

    # File is so big
    if msg.document.file_size > 20 * 1024 * 1024:
        message = await msg.reply('Файл слишком большой\! 😖', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return None, message

    # Unsupported file type
    if msg.document.mime_type not in SUPPORTED_IMAGE_TYPES.keys():
        message = await msg.reply('Файл неподдерживаемого формата\! 😩', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return None, message

    message = await msg.answer('Скачивание файла\. 📄', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    # Download image
    filename = msg.document.file_id + SUPPORTED_IMAGE_TYPES[msg.document.mime_type]
    document_path = TEMP_DIR / filename

    TEMP_DIR.mkdir(exist_ok=True)
    await msg.bot.download(msg.document, document_path)

    # Was cancel
    if not (await state.get_data()).get(cancel_flag):
        return None, message

    # Is the image downloaded?
    if not document_path.exists():
        await message.edit_text('Загрузка файла не удалась\. 😭\n'
                                'Попробуйте ещё раз или обратитесь к админам\.', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return None, message

    return document_path, message


async def find_faces(image_path: Path, message: types.Message, state: FSMContext, cancel_flag: str) -> Client | np.ndarray | None:
    """ Validate image and find face on it """

    # Prepare and recognize faces on image
    image = face_recognition.load_image_file(image_path)

    # Check if image can be sent to telegram
    w, h, _ = image.shape
    if max(w, h) / min(w, h) > 20:
        await message.edit_text('Соотношение высоты к ширине не должно превышать 20\.',
                                reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    face_locations = face_recognition.face_locations(image, model=LOCATION_MODEL_NAME)

    # Was cancel
    if not (await state.get_data()).get(cancel_flag):
        return

    # Faces not found
    if len(face_locations) == 0:
        await message.edit_text('🚫 Ни одного лица не обнаружено\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    # Found more than one face
    if len(face_locations) > 1:
        await message.edit_text(f'Обнаружено {len(face_locations)} лиц\. 🤔\n'
                                'На фотографии должно быть только 1 лицо\!', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    await message.edit_text('Обнаружено 1 лицо\. 👌\n'
                            'Проверяю на наличие такого же лица в базе данных\.', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    # Get face encodings
    face_encodings = face_recognition.face_encodings(image, face_locations, model=ENCODING_MODEL_NAME)

    # Get known faces encoding
    clients = await get_all_clients()
    known_faces = [client.face_encoding for client in clients]

    # Compare encodings
    results = face_recognition.compare_faces(known_faces, face_encodings[0], tolerance=TOLERANCE)

    # Was cancel
    if not (await state.get_data()).get(cancel_flag):
        return

    # Extract matches
    indexes = np.nonzero(results)[0]  # axe=0
    if len(indexes) == 0:  # Clients with this face aren't found.
        return face_encodings[0]  # Return face encoding

    # Found more than one matches
    if len(indexes) > 1:
        await message.edit_text(f'Найдено {len(indexes)} таких же лиц\. 🤔\n'
                                'Отправлено на решение админам\.', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        # TODO send to admins
        return

    return clients[indexes[0]]  # Return matched client


async def clear_temp(state: FSMContext):
    """ Delete file in temp_photo_path and clear state """

    state_data = await state.get_data()
    document_path = state_data.get('temp_photo_path')

    if document_path is not None:
        document_path = Path(document_path)
        if document_path.exists():
            document_path.unlink()

    await state.clear()
