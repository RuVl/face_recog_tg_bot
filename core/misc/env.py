from os import environ
from typing import Final

from dotenv import load_dotenv

load_dotenv()


class TgKeys:
    TOKEN: Final[str] = environ.get('TG_API_TOKEN')
    ADMIN_GROUP_ID: Final[int] = int(environ.get('ADMIN_GROUP_ID'))


class DBKeys:
    HOST: Final[str] = '127.0.0.1'
    PORT: Final[str] = '5432'

    USERNAME: Final[str] = environ.get('DB_USERNAME')
    PASSWORD: Final[str] = environ.get('DB_PASSWORD')
    DATABASE: Final[str] = environ.get('DB_DATABASE')

    connection_string = f'postgresql+asyncpg://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'


class ImHostKeys:
    API_TOKEN: Final[str] = environ.get('IM_HOST_TOKEN')
