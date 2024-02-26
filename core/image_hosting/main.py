import logging
import shutil
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp.web_exceptions import HTTPException

from core.image_hosting.config import API_URL
from core.image_hosting.utils import prepare_path, parse_response, get_available_filepath
from core.misc.env import ImHostKeys


async def send_image(path: str | Path, dir2copy: str | Path, base_name: str = None) -> dict[str, Any]:
    """ Send an image to the photo hosting server.  """

    if base_name is None:
        base_name = path.stem[-5:]

    path = prepare_path(path)
    new_path = get_available_filepath(dir2copy, base_name, path.suffix)

    shutil.copy2(path, new_path)

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

    return parse_response(resp)
