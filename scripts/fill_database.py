import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from core.config import SUPPORTED_IMAGE_TYPES, MEDIA_DIR
from core.database.methods.client import create_client
from core.database.methods.service import create_visit_service
from . import FOLDERS_INFO, get_or_create_location_address, create_visit_with_date, get_date_taken, find_faces
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
            td = tempfile.TemporaryDirectory()

            location = await get_or_create_location_address(folder_info.get('location_address'))

            service_title = folder_info.get('service_title')
            if service_title is None:
                rootLogger.error(f"Service title cannot be empty!")
                continue

            last_num = 1
            for img_type in SUPPORTED_IMAGE_TYPES.values():
                for i, img_path in enumerate(folder.glob(f'*{img_type}')):
                    i_path = img_path.name  # dictionary's key for file processed.json
                    img_path_temp = shutil.copy2(str(img_path), td.name)

                    if i % 100 == 0:
                        rootLogger.info(f'Processed {i} images in folder: {folder}. Dump data...')
                        with processed_file.open('w', encoding='utf-8') as f:
                            json.dump(processed, f, ensure_ascii=True, indent=4)

                    if processed.get(i_path) is not None:
                        continue

                    rootLogger.info(f'Processing image: {img_path}')

                    clients, face = await find_faces(img_path_temp)
                    if face is None:
                        processed[i_path] = f'found 0 or >1 faces'
                        continue

                    if clients is not None:
                        clients_id = [client.id for client in clients]
                        rootLogger.warning(f'Face on {img_path} similar with: {clients_id}')
                        processed[i_path] = f'found {len(clients)} similar'
                        continue

                    rootLogger.info(f'Copy image to media directory: {img_path}')

                    save_path = MEDIA_DIR / f'{last_num}{img_path.suffix.lower()}'
                    while save_path.exists():
                        last_num += 1
                        save_path = MEDIA_DIR / f'{last_num}{img_path.suffix.lower()}'

                    last_num += 1

                    face_path = shutil.copy2(img_path, save_path)
                    date = get_date_taken(img_path) or datetime.utcnow()

                    client = await create_client(face_path, face)
                    visit = await create_visit_with_date(client.id, location.id, date)
                    await create_visit_service(visit.id, service_title)

                    rootLogger.info(f'Created client ({client.id}) with: {face_path}')
                    processed[i_path] = 'success'
        finally:
            td.cleanup()

            with processed_file.open('w', encoding='utf-8') as f:
                json.dump(processed, f, ensure_ascii=True, indent=4)

    rootLogger.info(f'Processed in {(datetime.now() - start_time).seconds} sec')
