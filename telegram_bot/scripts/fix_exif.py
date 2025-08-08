import logging

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from tqdm import tqdm

from core.database import session_maker
from core.database.models import *
from scripts import get_date_taken


async def fix_exif():
	async with session_maker() as session:
		visits_query = select(Visit).options(joinedload(Visit.client))
		visits = (await session.scalars(visits_query)).all()

		for visit in tqdm(visits):
			client = visit.client
			image = client.profile_picture

			dt = get_date_taken(image.path)
			if dt is None:
				logging.warning(f'Client ({client.id}) image ({image.id}) {image.path} has no date in exif!')
				continue

			if dt < visit.date:
				logging.info(f'Set visit ({visit.id}) date to {dt}')
				visit.date = dt
			else:
				logging.info(f'Current visit ({visit.id}) date is lower than {dt}')

		logging.info('Save all changes...')
		await session.commit()
