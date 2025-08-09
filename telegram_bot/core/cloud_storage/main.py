import logging
import shutil
import traceback
from pathlib import Path

import yadisk
from yadisk.exceptions import YaDiskError
from yadisk.objects import AsyncResourceObject

from core.cloud_storage.config import CLOUD_FOLDER
from core.env import CloudStorageKeys
from core.misc.utils import prepare_path, get_available_filepath


async def upload_file(file_path: str | Path, dir2copy: str | Path, base_name: str = None) -> tuple[AsyncResourceObject, Path]:
	""" Send a file to the cloud storage """

	file_path = prepare_path(file_path)

	if base_name is None:
		base_name = file_path.stem[-5:]

	new_path = get_available_filepath(dir2copy, base_name, file_path.suffix)
	shutil.move(file_path, new_path, shutil.copy2)

	logging.info(f"Sending file {new_path} to cloud storage")
	async with yadisk.AsyncClient(token=CloudStorageKeys.API_TOKEN, session='aiohttp') as client:
		if not await client.exists(CLOUD_FOLDER):
			await client.mkdir(CLOUD_FOLDER)

		upload_path = f'{CLOUD_FOLDER}/{new_path.stem}'

		i = 1
		while await client.exists(upload_path):
			upload_path = f'{CLOUD_FOLDER}/{new_path.stem}_{i}'

		try:
			await client.upload(str(new_path.absolute()), upload_path)
		except YaDiskError:
			logging.error(traceback.format_exc())

			if not await client.exists(upload_path):
				return None, new_path

		cloud_link_obj = await client.move(upload_path, upload_path + file_path.suffix)
		cloud_link_obj = await cloud_link_obj.publish()

		cloud_obj = await cloud_link_obj.get_meta()
		return cloud_obj, new_path
