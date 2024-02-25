import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import types

from core import bot
from core.cancel_token import CancellationToken
from core.database import models


class TGDecoder(json.JSONDecoder):
    """ Write decoder for all you need in state.get_data """

    def __init__(self, *args, **kwargs):
        super(TGDecoder, self).__init__(object_hook=self.object_hook, *args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def object_hook(self, o: dict[str, Any]) -> Any:
        if '_type' not in o:
            return o

        match o['_type']:
            case 'pathlib.Path':
                return Path(o['_value'])
            case _type if _type.startswith('aiogram.') and _type[8:] in types.__all__:
                class_ = getattr(types, _type[8:])
                o = class_(**o['_value'])
                o._bot = bot
                return o
            case 'datetime.datetime':
                return datetime.fromisoformat(o['_value'])
            case 'CancellationToken':
                return CancellationToken(**o['_value'])
            case _type if _type.startswith('models.') and _type[7:] in models.__all__:
                class_ = getattr(models, _type[7:])
                return class_(**o['_value'])
            case _:
                return o
