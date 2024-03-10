import logging
import traceback
from pathlib import Path

from core.cloud_storage import upload_file, cut_url
from core.config import MEDIA_DIR
from core.database.methods.video import update_video_fields


async def _send_video2cloud(video_id: str | int, path: str | Path):
    if isinstance(path, Path):
        path = str(path)

    logging.info(f'Uploading video for {video_id} record...')
    try:
        cloud_obj, new_path = await upload_file(path, MEDIA_DIR)

        if not cloud_obj:
            logging.warning('Cannot upload video!')
            return

        cloud_data = {
            'resource_id': cloud_obj.resource_id,
            'media_type': cloud_obj.media_type,
            'public_url': cloud_obj.public_url,
            'type': cloud_obj.type,
            'path': cloud_obj.path,
            'modified': cloud_obj.modified,
            'mime_type': cloud_obj.mime_type,
            'name': cloud_obj.name,
            'antivirus_status': cloud_obj.antivirus_status,
            'size': cloud_obj.size,
            'preview': cloud_obj.preview,
            'public_key': cloud_obj.public_key,
            'created': cloud_obj.created,
            'sha256': cloud_obj.sha256,
            'md5': cloud_obj.md5
        }
    except Exception:
        logging.error(traceback.format_exc())

    logging.info(f"Cutting video's ({video_id}) public_url...")
    url = await cut_url(cloud_obj.public_url)

    logging.info(f'Updating {video_id} record...')
    await update_video_fields(video_id, path=new_path, cloud_data=cloud_data, url=url)
