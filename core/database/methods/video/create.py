from pathlib import Path

from core.config import MEDIA_DIR
from core.database import session_maker
from core.database.models import Video
from core.misc.adapters import str2int


async def create_video_from_path(path: str | Path, visit_id: int | str = None) -> Video:
    """ Load the path to photo hosting and create an image entry """

    visit_id, = str2int(visit_id)

    if isinstance(path, Path):
        path = str(path)

    raise NotImplementedError()

    # data, new_path = await send_image(path, MEDIA_DIR)
    # url = data.get('url')

    # async with session_maker() as session:
    #     video = Video(path=str(new_path.absolute()), visit_id=visit_id)
    #
    #     if data and url:
    #         video.cloud_data = data
    #         video.url = url
    #
    #     session.add(video)
    #     await session.commit()
    #
    #     await session.refresh(video)
    #     return video
