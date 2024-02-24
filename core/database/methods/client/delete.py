from sqlalchemy import delete

from core.database import session_maker
from core.database.models import Client
from core.misc import str2int


async def delete_client(client_id: str | int) -> Client:
    """ Delete the client by client_id """

    client_id, = str2int(client_id)

    async with session_maker() as session:
        query = delete(Client).where(Client.id == client_id)
        await session.execute(query)
        await session.commit()
