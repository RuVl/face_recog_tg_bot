from sqlalchemy import select

from core.database import session_maker
from core.database.models import Service


async def get_client_services(client_id: int) -> list[Service]:
    """ Returns a list of services by given client_id """

    async with session_maker() as session:
        query = select(Service).where(Service.client_id == client_id)
        result = await session.scalars(query)
        return result.all()
