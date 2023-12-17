import logging
from typing import Any

import aiohttp
from pathlib import Path

from aiohttp.web_exceptions import HTTPException

from core.image_hosting.config import API_URL
from core.image_hosting.utils import prepare_path, parse_response
from core.misc.env import ImHostKeys


async def send_image(path: str | Path) -> dict[str, Any]:
    """ Send an image to the photo hosting server.  """

    path = prepare_path(path)

    params = dict(key=ImHostKeys.API_TOKEN)
    post_data = aiohttp.FormData()

    logging.info(f"Sending image {path} to photo hosting")
    async with aiohttp.ClientSession() as session:
        with open(path, 'rb') as f:
            post_data.add_field('image', f)

            # Do not close file before send request
            async with session.post(API_URL, data=post_data, params=params) as response:
                if response.status == 200:
                    resp = await response.json()
                else:
                    raise HTTPException(text="Can't post image!")

    return parse_response(resp)


async def send_images(paths: list[str | Path]) -> list[dict[str, Any]]:
    """ Send some images to the photo hosting server """

    paths = list(prepare_path(path) for path in paths)
    params = dict(key=ImHostKeys.API_TOKEN)

    results = []

    async with aiohttp.ClientSession() as session:
        for path in paths:
            post_data = aiohttp.FormData()

            with open(path, 'rb') as f:
                post_data.add_field('image', f)

                async with session.post(API_URL, data=post_data, params=params) as response:
                    if response.status == 200:
                        resp = await response.json()
                    else:
                        raise HTTPException(text="Can't post image!")

            results.append(parse_response(resp))

    return results
