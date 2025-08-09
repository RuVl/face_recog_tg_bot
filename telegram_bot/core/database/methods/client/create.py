from pathlib import Path

from core.database import session_maker
from core.database.methods.image import create_image_from_path
from core.database.models import Client


async def create_client(temp_face_image_path: str | Path, face_encoding: dict) -> Client:
	""" Create a new client with the provided image path and encoding """

	profile_photo = await create_image_from_path(temp_face_image_path)

	async with session_maker() as session:
		client = Client(face_encoding=face_encoding, profile_picture=profile_photo)

		session.add(client)
		await session.commit()

		await session.refresh(client)
		return client
