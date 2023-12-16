from typing import TYPE_CHECKING

from sqlalchemy import Column, JSON, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from core.database.models import Base

if TYPE_CHECKING:
    from . import Visit


class Image(Base):
    """
        Таблица изображений с фото хостинга. (Связывается с Client по Client.id)
        :param path: Путь к изображению локально
        :param url: Ссылка на изображение на фото хостинге
        :param hosting_data: Информация об изображении при загрузке на фото хостинг
        :param visit_id: Foreign key to Visit. Its null when image is client.profile_picture
    """

    __tablename__ = 'images'

    id: Mapped[int] = Column(Integer, primary_key=True)

    path: Mapped[str] = Column(String(255), nullable=True)

    url: Mapped[str] = Column(String(255), nullable=True)
    hosting_data: Mapped[dict] = Column(JSON, nullable=True)

    visit_id: Mapped[int] = Column(ForeignKey('visits.id'), nullable=True)
    visit: Mapped['Visit'] = relationship('Visit', back_populates='images')
