from contextlib import contextmanager
from quart import Quart
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models


def make_db():
    models.Base.metadata.create_all(bind=engine)


@contextmanager
def with_db():
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as ex:
        print("an error occured", ex)
    finally:
        db.close()
