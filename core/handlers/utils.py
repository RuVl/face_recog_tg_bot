import asyncio
import functools
import logging
from pathlib import Path
from typing import Callable, Awaitable

import numpy as np
from PIL import Image, UnidentifiedImageError, ImageOps, ImageFile
from aiogram import types, methods
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from deepface import DeepFace

from core.cancel_token import CancellationToken
from core.config import SUPPORTED_IMAGE_TYPES, TEMP_DIR, MODEL, BACKEND, SUPPORTED_VIDEO_TYPES
from core.database.methods.client import get_all_clients
from core.database.models import Client
from core.face_recognition.main import compare_faces
from core.keyboards.inline import cancel_keyboard
from core.state_machines.clearing import clear_all_in_one, cancel_token, complete_token
from core.state_machines.fields import LAST_MESSAGE_FIELD
from core.text import file_downloaded

ImageFile.LOAD_TRUNCATED_IMAGES = True

TokenCancelCheck = Callable[[], Awaitable[bool]]

change_msg_lock = asyncio.Lock()


async def token_is_canceled(token: CancellationToken, token_name: str, state: FSMContext) -> bool:
    state_data = await state.get_data()
    t: CancellationToken = state_data.get(token_name)
    return t != token or t.canceled


def handler_with_token(token_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            state: FSMContext = kwargs['state']
            state_data = await state.get_data()

            token: CancellationToken = state_data.get(token_name)
            if token is not None and not token.completed:
                await cancel_token(state, token_name)

            token = CancellationToken()
            await state.update_data({token_name: token})

            kwargs['token_canceled'] = functools.partial(token_is_canceled, token, token_name, state)

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await complete_token(state, token_name)

            return result
        return wrapper
    return decorator


async def download_media(msg: types.Message, state: FSMContext,
                         media: types.Video | types.Document,
                         supported_types: dict[str, str],
                         token_canceled: TokenCancelCheck) -> tuple[Path | None, types.Message]:
    """
        Download the document from the msg.
        Cancellation token for stop downloading.
        Editable message for alarm if it can't be downloaded.
        Media parameter must have the following attributes: mime_type, file_unique_id, file_id
    """

    # Unsupported file type
    if media.mime_type not in supported_types.keys():
        message = await change_msg(
            msg.reply('Файл неподдерживаемого формата\! 😩',
                      reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return None, message

    message = await change_msg(
        msg.answer('Скачивание файла\. 📄', reply_markup=cancel_keyboard(), parse_mode=ParseMode.MARKDOWN_V2),
        state
    )

    TEMP_DIR.mkdir(exist_ok=True)  # Create temporary directory

    filename = media.file_unique_id + supported_types[media.mime_type]
    document_path = TEMP_DIR / filename

    if await token_canceled():
        return None, message

    # Download image
    await msg.bot.download(media, document_path)

    # Check if the file is downloaded
    if not document_path.exists():
        message = await message.edit_text('Загрузка файла не удалась\. 😭\n'
                                          'Попробуйте ещё раз или обратитесь к админам\.',
                                          reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return None, message

        # Check if the task canceled
    if await token_canceled():
        document_path.unlink(missing_ok=True)
        return None, message

    return document_path, message


async def download_document(msg: types.Message, state: FSMContext, token_canceled: TokenCancelCheck,
                            *, additional_text=None, success_keyboard=cancel_keyboard()) -> tuple[Path | None, types.Message]:
    """
        Download the document from msg to TEMP_DIR, check if it is an image and validate its resolution.
        Returns a path to image and editable message.
        If the task is canceled or errors have occurred, it returns None.
    """

    # File is too big
    if msg.document.file_size > 10 * 1024 * 1024:
        message = await change_msg(
            msg.reply('Файл слишком большой\! \(Не более 10мб\) 😖', reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return None, message

    document_path, message = await download_media(msg, state, msg.document, SUPPORTED_IMAGE_TYPES, token_canceled)

    # Check image resolution
    try:
        image = Image.open(document_path)
        w, h = image.size

        if w + h > 10000:
            await message.edit_text('Ширина и высота фотографии в сумме не должны превышать 10000\!',
                                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
            document_path.unlink(missing_ok=True)
            return None, message

        if max(w, h) / min(w, h) > 20:
            await message.edit_text('Соотношение высоты к ширине не должно превышать 20\.',
                                    reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)

            document_path.unlink(missing_ok=True)
            return None, message

        # Transpose image by exif data
        ImageOps.exif_transpose(image, in_place=True)
        image.save(document_path)

    except UnidentifiedImageError:
        await message.edit_text('Файл повреждён и не может быть обработан\!\n'
                                'Попробуйте другую отправить фотографию\.',
                                reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)

        document_path.unlink(missing_ok=True)
        return None, message

    if await token_canceled():
        document_path.unlink(missing_ok=True)
        return None, message

    text = file_downloaded()
    if additional_text is not None:
        text += f'\n{additional_text}'

    await message.edit_text(text, reply_markup=success_keyboard, parse_mode=ParseMode.MARKDOWN_V2)

    return document_path, message


async def download_video(msg: types.Message, state: FSMContext, token_canceled: TokenCancelCheck,
                         *, additional_text=None, success_keyboard=cancel_keyboard()) -> tuple[Path | None, types.Message]:
    """
        Download the document from msg to TEMP_DIR, check if it is an image and validate its resolution.
        Returns a path to image and editable message.
        If the task is canceled or errors have occurred, it returns None.
    """

    # File is too big
    if msg.video.file_size > 20 * 1024 * 1024:
        message = await change_msg(
            msg.reply('Файл слишком большой\! \(Не более 20мб\) 😖', reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2),
            state
        )
        return None, message

    document_path, message = await download_media(msg, state, msg.video, SUPPORTED_VIDEO_TYPES, token_canceled)

    text = file_downloaded()
    if additional_text is not None:
        text += f'\n{additional_text}'

    await message.edit_text(text, reply_markup=success_keyboard, parse_mode=ParseMode.MARKDOWN_V2)

    return document_path, message


async def find_faces(image_path: Path, msg: types.Message, token_canceled: TokenCancelCheck) -> tuple[list[Client] | None, dict | None]:
    """
        :param image_path: path to image
        :param msg: the editable message
        :param token_canceled: the cancel check function

        Find faces on an image and check matches in the database.
        If no faces are found or faces more than 1, it returns None and completes the cancellation token.
        If found matches in the database, it returns a list of Clients, np.ndarray.
        If no matches are found, it returns None, np.ndarray.
    """

    embeddings = DeepFace.represent(str(image_path), model_name=MODEL, detector_backend=BACKEND, enforce_detection=False)

    if await token_canceled():
        return None, None

    embeddings = list(filter(lambda e: e['face_confidence'] > .75, embeddings))

    if len(embeddings) > 1:
        await msg.edit_text(f'Обнаружено {len(embeddings)} лиц\!\n'
                            f'На фотографии должен быть только 1 человек\.\n'
                            f'Попробуйте отправить другую фотографию\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return None, None

    if len(embeddings) == 0:
        await msg.edit_text('Ни одного лица на фотографии не обнаружено\!\n'
                            'Попробуйте отправить другую фотографию\.',
                            reply_markup=cancel_keyboard('Назад'), parse_mode=ParseMode.MARKDOWN_V2)
        return None, None

    await msg.edit_text('📇 Обнаружено 1 лицо\!\n'
                        'Поиск совпадений в базе данных\. 🗄',
                        reply_markup=cancel_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)

    face = embeddings[0]

    # Get known faces encoding
    clients = await get_all_clients()
    known_faces = [client.face_encoding for client in clients]

    if await token_canceled():
        return None, face

    # Compare with known faces
    results = compare_faces(known_faces, face)

    # Extract matches
    indexes = np.nonzero(results)[0]  # axe=0

    # Clients with this face aren't found.
    if len(indexes) == 0:
        return None, face  # Return only face encoding

    return [clients[i] for i in indexes], face  # Return an array of clients and face encoding


async def change_msg(awaitable_msg: methods.TelegramMethod[types.Message], state: FSMContext,
                     *, clear_state=False) -> types.Message:
    """
        Deletes last_msg in state if exists.
        Send awaitable_msg, save it in the state and return it.
        If clear_state is True, then state.clear()
    """

    async with change_msg_lock:
        state_data = await state.get_data()

        last_msg: types.Message = state_data.get(LAST_MESSAGE_FIELD)
        if last_msg is not None:
            try:
                await last_msg.delete()
            except TelegramBadRequest as e:
                logging.warning(f'Exception during delete last message: {e.message}')

        if clear_state:
            await clear_all_in_one(state, clear_state=True)

        msg = await awaitable_msg
        await state.update_data({LAST_MESSAGE_FIELD: msg})

    return msg
