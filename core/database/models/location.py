from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import Mapped

from . import Base


class Location(Base):
    """
        Таблица адресов точек.
    """

    __tablename__ = 'locations'

    id: Mapped[int] = Column(Integer, primary_key=True)

    address: Mapped[str] = Column(String(255))
