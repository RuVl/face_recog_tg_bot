from core.database import session_maker
from core.database.models import Location


async def create_location(address: str) -> Location:
    async with session_maker() as session:
        location = Location(address=address)

        session.add(location)
        await session.commit()

        return location
