from core.database import session_maker
from core.database.models import Service
from core.misc import str2int
from datetime import datetime


async def create_visit_service(visit_id: int | str, title: str) -> Service:
    """ Adds a new client's service and returns it """

    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        service = Service(title=title, date=datetime.utcnow(), visit_id=visit_id)
        session.add(service)

        await session.commit()
        await session.refresh(service)

        return service
