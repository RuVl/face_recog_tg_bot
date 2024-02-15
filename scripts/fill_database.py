import json
import shutil
from datetime import datetime
from pathlib import Path

from core.config import SUPPORTED_IMAGE_TYPES, MEDIA_DIR
from core.database.methods.client import create_client
from core.database.methods.service import create_visit_service
from core.database.models import Client
from . import FOLDERS_INFO, get_or_create_location_address, find_faces, create_visit_with_date, get_date_taken
from .logger import rootLogger


async def fill_database():
    start_time = datetime.now()

    for folder_info in FOLDERS_INFO:
        folder = Path(folder_info.get('folder'))

        if not folder.exists() or not folder.is_dir():
            rootLogger.error(f"Wrong folder: {folder_info.get('folder')} in FOLDERS_INFO!")
            continue

        rootLogger.info(f"Working with folder: {folder}")

        processed_file = folder / 'processed.json'
        if not processed_file.exists():
            processed_file.write_text('{}')
        else:
            rootLogger.info(f'Found processed file!')

        with processed_file.open('r', encoding='utf-8') as f:
            processed: dict[str, str] = json.load(f)  # [img_path] = 'status'

        try:
            location = await get_or_create_location_address(folder_info.get('location_address'))

            service_title = folder_info.get('service_title')
            if service_title is None:
                rootLogger.error(f"Service title cannot be empty!")
                continue

            last_num = 1
            for img_type in SUPPORTED_IMAGE_TYPES.values():
                for i, img_path in enumerate(folder.glob(f'*{img_type}')):
                    i_path = str(img_path)

                    if i % 100 == 0:
                        rootLogger.info(f'Processed {i} images in folder: {folder}. Dump data...')
                        with processed_file.open('w', encoding='utf-8') as f:
                            json.dump(processed, f, ensure_ascii=True, indent=4)

                    if processed.get(i_path) is not None:
                        continue

                    rootLogger.info(f'Processing image: {img_path}')

                    result = await find_faces(img_path)
                    if isinstance(result, str):
                        processed[i_path] = result
                        continue

                    if isinstance(result, Client):
                        processed[i_path] = 'face exists'
                        rootLogger.warning(f"Found face match: {img_path}")
                        continue

                    rootLogger.info(f'Copy image to media directory: {img_path}')

                    save_path = MEDIA_DIR / f'{last_num}{img_path.suffix.lower()}'
                    while save_path.exists():
                        last_num += 1
                        save_path = MEDIA_DIR / f'{last_num}{img_path.suffix.lower()}'

                    last_num += 1

                    face_path = shutil.copy2(img_path, save_path)

                    date = get_date_taken(img_path)
                    if date is None:
                        date = datetime.utcnow()

                    client = await create_client(face_path, result)
                    visit = await create_visit_with_date(client.id, location.id, date)
                    await create_visit_service(visit.id, service_title)

                    rootLogger.info(f'Created client ({client.id}) with: {face_path}')
                    processed[i_path] = 'success'
        finally:
            with processed_file.open('w', encoding='utf-8') as f:
                json.dump(processed, f, ensure_ascii=True, indent=4)

    rootLogger.info(f'Processed in {(datetime.now() - start_time).seconds} sec')
