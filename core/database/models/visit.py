from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from . import Base, Location, Image, Service

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Client


class Visit(Base):
    """
        Таблица обращений (прихода на точку).
    """

    __tablename__ = 'visits'

    id: Mapped[int] = Column(Integer, primary_key=True)
    date: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    name: Mapped[str] = Column(String(255), nullable=True)
    contacts: Mapped[str] = Column(String(255), nullable=True)

    images: Mapped[list['Image']] = relationship('Image', back_populates='visit')
    services: Mapped[list['Service']] = relationship('Service', back_populates='visit')

    location_id: Mapped[int] = Column(ForeignKey('locations.id'))
    location: Mapped['Location'] = relationship('Location')

    client_id: Mapped[int] = Column(ForeignKey('clients.id'))
    client: Mapped['Client'] = relationship('Client', back_populates='visits')
