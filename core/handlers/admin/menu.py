from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext

from core.callback_factory import PaginatorFactory
from core.database.methods.location import create_location, get_location
from core.database.methods.user import check_if_moderator, create_or_set_moderator, delete_moderator, get_moderator_with_location, get_moderator, \
    change_location
from core.handlers.utils import change_msg
from core.keyboards.inline import cancel_keyboard, select_location, add_location, admin_menu, select_moderator, edit_moderator, yes_no_cancel
from core.state_machines import AdminMenu
from core.text import add_moderator_text, added_moderator_text, edit_moderator_text
from core.text.admin import admin_menu_text, select_moderator_text

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

            keyboard = await select_moderator()
            await callback.message.edit_text(select_moderator_text(), reply_markup=keyboard, parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator'
@admin_menu_router.message(AdminMenu.ADD_MODERATOR)
async def add_moderator_id(msg: types.Message, state: FSMContext):
    """ Add new moderator branch. Select user by id in message """

    # Validate telegram id
    try:
        id_ = int(msg.text)
    except ValueError:
        await change_msg(
            msg.answer('Это не похоже на id пользователя\!\n\n' + add_moderator_text(),
                       reply_markup=cancel_keyboard(), parse_mode='MarkdownV2'),
            state
        )
        return

    try:
        chat = await msg.bot.get_chat(id_)
    except TelegramBadRequest:
        await state.update_data(new_moderator_id=id_)
        await state.set_state(AdminMenu.ADD_ID_ANYWAY)
        await change_msg(
            msg.answer('Пользователь с таким id не найден, возможно из\-за настроек приватности\.\n'
                       'Всё равно добавить?',
                       reply_markup=yes_no_cancel(), parse_mode='MarkdownV2'),
            state
        )
        return

    if chat.type != 'private':
        await change_msg(
            msg.answer('Это не id пользователя\!\n\n' + add_moderator_text(),
                       reply_markup=cancel_keyboard(), parse_mode='MarkdownV2'),
            state
        )
        return

    if await check_if_moderator(chat.id):
        await change_msg(
            msg.answer(added_moderator_text(False), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2'),
            state
        )
        return

    await state.update_data(new_moderator_id=chat.id)
    await state.set_state(AdminMenu.SELECT_LOCATION)

    keyboard = await select_location()
    await change_msg(
        msg.answer(add_moderator_text(chat.id), reply_markup=keyboard, parse_mode='MarkdownV2'),
        state
    )


# /start -> 'admin_menu' -> 'add_moderator' -> user with id not found
@admin_menu_router.callback_query(F.data != 'cancel', AdminMenu.ADD_ID_ANYWAY)
async def add_id_anyway(callback: types.CallbackQuery, state: FSMContext):
    """ Add not valid (not found with bot.get_chat) id anyway """

    match callback.data:
        case 'yes':
            state_data = await state.get_data()
            moderator_id = int(state_data.get("new_moderator_id"))

            if await check_if_moderator(moderator_id):
                await callback.message.edit_text(added_moderator_text(False), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')
                return

            await state.update_data(new_moderator_id=moderator_id)
            await state.set_state(AdminMenu.SELECT_LOCATION)
            await callback.answer()

            keyboard = await select_location()
            await callback.message.edit_text(add_moderator_text(moderator_id), reply_markup=keyboard, parse_mode='MarkdownV2')
        case 'no':
            await state.set_state(AdminMenu.ADD_MODERATOR)
            await callback.answer()
            await callback.message.edit_text(add_moderator_text(), reply_markup=cancel_keyboard(), parse_mode='MarkdownV2')


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
        await callback.answer('Что-то пошло не так.\nПовторите попытку.')
        await callback.message.edit_text(add_moderator_text(moderator_id), reply_markup=select_location(), parse_mode='MarkdownV2')
        return

    updated = await create_or_set_moderator(moderator_id, location.id)

    await state.set_state(AdminMenu.ADMIN_MENU)
    await callback.answer(added_moderator_text(updated))

    await callback.message.edit_text(admin_menu_text(), reply_markup=admin_menu(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'add_moderator' -> id passed -> 'add_location'
@admin_menu_router.message(AdminMenu.ADD_LOCATION)
async def add_moderator_new_location(msg: types.Message, state: FSMContext):
    """ Add new location and create new moderator """

    state_data = await state.get_data()
    moderator_id = int(state_data.get("new_moderator_id"))

    location = await create_location(msg.text)
    updated = await create_or_set_moderator(moderator_id, location.id)

    await change_msg(
        msg.answer(added_moderator_text(updated), reply_markup=cancel_keyboard('Назад в меню'), parse_mode='MarkdownV2'),
        state
    )


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
    AdminMenu.ADD_MODERATOR, AdminMenu.ADD_ID_ANYWAY, AdminMenu.SELECT_LOCATION, AdminMenu.ADD_LOCATION
))
async def cancel_add_moderator(callback: types.CallbackQuery, state: FSMContext):
    """ Cancel adding moderator (or successful added). """

    await state.set_state(AdminMenu.ADMIN_MENU)
    await callback.answer()
    await callback.message.edit_text(admin_menu_text(), reply_markup=admin_menu(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'moderators_list'
@admin_menu_router.callback_query(AdminMenu.MODERATORS_LIST, ~PaginatorFactory.filter(F.action == 'change_page'))
async def moderators_list(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'back':
        await state.set_state(AdminMenu.ADMIN_MENU)
        await callback.answer()
        await callback.message.edit_text(admin_menu_text(), reply_markup=admin_menu(), parse_mode='MarkdownV2')
        return

    mod_id, mod_tg_id = callback.data.split('-')

    moderator = await get_moderator_with_location(mod_tg_id)
    if moderator is None or str(moderator.id) != mod_id:
        await callback.answer('Что-то пошло не так.\n'
                              'Повторите попытку.')

        keyboard = await select_moderator()
        await callback.message.edit_text(select_moderator_text(), reply_markup=keyboard, parse_mode='MarkdownV2')
        return

    await state.update_data(edit_moderator_id=moderator.telegram_id)
    await state.set_state(AdminMenu.EDIT_MODERATOR)

    await callback.answer()
    await callback.message.edit_text(edit_moderator_text(moderator.telegram_id, moderator.username, moderator.location.address),
                                     reply_markup=edit_moderator(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'moderators_list' -> moderator selected
@admin_menu_router.callback_query(AdminMenu.EDIT_MODERATOR)
async def admin_edit_moderator(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    mod_tg_id = state_data.get('edit_moderator_id')
    moderator = await get_moderator_with_location(mod_tg_id)

    match callback.data:
        case 'change_location_moderator':
            await state.set_state(AdminMenu.CHANGE_LOCATION)
            await callback.answer()

            keyboard = await select_location()
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        case 'delete_moderator':
            await delete_moderator(moderator.telegram_id)
            await state.set_state(AdminMenu.ADMIN_MENU)

            await callback.answer('Модератор удалён')
            await callback.message.edit_text(admin_menu_text(), reply_markup=admin_menu(), parse_mode='MarkdownV2')
        case 'back':
            await state.set_state(AdminMenu.MODERATORS_LIST)
            await callback.answer()

            keyboard = await select_moderator()
            await callback.message.edit_text(select_moderator_text(), reply_markup=keyboard, parse_mode='MarkdownV2')
            return


# /start -> 'admin_menu' -> 'moderators_list' -> moderator selected -> 'change_location'
@admin_menu_router.callback_query(F.data != 'cancel', AdminMenu.CHANGE_LOCATION, ~PaginatorFactory.filter(F.action == 'change_page'))
async def moderator_change_location(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    mod_tg_id = state_data.get('edit_moderator_id')

    if callback.data == 'add_location':
        moderator = await get_moderator(mod_tg_id)
        await state.set_state(AdminMenu.NEW_LOCATION)
        await callback.answer()

        await callback.message.edit_text(
            edit_moderator_text(moderator.telegram_id, moderator.username, 'введите'),
            reply_markup=add_location(), parse_mode='MarkdownV2')
        return

    loc_id, loc_address = callback.data.split('-')
    await change_location(mod_tg_id, loc_id)
    await callback.answer('Изменено')

    moderator = await get_moderator_with_location(mod_tg_id)

    await state.set_state(AdminMenu.EDIT_MODERATOR)
    await callback.message.edit_text(edit_moderator_text(moderator.telegram_id, moderator.username, moderator.location.address),
                                     reply_markup=edit_moderator(), parse_mode='MarkdownV2')


# /start -> 'admin_menu' -> 'moderators_list' -> moderator selected -> 'change_location' -> 'add_location'
@admin_menu_router.message(AdminMenu.NEW_LOCATION)
async def moderator_add_location(msg: types.Message, state: FSMContext):
    state_data = await state.get_data()
    mod_tg_id = state_data.get('edit_moderator_id')

    location = await create_location(msg.text)
    await change_location(mod_tg_id, location.id)
    await state.set_state(AdminMenu.EDIT_MODERATOR)

    moderator = await get_moderator_with_location(mod_tg_id)
    await change_msg(
        msg.answer(edit_moderator_text(moderator.telegram_id, moderator.username, moderator.location.address),
                   reply_markup=edit_moderator(), parse_mode='MarkdownV2'),
        state
    )


# /start -> 'admin_menu' -> 'moderators_list' -> moderator selected -> 'change_location' -> 'add_location' -> back
@admin_menu_router.callback_query(F.data != 'cancel', AdminMenu.NEW_LOCATION)
async def moderator_add_location_switch(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'back':
        await state.set_state(AdminMenu.CHANGE_LOCATION)
        await callback.answer()

        keyboard = await select_location()
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        return


@admin_menu_router.callback_query(F.data == 'cancel', or_f(
    AdminMenu.CHANGE_LOCATION, AdminMenu.NEW_LOCATION
))
async def cancel_edit_moderator(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminMenu.EDIT_MODERATOR)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=edit_moderator())


# /start -> 'admin_menu' -> [...] -> 'change_page'
@admin_menu_router.callback_query(PaginatorFactory.filter(F.action == 'change_page'), or_f(
    AdminMenu.SELECT_LOCATION, AdminMenu.MODERATORS_LIST, AdminMenu.CHANGE_LOCATION
))
async def page_changer(callback: types.CallbackQuery, callback_data: PaginatorFactory, state: FSMContext):
    """ Universal change page (generate keyboard for each state) """

    match await state.get_state():
        case AdminMenu.SELECT_LOCATION | AdminMenu.CHANGE_LOCATION:
            keyboard = await select_location(callback_data.page)
        case AdminMenu.MODERATORS_LIST:
            keyboard = await select_moderator(callback_data.page)
        case _:
            await callback.answer('Не реализовано!')
            return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=keyboard)
