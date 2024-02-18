from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile
from deepface import DeepFace
from pillow_heif import register_heif_opener
from sqlalchemy import select

from core.config import BACKEND, MODEL
from core.database import session_maker
from core.database.methods.client import get_all_clients
from core.database.models import Location, Visit, Client
from core.face_recognition.main import compare_faces
from core.misc import str2int
from scripts.logger import rootLogger

register_heif_opener()

ImageFile.LOAD_TRUNCATED_IMAGES = True


async def find_faces(image_path: Path) -> tuple[list[Client] | None, dict | None]:
    embeddings = DeepFace.represent(str(image_path), model_name=MODEL, detector_backend=BACKEND, enforce_detection=False)

    if len(embeddings) > 1:
        rootLogger.error(f'Found {len(embeddings)} faces on {image_path}')
        return None, None

    if len(embeddings) == 0:
        rootLogger.error(f'No faces found on {image_path}')
        return None, None

    face = embeddings[0]

    # Get known faces encoding
    clients = await get_all_clients()
    known_faces = [client.face_encoding for client in clients]

    # Compare with known faces
    results = compare_faces(known_faces, face)

    # Extract matches
    indexes = np.nonzero(results)[0]  # axe=0

    # Clients with this face aren't found.
    if len(indexes) == 0:
        return None, face  # Return only face encoding

    return [clients[i] for i in indexes], face  # Return an array of clients and face encoding


async def get_or_create_location_address(address: str) -> Location:
    async with session_maker() as session:
        query = select(Location).where(Location.address == address)
        result = await session.scalar(query)

        if result is not None:
            return result

        location = Location(address=address)
        session.add(location)

        await session.commit()
        await session.refresh(location)

        return location


async def create_visit_with_date(client_id: int | str, location_id: int | str, date: datetime) -> Visit:
    """ Create a new visit of a client with user location and returns it """

    client_id, location_id = str2int(client_id, location_id)

    async with session_maker() as session:
        visit = Visit(client_id=client_id, date=date, location_id=location_id)

        session.add(visit)
        await session.commit()

        await session.refresh(visit)
        return visit


def get_date_taken(path) -> datetime | None:
    im = Image.open(path)
    exif = im.getexif()

    if not exif:
        return None

    date_str = exif.get(36867)
    if date_str is None:
        return None

    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
