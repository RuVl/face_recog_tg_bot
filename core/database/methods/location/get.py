from sqlalchemy import select

from core.database import session_maker
from core.database.models import Location
from core.misc.adapters import str2int


async def get_all_locations() -> list[Location]:
    async with session_maker() as session:
        query = select(Location)
        result = await session.scalars(query)
        return result.all()


async def get_location(location_id: int | str) -> Location:
    location_id, = str2int(location_id)

    async with session_maker() as session:
        query = select(Location).where(Location.id == location_id)
        return await session.scalar(query)
