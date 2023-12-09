from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from core.database import session_maker
from core.database.models import User
from core.misc import str2int


async def get_moderator(telegram_id: int | str) -> User | None:
    """ Get User.is_moderator """

    telegram_id, = str2int(telegram_id)

    async with session_maker() as session:
        query = select(User).where(and_(User.is_moderator, User.telegram_id == telegram_id))
        return await session.scalar(query)


async def get_moderator_with_location(telegram_id: int | str) -> User | None:
    """ Get User.is_moderator with location relationship """

    telegram_id, = str2int(telegram_id)

    async with session_maker() as session:
        query = select(User).where(and_(User.is_moderator, User.telegram_id == telegram_id)
                                   ).options(joinedload(User.location))
        return await session.scalar(query)


async def get_all_moderators() -> list[User]:
    """ Returns all moderators """

    async with session_maker() as session:
        query = select(User).where(User.is_moderator)
        result = await session.scalars(query)
        return result.all()
