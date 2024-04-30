# -*- coding=utf-8 -*-
from dataclasses import dataclass
import errno
import logging

from truenas_installer.server.error import Error

from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

__all__ = ["methods", "method"]

methods = {}


@dataclass
class Context:
    server: object
    rpc_request: object


class Method:
    def __init__(self, name, schema, result_schema, fn):
        self.name = name
        self.schema = schema
        self.result_schema = result_schema
        self.fn = fn
        self.server = None

    async def call(self, rpc_request, *args):
        args = (Context(self.server, rpc_request),)

        if self.schema is not None:
            if len(rpc_request.args) != 1:
                raise Error(f"1 parameter required, found {len(rpc_request.args)}", errno.EINVAL)

            param = rpc_request.args[0]
            try:
                validate(param, self.schema)
            except ValidationError as e:
                raise Error(str(e), errno.EINVAL)

            args += (param,)
        else:
            if len(rpc_request.args) != 0:
                raise Error(f"0 parameters required, found {len(rpc_request.args)}", errno.EINVAL)

        return await self.fn(*args)


def method(schema, result_schema):
    def wrapper(fn):
        name = fn.__name__

        if name in methods:
            raise RuntimeError(f"Method {name!r} is already registered")

        methods[name] = Method(name, schema, result_schema, fn)
        return fn

    return wrapper
