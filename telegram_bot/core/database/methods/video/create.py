import asyncio
from pathlib import Path

from core.database import session_maker
from core.database.methods.video.utils import _send_video2cloud
from core.database.models import Video
from core.misc.adapters import str2int


async def create_video_from_path(path: str | Path, visit_id: int | str) -> Video:
	""" Load the path to photo hosting and create an image entry """

	visit_id, = str2int(visit_id)

	if isinstance(path, str):
		path = Path(path)

	async with session_maker() as session:
		video = Video(path=str(path.absolute()), visit_id=visit_id)
		session.add(video)

		await session.commit()
		await session.refresh(video)

		_ = asyncio.create_task(_send_video2cloud(video.id, path))
		return video
