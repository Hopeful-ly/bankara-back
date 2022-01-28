from functools import wraps
from hashlib import sha256
from typing import Literal, Optional, Union
from sqlalchemy.orm import Session

from . import models, schemas, with_db


def in_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with with_db() as db:
            res = func(*args, **kwargs, db=db)
            return res

    return wrapper


def card_model_to_schema(card: models.Card) -> schemas.User:
    if card:
        return schemas.Card(
            title=card.title,
            provider=card.provider,
            balance=card.balance,
            id=card.id,
            owner_id=card.owner_id,
            card_number=card.card_number,
            name=card.name,
        )
    else:
        return False


def user_model_to_schema(user: models.User) -> schemas.User:
    if user:
        return schemas.User(
            name=user.name,
            email=user.email,
            id=user.id,
            cards=[card_model_to_schema(card) for card in user.cards],
            hashed_password=user.hashed_password,
        )
    else:
        False


@in_session
def delete_user(user_id: int, db: Optional[Session]) -> bool:
    deleted_count = db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()
    if deleted_count:
        return True
    else:
        return False


@in_session
def get_user(user_id: int, db: Optional[Session]) -> schemas.User:
    return user_model_to_schema(
        db.query(models.User).filter(models.User.id == user_id).first()
    )


@in_session
def get_user_by_email(user_email: int, db: Optional[Session]) -> schemas.User:
    return user_model_to_schema(
        db.query(models.User).filter(models.User.email == user_email).first()
    )


@in_session
def create_user(user: schemas.UserCreate, db: Optional[Session]) -> schemas.User:
    hashed_password = sha256(user.password.encode()).hexdigest()
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print("new user:", db_user.name)
    return user_model_to_schema(db_user)


@in_session
def set_card_balance(
    new_balance: int, card_id: int, db: Optional[Session]
) -> schemas.Card:
    db_card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if db_card:
        db_card.balance = new_balance
        db.commit()
        db.refresh(db_card)
        return card_model_to_schema(db_card)
    else:
        False


@in_session
def get_card(card_id: int, db: Optional[Session]):
    return card_model_to_schema(
        db.query(models.Card).filter(models.Card.id == card_id).first()
    )


@in_session
def create_user_card(
    card: schemas.CardCreate, user_id: int, db: Optional[Session]
) -> schemas.Card:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_card = models.Card(**card.dict(), owner_id=user_id)
        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        return card_model_to_schema(db_card)
    else:
        False
