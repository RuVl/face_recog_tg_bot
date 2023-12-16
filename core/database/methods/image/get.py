from sqlalchemy import select, and_

from core.database import session_maker
from core.database.models import Image, Visit
from core.misc import str2int


async def get_image_by_id(id_: int | str) -> Image:
    """ Returns the image by given id """

    id_, = str2int(id_)

    async with session_maker() as session:
        query = select(Image).where(Image.id == id_)
        return await session.scalar(query)


async def get_client_images(client_id: int | str) -> list[Image]:
    """ Returns all client's images """

    client_id, = str2int(client_id)

    async with session_maker() as session:
        query = select(Image).where(and_(Image.visit_id == Visit.id, Visit.client_id == client_id))
        result = await session.scalars(query)
        return result.all()
