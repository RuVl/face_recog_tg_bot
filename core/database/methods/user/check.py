from sqlalchemy import and_, exists, or_

from core.database import session_maker
from core.database.models import User


async def check_if_moderator(telegram_id: int) -> bool:
    async with session_maker() as session:
        query = exists(User).where(and_(
            User.is_moderator,
            User.telegram_id == telegram_id
        )).select()
        return await session.scalar(query)


async def check_if_admin(telegram_id: int) -> bool:
    async with session_maker() as session:
        query = exists(User).where(and_(
            User.is_admin,
            User.telegram_id == telegram_id
        )).select()
        return await session.scalar(query)


async def check_if_moderator_or_admin(telegram_id: int) -> bool:
    async with session_maker() as session:
        query = exists(User).where(and_(
            or_(User.is_moderator, User.is_admin),
            User.telegram_id == telegram_id
        )).select()
        return await session.scalar(query)
