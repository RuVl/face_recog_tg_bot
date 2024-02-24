import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import types

from core.cancel_token import CancellationToken
from core.database import models


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
                "_type": f'aiogram.{_type}',
                "_value": o.__dict__
            }
        elif isinstance(o, datetime):
            return {
                "_type": "datetime.datetime",
                "_value": o.isoformat()
            }
        elif isinstance(o, CancellationToken):
            return {
                "_type": "CancellationToken",
                "_value": o.__dict__
            }
        elif (_type := type(o).__name__) in models.__all__:
            return {
                "_type": f'models.{_type}',
                "_value": o.__dict__
            }

        return super().default(o)
