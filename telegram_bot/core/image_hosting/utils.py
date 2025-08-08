from typing import Any


def parse_response(response: dict) -> dict[str, Any]:
	return response.get('data')
