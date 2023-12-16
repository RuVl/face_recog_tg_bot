from sqlalchemy import select

from core.database import session_maker
from core.database.models import Client
from core.misc import str2int


async def get_all_clients() -> list[Client]:
    async with session_maker() as session:
        query = select(Client)
        result = await session.scalars(query)
        return result.all()


async def get_client(client_id: int | str) -> Client:
    client_id, = str2int(client_id)

    async with session_maker() as session:
        query = select(Client).where(Client.id == client_id)
        return await session.scalar(query)
