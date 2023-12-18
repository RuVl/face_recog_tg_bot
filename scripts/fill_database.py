import logging
import shutil
from datetime import datetime
from pathlib import Path

from core.config import SUPPORTED_IMAGE_TYPES, MEDIA_DIR
from core.database.methods.client import create_client
from core.database.methods.service import create_visit_service
from core.database.models import Client
from . import FOLDERS_INFO, get_or_create_location_address, find_faces, create_visit_with_date, get_date_taken


async def fill_database():
    start_time = datetime.now()

    for folder_info in FOLDERS_INFO:
        folder = Path(folder_info.get('folder'))

        if not folder.exists() or not folder.is_dir():
            logging.error(f"Wrong folder: {folder_info.get('folder')} in FOLDERS_INFO!")
            continue

        logging.info(f"Working with folder: {folder}")

        location = await get_or_create_location_address(folder_info.get('location_address'))

        service_title = folder_info.get('service_title')
        if service_title is None:
            logging.error(f"Service title cannot be empty!")
            continue

        for img_type in SUPPORTED_IMAGE_TYPES.values():
            for img_path in folder.glob(f'*{img_type}'):
                logging.info(f'Processing image: {img_path}')

                result = await find_faces(img_path)
                if result is None:
                    logging.info(f"No result for: {img_path}")
                    continue

                if isinstance(result, Client):
                    logging.warning(f"Found face match: {img_path}")
                    continue

                logging.info(f'Copy image to media directory: {img_path}')
                face_path = shutil.copy2(img_path, MEDIA_DIR)

                logging.info(f'Create client with: {face_path}')

                date = get_date_taken(img_path)
                if date is None:
                    date = datetime.utcnow()

                client = await create_client(face_path, result)
                visit = await create_visit_with_date(client.id, location.id, date)
                await create_visit_service(visit.id, service_title)

    logging.info(f'Обработано за {(datetime.now() - start_time).seconds} sec')
