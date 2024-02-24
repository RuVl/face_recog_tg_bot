import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import types

from core import bot
from core.cancel_token import CancellationToken
from core.database.models import Client


class TGDecoder(json.JSONDecoder):
    """ Write decoder for all you need in state.get_data """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def object_hook(self, o: dict[str, Any]) -> Any:
        if '_type' not in o:
            return o

        match o['_type']:
            case 'pathlib.Path':
                return Path(o['_value'])
            case _type if _type in types.__all__:
                class_ = getattr(types, _type)
                return class_(**o['_value'], _bot=bot)
            case 'datetime.datetime':
                return datetime.fromisoformat(o['_value'])
            case 'CancellationToken':
                return CancellationToken(**o['_value'])
            case 'models.Client':
                return Client(**o['_value'])
            case _:
                return o
