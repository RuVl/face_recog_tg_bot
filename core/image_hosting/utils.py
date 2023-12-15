import json
from pathlib import Path
from typing import Any


def prepare_path(path: str | Path) -> Path:
    """ Check if the path is valid and exists """

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError()

    return path


def parse_response(response: dict) -> dict[str, Any]:
    return response.get('data')
