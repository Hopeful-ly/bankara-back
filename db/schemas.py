from typing import List, Optional
from pydantic import BaseModel

from utils import blur_text


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

    def dict(self, *args, **kwargs):
        self_dict = super().dict(*args, **kwargs)
        self_dict["card_number"] = blur_text(str(self_dict["card_number"]), 4, 4)
        return self_dict

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
