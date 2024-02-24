import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import types

from core.cancel_token import CancellationToken
from core.database.models import Client


class TGEncoder(json.JSONEncoder):
    """ Write encoder for all you need in state.set_data """

    def default(self, o: Any) -> Any:
        if isinstance(o, Path):
            return {
                "_type": "pathlib.Path",
                "_value": str(o.absolute())
            }

        elif (_type := type(o).__name__) in types.__all__:
            return {
                "_type": _type,
                "_value": o.__dict__
            }

        elif isinstance(o, datetime):
            return {
                "_type": "datetime.datetime",
                "_value": o.isoformat()
            }

        # elif isinstance(o, types.Message):
        #     return {
        #         "_type": "aiogram.Message",
        #         "_value": o.__dict__
        #     }

        elif isinstance(o, CancellationToken):
            return {
                "_type": "CancellationToken",
                "_value": o.__dict__
            }

        elif isinstance(o, Client):
            return {
                "_type": "models.Client",
                "_value": o.__dict__
            }

        return super().default(o)
