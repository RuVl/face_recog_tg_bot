from sqlalchemy import select, and_

from core.database import session_maker
from core.database.models import User


async def get_moderator(telegram_id: int) -> User | None:
    async with session_maker() as session:
        query = select(User).where(and_(User.is_moderator, User.telegram_id == telegram_id))
        return await session.scalar(query)


async def get_all_moderators() -> list[User]:
    async with session_maker() as session:
        query = select(User).where(User.is_moderator)
        result = await session.scalars(query)
        return result.all()
