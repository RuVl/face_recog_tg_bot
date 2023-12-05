from aiogram import Dispatcher, Router

from . import moderator_router, admin_router


def register_all_handlers(dp: Dispatcher) -> None:
    main_router = Router()
    main_router.include_routers(admin_router, moderator_router)  # Admin router first

    dp.include_router(main_router)
