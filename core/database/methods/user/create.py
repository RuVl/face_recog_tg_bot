from sqlalchemy import select

from core.database import session_maker
from core.database.models import User


async def create_or_set_moderator(telegram_id: int, location_id: int) -> bool:
    """
        Create a new moderator or add moderator rights.
        :return: True if user updated
    """

    async with session_maker() as session:
        query = select(User).where(User.telegram_id == telegram_id)
        user = await session.scalar(query)

        if user:
            if user.is_moderator:
                return False

            user.is_moderator = True
            user.location_id = location_id
            await session.commit()

            return True

        user = User(telegram_id=telegram_id, is_moderator=True, location_id=location_id)
        session.add(user)
        await session.commit()

        return True
