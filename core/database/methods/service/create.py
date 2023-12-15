from core.database import session_maker
from core.database.models import Service
from core.misc import str2int
from datetime import datetime


async def add_client_service(client_id: int | str, title: str) -> Service:
    """ Adds a new client's service and returns it """

    client_id, = str2int(client_id)

    async with session_maker() as session:
        service = Service(title=title, date=datetime.utcnow(), client_id=client_id)
        session.add(service)

        await session.commit()
        await session.refresh(service)

        return service
