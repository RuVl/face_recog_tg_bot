from sqlalchemy import update

from core.database import session_maker
from core.database.models import User
from core.misc.adapters import str2int


async def update_username(telegram_id: int | str, username: str) -> None:
	""" Update username """

	telegram_id, = str2int(telegram_id)

	async with session_maker() as session:
		query = update(User).where(User.telegram_id == telegram_id).values(username=username)
		await session.execute(query)
		await session.commit()


async def delete_moderator(telegram_id: int = 0) -> None:
	""" Set is_moderator to False """

	telegram_id, = str2int(telegram_id)

	async with session_maker() as session:
		query = update(User).where(User.telegram_id == telegram_id).values(is_moderator=False)
		await session.execute(query)
		await session.commit()


async def change_location(telegram_id: int | str, location_id: int | str) -> None:
	""" Set new location_id """

	telegram_id, location_id = str2int(telegram_id, location_id)

	async with session_maker() as session:
		query = update(User).where(User.telegram_id == telegram_id).values(location_id=location_id)
		await session.execute(query)
		await session.commit()
