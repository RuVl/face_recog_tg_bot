from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from . import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Client


class Service(Base):
    """
        Таблица сервисов в которых используется клиент.
    """

    __tablename__ = 'services'

    id: Mapped[int] = Column(Integer, primary_key=True)

    title: Mapped[str] = Column(String(255))
    date: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    client_id: Mapped[int] = Column(Integer, ForeignKey('clients.id'))
    client: Mapped['Client'] = relationship('Client', back_populates='services')
