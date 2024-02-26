from pathlib import Path

from core.config import MEDIA_DIR
from core.database import session_maker
from core.database.models import Image
from core.image_hosting import send_image
from core.misc import str2int


async def create_image_from_path(path: str | Path, visit_id: int | str = None) -> Image:
    """ Load the path to photo hosting and create an image entry """

    if isinstance(path, Path):
        path = str(path)

    data, new_path = await send_image(path, MEDIA_DIR)
    url = data.get('url')

    async with session_maker() as session:
        image = Image(path=new_path, url=url, hosting_data=data)

        if visit_id is not None:
            visit_id, = str2int(visit_id)
            image.visit_id = visit_id

        session.add(image)
        await session.commit()

        await session.refresh(image)
        return image
