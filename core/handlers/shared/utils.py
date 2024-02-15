from pathlib import Path

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InputMediaPhoto

from core import bot
from core.database.models import Client
from core.keyboards.inline import cancel_keyboard
from core.keyboards.inline.shared import select_clients_kb
from core.misc import TgKeys
from core.state_machines import SharedMenu
from core.text import face_info_text


async def show_client(msg: types.Message, state: FSMContext, reply_markup: types.InlineKeyboardMarkup):
    """ Show the client (photo with caption and buttons). Needs client_id and client_photo_path in state data """

    state_data = await state.get_data()

    client_id = state_data.get('client_id')
    face_path = state_data.get('client_photo_path')

    text = await face_info_text(client_id)
    await msg.answer_photo(
        FSInputFile(face_path), caption=text,
        reply_markup=reply_markup, parse_mode='MarkdownV2'
    )


async def show_clients_choosing(msg: types.Message, state: FSMContext, page=None):
    """ Show the clients photos and buttons to choose them """

    COLS = 3
    ROWS = 2

    state_data = await state.get_data()

    face_gallery_msg: types.Message = state_data.get('face_gallery_msg')
    if face_gallery_msg is not None:
        await face_gallery_msg.delete()

    if page is None:
        page: int = state_data.get('page', 0)

    clients: list[Client] = state_data.get('possible_clients')
    if clients is None:
        await msg.answer('Что-то пошло не так, повторите попытку\.\n'
                         'Приносим свои извинения за неудобство 😣',
                         reply_markup=cancel_keyboard('Назад'), parse_mode='MarkdownV2')
        return

    clients2show = clients[page * COLS * ROWS: (page + 1) * COLS * ROWS]

    media_msg = await msg.answer_media_group([
        InputMediaPhoto(
            media=FSInputFile(client.profile_picture.path),
            caption=f'· {client.id} ·',
            parse_mode='MarkdownV2'
        ) for client in clients2show
    ])

    await msg.answer('Выберите этого человека из нескольких распознанных выше\.\n'
                     'Если такого человека нет \- нажмите добавить нового',
                     reply_markup=select_clients_kb(clients, page, cols=COLS, rows=ROWS), parse_mode='MarkdownV2')

    await state.update_data(face_gallery_msg=media_msg)


async def notify_admins(callback: types.CallbackQuery, state: FSMContext):
    """ Send notification to admin chat according to the current state """

    state_data = await state.get_data()

    username = callback.from_user.username.strip() or 'пользователь'
    user_str = f'[{username}](tg://user?id={callback.from_user.id})'

    # Check if the path exists and send the message or photo
    async def safe_send_photo(path, caption):
        if path and Path(path).exists():
            await bot.safe_send_photo(TgKeys.ADMIN_GROUP_ID, FSInputFile(path),
                                      caption=caption, parse_mode='MarkdownV2')
        else:
            await bot.send_message(TgKeys.ADMIN_GROUP_ID, f'`фото не найдено`' + caption,
                                   parse_mode='MarkdownV2')

    match await state.get_state():
        case SharedMenu.NOT_CHOSEN:
            face_path_temp = state_data.get('temp_image_path')
            clients: list[Client] = state_data.get('possible_clients')

            if isinstance(clients, list) and 0 < len(clients) <= 10:
                await safe_send_photo(face_path_temp, f'{user_str} создал нового клиента при выборе:')

                await bot.send_media_group(
                    TgKeys.ADMIN_GROUP_ID,
                    media=[InputMediaPhoto(
                        media=FSInputFile(client.profile_picture.path),
                        caption=f'id: `{client.id}`',
                        parse_mode='MarkdownV2'
                    ) for client in clients]
                )
            else:
                all_clients_str = ('`' + '`, `'.join([clients]) + '`') if clients else 'данные не сохранились'
                await safe_send_photo(face_path_temp, f'{user_str} создал нового клиента при выборе:\n{all_clients_str}')

        case SharedMenu.ADD_NEW_CLIENT:
            face_path_temp = state_data.get('temp_image_path')
            await safe_send_photo(face_path_temp, f'Такое лицо не было найдено в базе данных\n'
                                                  f'{user_str} добавил такое лицо в базу данных')