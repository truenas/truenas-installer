import errno
import logging
import typing

from aiohttp_rpc import errors, protocol

logger = logging.getLogger(__name__)

__all__ = ["Error", "exception_middleware"]


class Error(Exception):
    def __init__(self, text, code=errno.EFAULT):
        self.text = text
        self.code = code
        super().__init__(self.text, self.code)


async def exception_middleware(request: protocol.JsonRpcRequest, handler: typing.Callable) -> protocol.JsonRpcResponse:
    try:
        response = await handler(request)
    except Error as e:
        response = protocol.JsonRpcResponse(
            id=request.id,
            jsonrpc=request.jsonrpc,
            error=errors.InvalidParams(e.text, data={"errno": errno.errorcode.get(e.code)}),
        )
    except Exception:
        logger.error("Unhandled exception", exc_info=True)
        response = protocol.JsonRpcResponse(
            id=request.id,
            jsonrpc=request.jsonrpc,
            error=errors.InternalError(),
        )

    return response
