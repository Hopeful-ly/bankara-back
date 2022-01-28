from datetime import datetime
from enum import Enum
from functools import wraps
import secrets
from types import FunctionType
from typing import Dict, Optional, Any
from async_timeout import asyncio
from quart import current_app, jsonify, Quart, request
from quart.wrappers import Response
import time


def now_epoch():
    return int(time.time())


def validated_session(
    restricted=True,
    fail_response=lambda: jsonify({"status": False, "error": "Unauthorized"}),
):
    def decorator(func: FunctionType):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            session = current_app.session()
            validation = await session.validate()
            if not validation:
                if (not restricted) and (
                    len([0, *args, *kwargs.keys()]) == func.__code__.co_argcount
                ):
                    return await func(validation, *args, **kwargs)
                else:
                    return fail_response()
            return await func(validation, *args, **kwargs)

        return wrapper

    return decorator


class Session:
    def __init__(self, session_id) -> None:
        self._session_id = session_id
        self.user_id = None
        self.last_use = now_epoch()

    def delete(self) -> None:
        current_app.storage.remove(self._session_id)
        return self


class SessionStorage:
    def __init__(self, app: Quart) -> None:
        app.storage = self
        self._sessions: Dict[str, Session] = {}
        self.end = asyncio.Event()
        self.end_task = None

        @app.before_request
        async def session_injector():
            session = self.session()
            request.headers.set("x-session-id", session._session_id)
            session.last_use = now_epoch()

        @app.after_request
        async def session_updater(res: Response):
            if request.method != "OPTIONS":
                res.headers.set("x-session-id", self.session()._session_id)
            return res

        @app.before_serving
        async def init_deleter():
            self.end_task = asyncio.get_event_loop().create_task(self.session_deleter())

        @app.after_serving
        async def stop_deleter():
            self.end.set()
            if self.end_task:
                await self.end_task

    async def session_deleter(self):
        while not self.end.is_set():
            await asyncio.sleep(60 * 5)

            deleted_count = 0
            for session_id, session in self._sessions.items():
                if (now_epoch() - session.last_use) > 60 * 5:
                    self.remove(session_id)
                    deleted_count += 1
            print("Deleted", deleted_count, "sessions!")

    def create(self) -> str:
        session_id = secrets.token_hex(64)
        request.headers.set("x-session-id", session_id)
        self._sessions[session_id] = Session(session_id)
        return session_id

    def remove(self, session_id: Session) -> Optional[Session]:
        poped = self._sessions.pop(session_id, None)
        return poped

    def session(self, session_id: Optional[str] = None) -> Session:
        session_id = session_id or request.headers.get("x-session-id", False)
        if not type(session_id) == str:
            session_id = self.create()
            return self.session(session_id)
        session = self._sessions.get(session_id, None)
        if not session:
            request.headers.pop("x-session-id", None)
            session_id = self.create()
            return self.session(session_id)
        return session
