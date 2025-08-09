from aiogram.fsm.state import StatesGroup, State


class AnyoneMenu(StatesGroup):
	START = State()  # '/start'

	CHECK_IF_EXIST = State()  # '/start' -> 'check_if_exist'
