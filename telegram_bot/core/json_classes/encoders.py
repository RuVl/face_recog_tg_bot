import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import types
from sqlalchemy.orm import InstanceState

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
				"_value": {k: v for k, v in o.__dict__.items() if v is not None}
			}
		elif isinstance(o, datetime):
			return {
				"_type": "datetime.datetime",
				"_value": o.isoformat()
			}
		elif isinstance(o, CancellationToken):
			return {
				"_type": "CancellationToken",
				"_value": {k: v for k in o.__slots__ if (v := getattr(o, k)) is not None}
			}
		elif (_type := type(o).__name__) in models.__all__:
			_value = {k: v for k, v in o.__dict__.items() if v is not None}
			_value.pop('_sa_instance_state')
			return {
				"_type": f'models.{_type}',
				"_value": _value
			}
		elif isinstance(o, InstanceState):
			return None

		return super(TGEncoder, self).default(o)
