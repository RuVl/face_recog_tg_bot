from aiogram import Dispatcher, Router

from . import moderator_router, admin_router
from core.middlewares import DropEmptyButtonMiddleware


def register_all_handlers(dp: Dispatcher) -> None:
    main_router = Router()
    main_router.include_routers(admin_router, moderator_router)  # Admin router first

    main_router.callback_query.outer_middleware(DropEmptyButtonMiddleware())

    dp.include_router(main_router)
