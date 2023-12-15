from typing import TYPE_CHECKING

from sqlalchemy import Column, JSON, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from core.database.models import Base

if TYPE_CHECKING:
    from . import Client


class Image(Base):
    """
        Таблица изображений с фото хостинга. (Связывается с Client по Client.id)
        :param path: Путь к изображению локально
        :param url: Ссылка на изображение на фото хостинге
        :param hosting_data: Информация об изображении при загрузке на фото хостинг
        :param client_id: Foreign key to Client. Its null when image is client.avatar
    """

    __tablename__ = 'images'

    id: Mapped[int] = Column(Integer, primary_key=True)

    path: Mapped[str] = Column(String(255), nullable=True)

    url: Mapped[str] = Column(String(255), nullable=True)
    hosting_data: Mapped[dict] = Column(JSON, nullable=True)

    client_id: Mapped[int] = Column(ForeignKey('clients.id'), nullable=True)
    client: Mapped['Client'] = relationship('Client', back_populates='images', foreign_keys=[client_id])
