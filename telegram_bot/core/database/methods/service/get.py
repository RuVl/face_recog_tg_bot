from sqlalchemy import select, and_

from core.database import session_maker
from core.database.models import Service, Visit
from core.misc.adapters import str2int


async def get_client_services(client_id: int | str) -> list[Service]:
	""" Returns a list of services by given client_id """
	client_id, = str2int(client_id)

	async with session_maker() as session:
		query = select(Service).where(and_(Service.visit_id == Visit.id, Visit.client_id == client_id))
		result = await session.scalars(query)
		return result.all()
