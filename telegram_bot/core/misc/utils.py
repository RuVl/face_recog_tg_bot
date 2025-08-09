import json
from datetime import timedelta
from pathlib import Path

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio import Redis

from core.json_classes import TGEncoder, TGDecoder
from core.env import RedisKeys


def get_storage(*,
                state_ttl: timedelta | int | None = None,
                data_ttl: timedelta | int | None = None,
                key_builder_prefix: str = 'fsm',
                key_builder_separator: str = ':',
                key_builder_with_bot_id: bool = False,
                key_builder_with_destiny: bool = False,
                ) -> BaseStorage:
	return RedisStorage(
		Redis.from_url(RedisKeys.URL),
		key_builder=DefaultKeyBuilder(
			prefix=key_builder_prefix,
			separator=key_builder_separator,
			with_bot_id=key_builder_with_bot_id,
			with_destiny=key_builder_with_destiny
		),
		state_ttl=state_ttl,
		data_ttl=data_ttl,
		json_dumps=lambda data: json.dumps(data, cls=TGEncoder),
		json_loads=lambda data: json.loads(data, cls=TGDecoder)
	)


def get_available_filepath(directory: Path | str, base_name: str, extension: str) -> Path:
	extension = extension.removeprefix('.')
	directory = Path(directory)

	if not directory.exists():
		directory.mkdir(exist_ok=True)

	filename = f'{base_name}.{extension}'
	if not (directory / filename).exists():
		return directory / filename

	index = 0
	while True:
		filename = f"{base_name}{index}.{extension}"
		if not (directory / filename).exists():
			return directory / filename
		index += 1


def prepare_path(path: str | Path) -> Path:
	""" Check if the path is valid and exists """

	if isinstance(path, str):
		path = Path(path)

	if not path.exists():
		raise FileNotFoundError()

	return path
