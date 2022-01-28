from typing import List, Optional
from pydantic import BaseModel


class CardBase(BaseModel):
    title: str
    provider: str
    card_number: int
    balance: int
    name: str


class CardCreate(CardBase):
    pass


class Card(CardBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    cards: List[Card] = []
    hashed_password: str

    class Config:
        orm_mode = True
