import asyncio
import json
import logging
from pathlib import Path

from core.database.methods.client import create_client


async def main(results_path: Path, image_folder: Path) -> None:
	with results_path.open('r', encoding='utf-8') as f:
		results: dict[str, list] = json.load(f)

	for filename, faces in results.items():
		if len(faces) == 0:
			logging.warning(f'{filename} has no faces! Skipping...')
			continue
		elif len(faces) > 1:
			logging.warning(f'{filename} has {len(faces)} faces! Using first...')

		face = faces[0]

		img_path = image_folder / filename
		if not img_path.exists():
			logging.warning(f'{img_path} does not exist! Skipping...')
			continue

		client = await create_client(img_path, face)
		logging.info(f'Client created! Id: {client.id}')


if __name__ == '__main__':
	results_path = Path('results.json')
	img_folder = Path('db')

	asyncio.run(main(results_path, img_folder))
