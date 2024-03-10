import logging
import shutil
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp.web_exceptions import HTTPException

from core.image_hosting.config import API_URL
from core.image_hosting.utils import parse_response
from core.misc import ImHostKeys
from core.misc.utils import get_available_filepath, prepare_path


async def send_image(path: str | Path, dir2copy: str | Path, base_name: str = None) -> tuple[dict[str, Any], Path]:
    """ Send an image to the photo hosting server. """

    path = prepare_path(path)

    if base_name is None:
        base_name = path.stem[-5:]

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

    return parse_response(resp), new_path
