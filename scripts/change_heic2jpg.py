from pathlib import Path

from PIL import Image, ImageFile
from pillow_heif import register_heif_opener
from sqlalchemy import select
from tqdm import tqdm

from core.config import MEDIA_DIR
from core.database import session_maker, models
from core.misc.utils import get_available_filepath

ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()


async def change_heic2jpg():
    async with session_maker() as session:
        query = select(models.Image).where(models.Image.path.endswith('.heic'))
        result = await session.scalars(query)

        old_paths = []
        new_paths = []

        try:
            for image in tqdm(result.all()):
                path = Path(image.path)
                new_path = get_available_filepath(MEDIA_DIR, path.stem, '.jpg')

                img = Image.open(path)
                img.save(new_path)
                img.close()

                image.path = str(new_path.absolute())

                old_paths.append(path)
                new_paths.append(new_path)

            await session.commit()
        except Exception as e:
            for p in new_paths:
                p.unlink(missing_ok=True)

            raise e

        for p in old_paths:
            p.unlink(missing_ok=True)
