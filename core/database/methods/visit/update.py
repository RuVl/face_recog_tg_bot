import phonenumbers
from phonenumbers import PhoneNumber
from sqlalchemy import update

from core.database import session_maker
from core.database.models import Visit
from core.misc.adapters import str2int


async def update_visit_name(visit_id: int | str, name: str) -> None:
    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        query = update(Visit).where(Visit.id == visit_id).values(name=name)
        await session.execute(query)
        await session.commit()


async def update_visit_social_media(visit_id: int | str, social_media: str) -> None:
    visit_id, = str2int(visit_id)

    async with session_maker() as session:
        query = update(Visit).where(Visit.id == visit_id).values(social_media=social_media)
        await session.execute(query)
        await session.commit()


async def update_visit_phone_number(visit_id: int | str, phone_number: PhoneNumber) -> None:
    visit_id, = str2int(visit_id)
    phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)

    async with session_maker() as session:
        query = update(Visit).where(Visit.id == visit_id).values(phone_number=phone)

        await session.execute(query)
        await session.commit()
