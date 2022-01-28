from typing import Any, List
from quart import Quart, Blueprint, jsonify
from pydantic import BaseModel


def is_type(any: Any, _type: Any):
    return any.__class__ == _type


def expect_type(any: Any, _type: type):
    if not is_type(any, _type):
        raise Exception(f"Expected {_type}, got {any.__class__}")


def validate_req(pydantic_obj: BaseModel):
    try:
        pydantic_obj.validate(pydantic_obj)
        return False
    except Exception as ex:
        return json(False, msg=f"{ex}")


def json(*args, **kwargs):
    if args:
        kwargs["status"] = args[0]
    return jsonify(kwargs)


def register(app: Quart, blueprints: List[Blueprint]):
    expect_type(app, Quart)
    expect_type(blueprints, list)

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        name = blueprint.name.capitalize()
        print(f"{name} registered.")
    return app
