from pathlib import Path
import shutil
from typing import Any

from PIL import Image, ImageFile
from pillow_heif import register_heif_opener

from core.misc.utils import get_available_filepath, prepare_path

ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()


def store_image(path: str | Path, dir2copy: str | Path, base_name: str = None) -> Path:
	""" Copy image to media folder """

	path = prepare_path(path)

	if base_name is None:
		base_name = path.stem[-5:]

	new_path = get_available_filepath(dir2copy, base_name, '.jpg')

	# Copy image to media folder
	if path.suffix != '.jpg':
		img = Image.open(path)
		img.save(new_path)
		img.close()
		path.unlink(missing_ok=True)
	else:
		shutil.move(path, new_path, shutil.copy2)

	return new_path


def parse_response(response: dict) -> dict[str, Any]:
	return response.get('data')
