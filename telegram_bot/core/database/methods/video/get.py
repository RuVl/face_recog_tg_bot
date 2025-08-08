from sqlalchemy import select

from core.database import session_maker
from core.database.models import Video, Visit
from core.misc.adapters import str2int


async def get_client_videos(client_id: int | str, limit: int = None) -> list[Video]:
	""" Возвращает все видео клиента """

	client_id, = str2int(client_id)

	async with session_maker() as session:
		query = (select(Video)
		         .outerjoin(Visit, Video.visit_id == Visit.id)
		         .where(Visit.client_id == client_id))

		if limit is not None:
			query.limit(limit)

		result = await session.scalars(query)
		return result.all()
