import logging
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError, ImageOps, ImageFile
from aiogram import types, methods
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from core.cancel_token import CancellationToken
from deepface import DeepFace

from core.config import SUPPORTED_IMAGE_TYPES, TEMP_DIR, MODEL, BACKEND
from core.database.methods.client import get_all_clients
from core.database.models import Client
from core.face_recognition.main import compare_faces
from core.keyboards.inline import cancel_keyboard

ImageFile.LOAD_TRUNCATED_IMAGES = True


async def download_image(msg: types.Message, state: FSMContext, cancellation_token: CancellationToken) -> tuple[Path | None, types.Message]:
    """
        Download the document from msg to TEMP_DIR, check if it is an image and validate its resolution.
        Returns a path to image and editable message.
        If the task is canceled or errors have occurred, it returns None.
    """

    # File is too big
    if msg.document.file_size > 10 * 1024 * 1024:
        message = await change_msg(
            msg.reply('Файл слишком большой\! \(Не более 10мб\) 😖', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'),
            state
        )
        cancellation_token.complete()
        return None, message

    # Unsupported file type
    if msg.document.mime_type not in SUPPORTED_IMAGE_TYPES.keys():
        message = await change_msg(
            msg.reply('Файл неподдерживаемого формата\! 😩', reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2'),
            state
        )
        cancellation_token.complete()
        return None, message

    message = await change_msg(
        msg.answer('Скачивание файла\. 📄', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2'),
        state
    )

    # Create temporary directory
    TEMP_DIR.mkdir(exist_ok=True)

    filename = msg.document.file_id + SUPPORTED_IMAGE_TYPES[msg.document.mime_type]
    document_path = TEMP_DIR / filename

    if cancellation_token.cancelled:
        return None, message

    # Download image
    await msg.bot.download(msg.document, document_path)

    # Check if the file is downloaded
    if not document_path.exists():
        await message.edit_text('Загрузка файла не удалась\. 😭\n'
                                'Попробуйте ещё раз или обратитесь к админам\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        cancellation_token.complete()
        return None, message

    # Check if the task canceled
    if cancellation_token.cancelled:
        document_path.unlink(missing_ok=True)
        return None, message

    # Check image resolution
    try:
        image = Image.open(document_path)
        w, h = image.size

        if w + h > 10000:
            await message.edit_text('Ширина и высота фотографии в сумме не должны превышать 10000\!',
                                    reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
            document_path.unlink(missing_ok=True)
            cancellation_token.complete()
            return None, message

        if max(w, h) / min(w, h) > 20:
            await message.edit_text('Соотношение высоты к ширине не должно превышать 20\.',
                                    reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')

            document_path.unlink(missing_ok=True)
            cancellation_token.complete()
            return None, message

        # Transpose image by exif data
        ImageOps.exif_transpose(image, in_place=True)
        image.save(document_path)

    except UnidentifiedImageError:
        await message.edit_text('Файл повреждён и не может быть обработан\!\n'
                                'Попробуйте другую отправить фотографию\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')

        document_path.unlink(missing_ok=True)
        cancellation_token.complete()
        return None, message

    return document_path, message


async def find_faces(image_path: Path, msg: types.Message, cancellation_token: CancellationToken) -> tuple[list[Client] | None, dict | None]:
    """
        :param image_path: path to image
        :param msg: the editable message
        :param cancellation_token: the cancellation token

        Find faces on an image and check matches in the database.
        If no faces are found or faces more than 1, it returns None and completes the cancellation token.
        If found matches in the database, it returns a list of Clients, np.ndarray.
        If no matches are found, it returns None, np.ndarray.
    """

    embeddings = DeepFace.represent(str(image_path), model_name=MODEL, detector_backend=BACKEND, enforce_detection=False)

    if cancellation_token.cancelled:
        return None, None

    embeddings = list(filter(lambda e: e['face_confidence'] > .75, embeddings))

    if len(embeddings) > 1:
        await msg.edit_text(f'Обнаружено {len(embeddings)} лиц\!\n'
                            f'На фотографии должен быть только 1 человек\.\n'
                            f'Попробуйте отправить другую фотографию\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        cancellation_token.complete()
        return None, None

    if len(embeddings) == 0:
        await msg.edit_text('Ни одного лица на фотографии не обнаружено\!\n'
                            'Попробуйте отправить другую фотографию\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        cancellation_token.complete()
        return None, None

    await msg.edit_text('📇 Обнаружено 1 лицо\!\n'
                        'Поиск совпадений в базе данных\. 🗄',
                        reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')

    face = embeddings[0]

    # Get known faces encoding
    clients = await get_all_clients()
    known_faces = [client.face_encoding for client in clients]

    if cancellation_token.cancelled:
        return None, None

    # Compare with known faces
    results = compare_faces(known_faces, face)

    # Extract matches
    indexes = np.nonzero(results)[0]  # axe=0

    # Clients with this face aren't found.
    if len(indexes) == 0:
        return None, face  # Return only face encoding

    return [clients[i] for i in indexes], face  # Return an array of clients and face encoding


async def clear_cancellation_tokens(state: FSMContext):
    state_data = await state.get_data()

    check_face_token: CancellationToken = state_data.get('check_face_token')
    if check_face_token is not None and not check_face_token.completed:
        check_face_token.cancel()

    add_image_token: CancellationToken = state_data.get('add_image_token')
    if add_image_token is not None and not add_image_token.completed:
        add_image_token.cancel()


async def clear_gallery(state: FSMContext):
    state_data = await state.get_data()

    face_gallery_msg: list[types.Message] = state_data.get('face_gallery_msg')
    if face_gallery_msg is not None and isinstance(face_gallery_msg, list):
        for msg in face_gallery_msg:
            try:
                await msg.delete()
            except TelegramBadRequest as e:
                logging.warning(f'Exception during delete gallery: {e.message}')


async def clear_path(state: FSMContext):
    state_data = await state.get_data()

    document_path = state_data.get('temp_image_path')
    if document_path is not None:
        Path(document_path).unlink(missing_ok=True)


async def clear_state_data(state: FSMContext, *, clear_state=False):
    """ Delete file in temp_image_path and clear state """

    await clear_cancellation_tokens(state)
    await clear_gallery(state)
    await clear_path(state)

    if clear_state:
        await state.clear()


async def change_msg(awaitable_msg: methods.TelegramMethod[types.Message], state: FSMContext,
                     *, clear_state=False) -> types.Message:
    """
        Deletes last_msg in state if exists.
        Send awaitable_msg, save it in the state and return it.
        If clear_state is True, then state.clear()
    """

    state_data = await state.get_data()

    last_msg: types.Message = state_data.get('last_msg')
    if last_msg is not None:
        try:
            await last_msg.delete()
        except TelegramBadRequest as e:
            logging.warning(f'Exception during delete last_msg: {e.message}')

    if clear_state:
        await state.clear()

    msg = await awaitable_msg
    await state.update_data(last_msg=msg)

    return msg
