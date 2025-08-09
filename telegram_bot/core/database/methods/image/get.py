from sqlalchemy import select

from core.database import session_maker
from core.database.models import Image, Visit, Client
from core.misc.adapters import str2int


async def get_image_by_id(id_: int | str) -> Image:
	""" Returns the image by given id """

	id_, = str2int(id_)

	async with session_maker() as session:
		query = select(Image).where(Image.id == id_)
		return await session.scalar(query)


async def get_client_images(client_id: int | str, limit: int = None) -> list[Image]:
	""" Возвращает все изображения клиента """

	client_id, = str2int(client_id)

	async with session_maker() as session:
		query = (select(Image)
		         .outerjoin(Visit, Image.visit_id == Visit.id)
		         .outerjoin(Client, Image.id == Client.profile_picture_id)
		         .where((Visit.client_id == client_id) | (Client.id == client_id)))

		if limit is not None:
			query.limit(limit)

		result = await session.scalars(query)
		return result.all()
