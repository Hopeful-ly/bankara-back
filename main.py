import asyncio
from functools import wraps
from hashlib import sha256
import signal
from typing import Any
from black import traceback
from quart import Quart, current_app, request
from quart_auth import LocalProxy, Unauthorized
from db import crud, schemas, make_db
from utils import json, register, validate_req
from settings import SECRET_KEY
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart_cors import cors
from quart.utils import run_sync
from session import Session, SessionStorage

session: Session = LocalProxy(lambda: current_app.session())


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if session.user_id:
            return await func(*args, **kwargs)
        raise Unauthorized()

    return wrapper


app = Quart(__name__)
# app.config["SESSION_TYPE"] = "redis"
app.secret_key = SECRET_KEY

shutdown_event = asyncio.Event()
app = cors(app, allow_origin="*", expose_headers=["x-session-id"])
register(app, [])
storage = SessionStorage(app)
app.session = storage.session

make_db()

config = Config()
config.use_reloader = True
config.bind = ["localhost:4000"]


@app.route("/check", methods=["GET"])
async def check_user():
    print("user id!", session.user_id, session.last_use, session._session_id[:5])
    user_id = session.user_id
    assert user_id, "user is not logged in"
    user: schemas.User = crud.get_user(user_id)
    assert user, "user not found"
    return json(
        True,
        user=dict(
            id=user.id,
            name=user.name,
            email=user.email,
            cards=[card.dict() for card in user.cards],
        ),
    )


@app.route("/users", methods=["POST"])
async def create_user():

    if session.user_id:
        session.user_id = None

    user = schemas.UserCreate(**(await request.get_json()))
    error = validate_req(user)
    if error:
        raise AssertionError("error")
    already_user = crud.get_user_by_email(user.email)
    assert not already_user, "used-email"

    new_user: schemas.User = crud.create_user(user)
    assert new_user, "error"
    session.user_id = new_user.id
    print("logged user in: ", session.user_id)
    return json(
        True,
        user=dict(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            cards=[card.dict() for card in new_user.cards],
        ),
    )


@app.route("/users/<int:user_id>", methods=["DELETE"])
@login_required
async def del_user(user_id: int):
    assert session.user_id == user_id, "unauthorized"
    assert crud.delete_user(user_id), "user not found"
    return json(True)


@app.route("/users/<int:user_id>", methods=["GET"])
async def get_user(user_id: int):
    print(session.user_id, user_id)
    assert session.user_id == user_id, "unauthorized"
    user = crud.get_user(user_id)
    assert user, "user not found"
    return json(
        True,
        user=dict(
            name=user.name,
            email=user.email,
            id=user.id,
            cards=[card.dict() for card in user.cards],
        ),
    )


@app.route("/login", methods=["POST"])
async def user_login():
    credentials = schemas.UserCreate(**((await request.get_json()) or {}), name="")
    user: schemas.User = crud.get_user_by_email(credentials.email)
    assert user, "user not found"

    success_response = json(
        True,
        user=dict(
            id=user.id,
            name=user.name,
            email=user.email,
            cards=[card.dict() for card in user.cards],
        ),
    )
    if session.user_id:
        return success_response
    hashed_password = sha256(credentials.password.encode()).hexdigest()
    print(user.hashed_password)
    print(hashed_password)
    assert user.hashed_password == hashed_password, "incorrect email or password"
    session.user_id = user.id
    print("logged user in: ", session.user_id)
    return success_response


@app.route("/users/<int:user_id>/cards/<int:card_id>", ["GET"])
@login_required
async def get_user_card(user_id: int, card_id: int):
    assert session.user_id == user_id, "unauthorized"
    card: schemas.Card = crud.get_card(card_id)
    assert card.owner_id == user_id, "the specified card was not found"
    return json(True, card=card.dict())


@app.route("/users/<int:user_id>/cards", methods=["POST"])
@login_required
async def user_create_card(user_id: int):
    assert session.user_id == user_id, "unauthorized"
    card = schemas.CardCreate(**((await request.get_json()) or {}))
    error = validate_req(card)
    if error:
        return error
    card: schemas.Card = crud.create_user_card(card, user_id)
    return json(True, card=card.dict())


@app.route("/users/<int:user_id>/cards", methods=["GET"])
@login_required
async def get_user_cards(user_id: int):
    assert session.user_id == user_id, "unauthorized"
    user = crud.get_user(user_id)
    assert user, "user not found"
    cards = [
        dict(
            title=card.title,
            provider=card.provider,
            balance=card.balance,
            id=card.id,
        )
        for card in user.cards
    ]
    return json(True, cards=cards)


@app.errorhandler(AssertionError)
def assertion_handler(ex):
    print("assertion error")
    return json(False, msg=str(ex))


@app.errorhandler(Unauthorized)
def unauthorized_handler(ex):
    print("unauthorized endpoint was accessed")
    return json(False, msg="unauthorized session")


@app.errorhandler(Exception)
def error_handler(ex):
    print(ex)
    traceback.print_exc()
    print("an unexpected error has occurred")
    return json(False, msg="error")


@app.errorhandler(404)
def not_found_handler(ex):
    print("undefined endpoint was accessed")
    return json(False, msg="endpoint not found")


def _signal_handler(*_: Any):
    shutdown_event.set()


loop = asyncio.new_event_loop()
loop.add_signal_handler(signal.SIGTERM, _signal_handler)

try:
    loop.run_until_complete(serve(app, config, shutdown_trigger=shutdown_event.wait))
except:
    print("Gracefully shutting down...")
