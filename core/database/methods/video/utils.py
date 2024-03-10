import logging
from pathlib import Path

from core.cloud_storage import upload_file, cut_url
from core.config import MEDIA_DIR
from core.database.methods.video import update_video_fields


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
