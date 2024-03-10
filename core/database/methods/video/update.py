from sqlalchemy import update

from core.database import session_maker
from core.database.models import Video
from core.misc.adapters import str2int


async def update_video_fields(video_id: str | int, **kwargs):
    """ Update the video's cloud_data, url or path """

    video_id, = str2int(video_id)

    values = {
        k: v
        for k, v in kwargs.items()
        if k in ['cloud_data', 'url', 'path'] and v is not None
    }

    if len(values) == 0:
        return

    async with session_maker() as session:
        query = update(Video).where(Video.id == video_id).values(**values)
        await session.execute(query)
        await session.commit()
