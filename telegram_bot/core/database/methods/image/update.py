from sqlalchemy import update

from core.database import session_maker
from core.database.models import Image
from core.misc.adapters import str2int


async def set_visit2image(image_id: int | str, visit_id: int | str):
	""" Set Image.visit_id to an image """

	image_id, visit_id = str2int(image_id, visit_id)

	async with session_maker() as session:
		query = update(Image).where(Image.id == image_id).values(visit_id=visit_id)
		await session.execute(query)
		await session.commit()
