from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.database import session_maker
from core.database.models import Visit
from core.misc.adapters import str2int


async def get_client_visits_with_location(client_id: int) -> list[Visit]:
    """ Returns a list of Visits with its locations by given client_id """

    client_id, = str2int(client_id)

    async with session_maker() as session:
        query = select(Visit).where(Visit.client_id == client_id).options(joinedload(Visit.location))
        result = await session.scalars(query)
        return result.all()


async def get_visit_with_location(visit_id: int | str) -> Visit:
    """ Returns visit by id with its location """

    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        query = select(Visit).where(Visit.id == visit_id).options(joinedload(Visit.location))
        return await session.scalar(query)
