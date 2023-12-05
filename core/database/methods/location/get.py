from sqlalchemy import select

from core.database import session_maker
from core.database.models import Location


async def get_all_locations() -> list[Location]:
    async with session_maker() as session:
        query = select(Location)
        result = await session.scalars(query)
        return result.all()


async def get_location(id_: int) -> Location:
    async with session_maker() as session:
        query = select(Location).where(Location.id == id_)
        return await session.scalar(query)
