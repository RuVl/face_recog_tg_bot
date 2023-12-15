from datetime import datetime

from core.database import session_maker
from core.database.models import Visit
from core.misc import str2int


async def create_visit(client_id: int | str, location_id: int | str) -> Visit:
    """ Create a new visit of a client with user location and returns it """

    client_id, location_id = str2int(client_id, location_id)

    async with session_maker() as session:
        visit = Visit(client_id=client_id, date=datetime.utcnow(), location_id=location_id)

        session.add(visit)
        await session.commit()

        await session.refresh(visit)
        return visit
