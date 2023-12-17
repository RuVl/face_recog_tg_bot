import logging
from datetime import datetime
from pathlib import Path

import face_recognition
import numpy as np
from PIL import Image
from sqlalchemy import select

from core.config import LOCATION_MODEL_NAME, ENCODING_MODEL_NAME, TOLERANCE
from core.database import session_maker
from core.database.methods.client import get_all_clients
from core.database.models import Location, Client, Visit
from core.misc import str2int

register_heif_opener()

ImageFile.LOAD_TRUNCATED_IMAGES = True


async def find_faces(image_path: Path) -> Client | np.ndarray | None:
    """ Validate image and find face on it """

    # Prepare and recognize faces on image
    image = face_recognition.load_image_file(image_path)

    # Check if image can be sent to telegram
    w, h, _ = image.shape
    if max(w, h) / min(w, h) > 20:
        logging.warning(f"Face do not matches to telegram standard: {image_path}")

    face_locations = face_recognition.face_locations(image, model=LOCATION_MODEL_NAME)

    # Faces not found
    if len(face_locations) == 0:
        logging.error(f"Face not found: {image_path}")
        return

    # Found more than one face
    if len(face_locations) > 1:
        logging.error(f"Found more than one face: {image_path}")
        return

    # Get face encodings
    face_encodings = face_recognition.face_encodings(image, face_locations, model=ENCODING_MODEL_NAME)

    # Get known faces encoding
    clients = await get_all_clients()
    known_faces = [client.face_encoding for client in clients]

    # Compare encodings
    results = face_recognition.compare_faces(known_faces, face_encodings[0], tolerance=TOLERANCE)

    # Extract matches
    indexes = np.nonzero(results)[0]  # axe=0
    if len(indexes) == 0:  # Clients with this face aren't found.
        return face_encodings[0]  # Return face encoding

    # Found more than one matches
    if len(indexes) > 1:
        logging.warning(f"Found {len(indexes)} face matches: {image_path}")
        return

    return clients[indexes[0]]  # Return matched client


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
