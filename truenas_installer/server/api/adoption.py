import errno
import secrets
import typing

from aiohttp_rpc import errors, protocol

from truenas_installer.server.error import Error
from truenas_installer.server.method import method

__all__ = ["is_adopted", "adopt", "authenticate"]

access_key = None


@method(None, {"type": "boolean"})
async def is_adopted(context):
    """
    Returns `true` if the system in question is “adopted”, false otherwise.

    The system is “adopted” when the adopt method is called. Subsequent connections to the system must call the
    `authenticate` method before trying to do anything else.
    """

    return access_key is not None


@method(None, {"type": "string"})
async def adopt(context):
    """
    “Adopt” the system. It will return an access key that must be used to authenticate on this system when
    re-connecting.
    """

    global access_key

    if access_key is not None:
        raise Error("System is already adopted")

    access_key = secrets.token_urlsafe(32)

    setattr(context.rpc_request.context["http_request"], "_authenticated", True)

    return access_key


@method({"type": "string"}, None)
async def authenticate(context, key):
    """
    Authenticate the connection on the “adopted” system.
    """

    global access_key

    if access_key is None:
        raise Error("The system is not adopted")

    if key != access_key:
        raise Error("Invalid access key", errno.EINVAL)

    setattr(context.rpc_request.context["http_request"], "_authenticated", True)


async def adoption_middleware(request: protocol.JsonRpcRequest, handler: typing.Callable) -> protocol.JsonRpcResponse:
    if access_key is not None:
        if not (
            request.method_name in ["is_adopted", "authenticate"] or
            getattr(request.context["http_request"], "_authenticated", False)
        ):
            return protocol.JsonRpcResponse(
                id=request.id,
                jsonrpc=request.jsonrpc,
                error=errors.InvalidParams("You must authenticate before making this call",
                                           data={"errno": errno.EACCES}),
            )

    return await handler(request)
