from sqlalchemy import Integer, Column, Text, PickleType
from sqlalchemy.orm import Mapped, relationship

import numpy as np

from . import Base, Visit, Service


class Client(Base):
    """
        Таблица уникальных клиентов (уникальность - разные лица).
        :param images: Ссылки на картинки лица одного и того же клиента, разделённые '\n'
        :param face_encoding: 128-мерный массив numpy в байтовом представлении, кодирующий лицо клиента
    """

    __tablename__ = 'clients'

    id: Mapped[int] = Column(Integer, primary_key=True)

    images: Mapped[str] = Column(Text)
    face_encoding: Mapped[np.ndarray] = Column(PickleType)

    visits: Mapped[list['Visit']] = relationship('Visit', back_populates='client')

    services: Mapped[list['Service']] = relationship('Service', back_populates='client')
