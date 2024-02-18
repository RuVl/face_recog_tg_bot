import numpy as np
from sqlalchemy import Integer, Column, ForeignKey, JSON
from sqlalchemy.orm import Mapped, relationship

from . import Base, Visit, Image


class Client(Base):
    """
        Таблица уникальных клиентов (уникальность - разные лица).
        :param profile_picture: One-to-one relationship to Image for profile picture.
        :param face_encoding: 128-мерный массив numpy в байтовом представлении, кодирующий лицо клиента.
        :param visits: List of visits of this client.
    """

    __tablename__ = 'clients'

    id: Mapped[int] = Column(Integer, primary_key=True)

    profile_picture_id: Mapped[int] = Column(ForeignKey('images.id'), nullable=False)
    profile_picture: Mapped['Image'] = relationship('Image')

    face_encoding: Mapped[np.ndarray] = Column(JSON, nullable=False)

    visits: Mapped[list['Visit']] = relationship('Visit', back_populates='client')
