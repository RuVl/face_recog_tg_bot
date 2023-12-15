from pathlib import Path

from core.database import session_maker
from core.database.models import Image
from core.image_hosting import send_image
from core.misc import str2int


async def create_image_from_path(path: str | Path, client_id: int | str = None) -> Image:
    """ Load the path to photo hosting and create an image entry """

    data = await send_image(path)
    url = data.get('url')

    if isinstance(path, Path):
        path = str(path)

    async with session_maker() as session:
        image = Image(path=path, url=url, hosting_data=data)

        if client_id is not None:
            client_id, = str2int(client_id)
            image.client_id = client_id

        session.add(image)
        await session.commit()

        await session.refresh(image)
        return image
