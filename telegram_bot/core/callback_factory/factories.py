from aiogram.filters.callback_data import CallbackData


class PaginatorFactory(CallbackData, prefix='paginator'):
	menu: str
	action: str
	page: int
