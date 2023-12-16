from sqlalchemy import exists

from core.database import session_maker
from core.database.models import Client
from core.misc import str2int


async def client_have_visit(client_id: int | str) -> bool:
    client_id, = str2int(client_id)

    async with session_maker() as session:
        query = exists(Client.visits).where(Client.id == client_id).select()
        return await session.scalar(query)
