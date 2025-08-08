from aiogram.fsm.state import StatesGroup, State


class ModeratorMenu(StatesGroup):
	""" State machine for a moderator menu """

	START = State()  # /start
