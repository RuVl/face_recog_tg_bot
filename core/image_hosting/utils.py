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


def get_available_filepath(directory: Path | str, base_name: str, extension: str):
    extension = extension.removeprefix('.')
    directory = Path(directory)

    filename = f'{base_name}.{extension}'
    if not (directory / filename).exists():
        return directory / filename

    index = 0
    while True:
        filename = f"{base_name}{index}.{extension}"
        if not (directory / filename).exists():
            return directory / filename
        index += 1
