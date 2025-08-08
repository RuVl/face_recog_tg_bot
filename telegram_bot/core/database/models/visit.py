from datetime import datetime
from typing import TYPE_CHECKING

from phonenumbers import PhoneNumber
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy_utils import PhoneNumberType

from core.config import PHONE_NUMBER_REGION
from . import Base

if TYPE_CHECKING:
	pass


class Visit(Base):
	"""
		Таблица обращений (прихода на точку).
	"""

	__tablename__ = 'visits'

	id: Mapped[int] = Column(Integer, primary_key=True)
	date: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

	name: Mapped[str] = Column(String(255), nullable=True)
	social_media: Mapped[str] = Column(String(255), nullable=True)
	phone_number: Mapped[PhoneNumber] = Column(PhoneNumberType(region=PHONE_NUMBER_REGION), nullable=True, index=True)

	images: Mapped[list['Image']] = relationship('Image', back_populates='visit', passive_deletes=True)
	videos: Mapped[list['Video']] = relationship('Video', back_populates='visit', passive_deletes=True)

	services: Mapped[list['Service']] = relationship('Service', back_populates='visit', passive_deletes=True)

	location_id: Mapped[int] = Column(ForeignKey('locations.id'), nullable=False)
	location: Mapped['Location'] = relationship('Location')

	client_id: Mapped[int] = Column(ForeignKey('clients.id', ondelete='SET NULL'), nullable=False)
	client: Mapped['Client'] = relationship('Client', back_populates='visits', passive_deletes=True)
