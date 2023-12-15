from sqlalchemy import update

from core.database import session_maker
from core.database.models import Image
from core.misc import str2int


async def set_client2image(image_id: int | str, client_id: int | str):
    """ Set Image.client_id to an image """

    image_id, client_id = str2int(image_id, client_id)

    async with session_maker() as session:
        query = update(Image).where(Image.id == image_id).values(client_id=client_id)
        await session.execute(query)
        await session.commit()
