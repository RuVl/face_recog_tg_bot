from os import environ
from pathlib import Path
from typing import Final


class TgKeys:
	TOKEN: Final[str] = environ.get('TG_API_TOKEN')
	ADMIN_GROUP_ID: Final[int] = int(environ.get('ADMIN_GROUP_ID'))
	MEDIA_DIR: Final[Path] = Path(environ.get('MEDIA_DIR'))


class RecognizerKeys:
	HOST: Final[str] = environ.get('RECOGNIZER_HOST')
	PORT: Final[int] = environ.get('RECOGNIZER_PORT')

	URL: Final[str] = f'{HOST}:{PORT}'


class PostgresKeys:
	HOST: Final[str] = environ.get('POSTGRES_HOST', default='localhost')
	PORT: Final[str] = environ.get('POSTGRES_PORT', default='5432')

	USER: Final[str] = environ.get('POSTGRES_USER', default='postgres')
	PASSWORD: Final[str] = environ.get('POSTGRES_PASSWORD', default='')

	DATABASE: Final[str] = environ.get('POSTGRES_DB', default=USER)

	URL: Final[str] = f'postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'


class RedisKeys:
	HOST: Final[str] = environ.get('REDIS_HOST', default='localhost')
	PORT: Final[str] = environ.get('REDIS_PORT', default='6379')

	DATABASE: Final[str] = environ.get('REDIS_DB', default='0')

	URL: Final[str] = f'redis://{HOST}:{PORT}/{DATABASE}'


class ImHostKeys:
	API_TOKEN: Final[str] = environ.get('IM_HOST_TOKEN')


class CloudStorageKeys:
	API_TOKEN: Final[str] = environ.get('CLOUD_STORAGE_TOKEN')
