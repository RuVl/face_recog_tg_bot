import logging
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp.web_exceptions import HTTPException

from core.image_hosting.config import API_URL
from core.image_hosting.utils import parse_response, store_image
from core.env import ImHostKeys


async def send_image(path: str | Path, dir2copy: str | Path, base_name: str = None) -> tuple[dict[str, Any], Path]:
	""" Send an image to the photo hosting server. """

	new_path = store_image(path, dir2copy, base_name)

	params = dict(key=ImHostKeys.API_TOKEN)
	post_data = aiohttp.FormData()

	logging.info(f"Sending image {path} to photo hosting")
	async with aiohttp.ClientSession() as session:
		with open(new_path, 'rb') as f:
			post_data.add_field('image', f)

			# Do not close file before send request
			async with session.post(API_URL, data=post_data, params=params) as response:
				if response.status == 200:
					resp = await response.json()
				else:
					raise HTTPException(text="Can't post image!")

	return parse_response(resp), new_path
