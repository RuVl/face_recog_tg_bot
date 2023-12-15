from sqlalchemy import update

from core.database import session_maker
from core.database.models import Visit
from core.misc import str2int


async def update_visit_name(visit_id: int | str, name: str) -> None:
    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        query = update(Visit).where(Visit.id == visit_id).values(name=name)
        await session.execute(query)
        await session.commit()


async def update_visit_contacts(visit_id: int | str, contacts: str) -> None:
    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        query = update(Visit).where(Visit.id == visit_id).values(contacts=contacts)
        await session.execute(query)
        await session.commit()
