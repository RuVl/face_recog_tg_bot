from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.callback_factory import PaginatorFactory
from core.database.methods.location import create_location, get_location
from core.database.methods.user import check_if_moderator, create_or_set_moderator
from core.keyboards.inline import cancel_keyboard, select_location, add_location, admin_menu, select_moderator
from core.state_machines import AdminMenu
from core.text import add_moderator_text, added_moderator_text

admin_menu_router = Router()


# /start -> 'admin_menu'
@admin_menu_router.callback_query(AdminMenu.ADMIN_MENU)
async def handle_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    """ Select button in admin menu """

    match callback.data:
        case 'add_moderator':
            await state.set_state(AdminMenu.ADD_MODERATOR)
            await callback.answer()
            await callback.message.edit_text(add_moderator_text(), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        case 'moderators_list':
            await state.set_state(AdminMenu.MODERATORS_LIST)
            await callback.answer()
            await callback.message.edit_text('Выберите модератора 💼', reply_markup=select_moderator(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator'
@admin_menu_router.message(AdminMenu.ADD_MODERATOR)
async def add_moderator_id(msg: types.Message, state: FSMContext):
    """ Add new moderator branch. Select user by id in message """

    # Validate telegram id
    try:
        chat = await msg.bot.get_chat(msg.text)
    except TelegramBadRequest:
        await msg.answer('Пользователь с таким id не найден', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    if chat.type != 'private':
        await msg.answer('Это не id пользователя', reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    if await check_if_moderator(chat.id):
        await msg.answer(added_moderator_text(False), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
        return

    await state.update_data(new_moderator_id=chat.id)
    await state.set_state(AdminMenu.SELECT_LOCATION)

    keyboard = await select_location()
    await msg.answer(add_moderator_text(chat.id), reply_markup=keyboard, parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator' -> id passed
@admin_menu_router.callback_query(F.data != 'cancel', AdminMenu.SELECT_LOCATION, ~PaginatorFactory.filter(F.action == 'change_page'))
async def add_moderator_location(callback: types.CallbackQuery, state: FSMContext):
    """ Add new moderator branch. Select button with location. """

    state_data = await state.get_data()
    moderator_id = int(state_data.get("new_moderator_id"))

    if callback.data == 'add_location':
        await state.set_state(AdminMenu.ADD_LOCATION)
        await callback.answer()

        await callback.message.edit_text(add_moderator_text(moderator_id, 'введите'), reply_markup=add_location(), parse_mode='MarkdownV2')
        return

    location_id, location_address = callback.data.split('-')
    location = await get_location(int(location_id))

    if location.address != location_address:
        await callback.answer('Что-то пошло не так.\n'
                              'Повторите попытку.')

        await callback.message.edit_text(add_moderator_text(moderator_id), reply_markup=select_location(), parse_mode='MarkdownV2')
        return

    updated = await create_or_set_moderator(moderator_id, location.id)

    await state.set_state(AdminMenu.ADMIN_MENU)
    await callback.answer(added_moderator_text(updated))

    await callback.message.edit_text('Меню админа 👑', reply_markup=admin_menu(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator' -> id passed -> 'change_page'
@admin_menu_router.callback_query(AdminMenu.SELECT_LOCATION, PaginatorFactory.filter(F.action == 'change_page'))
async def add_moderator_location_change_page(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
    """ Change page with locations """

    state_data = await state.get_data()
    moderator_id = state_data.get("new_moderator_id")

    keyboard = await select_location(callback_data.page)
    await callback.message.edit_text(add_moderator_text(moderator_id), reply_markup=keyboard, parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator' -> id passed -> 'add_location'
@admin_menu_router.message(AdminMenu.ADD_LOCATION)
async def add_moderator_new_location(msg: types.Message, state: FSMContext):
    """ Add new location and create new moderator """

    state_data = await state.get_data()
    moderator_id = int(state_data.get("new_moderator_id"))

    location = await create_location(msg.text)
    updated = await create_or_set_moderator(moderator_id, location.id)

    await msg.answer(added_moderator_text(updated), reply_markup=cancel_keyboard('Назад в меню'), parse_mode='MarkdownV2')


# /start -> admin_menu -> add_moderator -> id passed -> add_location -> back
@admin_menu_router.callback_query(F.data != 'cancel', AdminMenu.ADD_LOCATION)
async def add_moderator_new_location_switch(callback: types.CallbackQuery, state: FSMContext):
    """ Was pressed inline button instead of adding new location """

    state_data = await state.get_data()
    moderator_id = int(state_data.get("new_moderator_id"))

    if callback.data == 'back':
        await state.set_state(AdminMenu.SELECT_LOCATION)
        await callback.answer()

        keyboard = await select_location()
        await callback.message.edit_text(add_moderator_text(moderator_id), reply_markup=keyboard, parse_mode='MarkdownV2')
        return


# /start -> 'admin_menu' -> 'add_moderator' -> [...] -> 'cancel'
@admin_menu_router.callback_query(F.data == 'cancel', or_f(
    AdminMenu.ADD_MODERATOR, AdminMenu.SELECT_LOCATION, AdminMenu.ADD_LOCATION
))
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    """ Cancel adding moderator (or successful added). """

    await state.set_state(AdminMenu.ADMIN_MENU)
    await callback.answer()

    await callback.message.edit_text('Меню админа 👑', reply_markup=admin_menu(), parse_mode='MarkdownV2')


@admin_menu_router.callback_query(AdminMenu.MODERATORS_LIST)
async def edit_moderators(callback: types.CallbackQuery, state: FSMContext):
    pass
