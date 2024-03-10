import asyncio
import logging
from pathlib import Path

from core.cloud_storage import cut_url, upload_file
from core.config import MEDIA_DIR
from core.database import session_maker
from core.database.methods.video import update_video_fields
from core.database.models import Video
from core.misc.adapters import str2int


async def _send_video2cloud(video_id: str | int, path: str | Path):
    if isinstance(path, Path):
        path = str(path)

    logging.info(f'Uploading video for {video_id} record...')
    data, new_path = await upload_file(path, MEDIA_DIR)

    if not data:
        logging.warning('Cannot upload video!')
        return

    cloud_data = {
        'path': data.path,
        'href': data.href,
        'file': data.file,
        'type': data.type,
        'public_url': data.public_url,
        'public_key': data.public_key
    }

    logging.info(f"Cutting video's ({video_id}) public_url...")
    url = await cut_url(data.public_url)

    logging.info(f'Updating {video_id} record...')
    await update_video_fields(video_id, path=new_path, cloud_data=cloud_data, url=url)


async def create_video_from_path(path: str | Path, visit_id: int | str) -> Video:
    """ Load the path to photo hosting and create an image entry """

    visit_id, = str2int(visit_id)

    if isinstance(path, str):
        path = Path(path)

    async with session_maker() as session:
        video = Video(path=str(path.absolute()), visit_id=visit_id)
        session.add(video)

        await session.commit()
        await session.refresh(video)

        _ = asyncio.create_task(_send_video2cloud(video.id, path))
        return video
