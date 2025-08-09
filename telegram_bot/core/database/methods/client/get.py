import phonenumbers
from phonenumbers import PhoneNumber
from sqlalchemy import select, exists
from sqlalchemy.orm import joinedload

from core.database import session_maker
from core.database.models import Client, Visit
from core.misc.adapters import str2int


async def get_all_clients() -> list[Client]:
	async with session_maker() as session:
		query = select(Client)
		result = await session.scalars(query)
		return result.all()


async def get_client(client_id: int | str, with_profile_image=False) -> Client | None:
	client_id, = str2int(client_id)

	async with session_maker() as session:
		query = select(Client).where(Client.id == client_id)
		if with_profile_image:
			query.options(joinedload(Client.profile_picture))

		return await session.scalar(query)


async def get_client_by_phone(phone_number: PhoneNumber, with_profile_image=False) -> Client | None:
	phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)

	async with session_maker() as session:
		query = (select(Client)
		         .join(Visit, Client.id == Visit.client_id)
		         .where(Visit.phone_number == phone))

		if with_profile_image:
			query.options(joinedload(Client.profile_picture))

		return await session.scalar(query)


async def load_clients_profile_images(clients: list[Client]) -> list[Client]:
	""" Returns a list of clients with profile image """

	clients_id = [client.id for client in clients]

	async with session_maker() as session:
		query = select(Client).where(Client.id.in_(clients_id)).options(joinedload(Client.profile_picture))
		result = await session.scalars(query)
		return result.all()


async def client_have_visit(client_id: int | str) -> bool:
	client_id, = str2int(client_id)

	async with session_maker() as session:
		query = exists(Client.visits).where(Client.id == client_id).select()
		return await session.scalar(query)
