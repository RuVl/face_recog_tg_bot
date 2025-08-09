from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, relationship

from core.database.models import Base


class Video(Base):
	"""
		Таблица видео, загруженных в облачное хранилище.
		:param path: Локальный путь к видео
		:param url: Публичная ссылка на видео в облачном хранилище
		:param cloud_data: Информация о загрузке в облачное хранилище
		:param visit_id: Foreign key to Visit.
	"""

	__tablename__ = 'videos'

	id: Mapped[int] = Column(Integer, primary_key=True)

	path: Mapped[str] = Column(String(255), nullable=False)

	url: Mapped[str] = Column(String(255), nullable=True)
	cloud_data: Mapped[dict] = Column(JSON, nullable=True)

	visit_id: Mapped[int] = Column(ForeignKey('visits.id', ondelete='SET NULL'), nullable=False)
	visit: Mapped['Visit'] = relationship('Visit', back_populates='videos', passive_deletes=True)
