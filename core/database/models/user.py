from typing import Optional

from sqlalchemy import Column, Integer, BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, relationship

from . import Base, Location


class User(Base):
    """
        Таблица пользователей бота (модераторы и админы)
    """

    __tablename__ = 'users'

    id: Mapped[int] = Column(Integer, primary_key=True)

    telegram_id: Mapped[int] = Column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = Column(String(255), nullable=True)

    is_moderator: Mapped[bool] = Column(Boolean, default=False)
    is_admin: Mapped[bool] = Column(Boolean, default=False)

    location_id: Mapped[int] = Column(ForeignKey('locations.id'))
    location: Mapped['Location'] = relationship('Location')
