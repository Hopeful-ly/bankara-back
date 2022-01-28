from sqlalchemy import String, ForeignKey, Column, Integer
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    cards = relationship("Card", back_populates="owner")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    provider = Column(String, index=True)
    name = Column(String, index=True)
    card_number = Column(Integer, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Integer, index=True)

    owner = relationship("User", back_populates="cards")
