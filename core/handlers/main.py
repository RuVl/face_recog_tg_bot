from aiogram import Dispatcher, Router

from core.middlewares import DropEmptyButtonMiddleware, ThrottlingMiddleware
from . import moderator_router, admin_router, admin_moderator_router, anyone_router


def register_all_handlers(dp: Dispatcher) -> None:
    main_router = Router()

    # Keep order
    main_router.include_routers(admin_router, moderator_router, admin_moderator_router, anyone_router)

    main_router.callback_query.outer_middleware(ThrottlingMiddleware())
    main_router.callback_query.outer_middleware(DropEmptyButtonMiddleware())

    dp.include_router(main_router)
