from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from . import Base, Location

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Client


class Visit(Base):
    """
        Таблица обращений (прихода на точку).
    """

    __tablename__ = 'visits'

    id: Mapped[int] = Column(Integer, primary_key=True)

    name: Mapped[str] = Column(String(255))
    date: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    contacts: Mapped[str] = Column(String(255))

    client_id: Mapped[int] = Column(Integer, ForeignKey('clients.id'))
    client: Mapped['Client'] = relationship('Client', back_populates='visits')

    location_id: Mapped[int] = Column(ForeignKey('locations.id'))
    location: Mapped['Location'] = relationship('Location')
